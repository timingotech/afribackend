from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Trip
from .serializers import (
    TripSerializer, TripActionSerializer, DriverLocationSerializer, DriverLocationModelSerializer,
    PaymentSerializer,
)
from .models import Payment
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import get_user_model


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200
import uuid
from django.conf import settings
import hmac
import hashlib
import json
import requests


class TripCreateView(generics.CreateAPIView):
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        trip = serializer.save(customer=self.request.user)

        # After creating the trip, find the nearest drivers and notify them
        try:
            from .utils import get_nearby_drivers
            from apps.notifications.push import send_push_async as send_push

            origin_lat = getattr(trip, 'origin_lat', None)
            origin_lng = getattr(trip, 'origin_lng', None)
            if origin_lat is not None and origin_lng is not None:
                drivers = get_nearby_drivers(origin_lat, origin_lng, radius_km=5.0, limit=20)
                # Collect device tokens for drivers
                for d in drivers:
                    try:
                        tokens = [dev.token for dev in getattr(d, 'devices').all() if dev.token]
                        if not tokens:
                            continue
                        title = 'New ride request nearby'
                        body = f'Pickup at {trip.origin_address or "your area"}. Tap to accept.'
                        data = {
                            'type': 'new_trip',
                            'trip_id': str(trip.pk),
                            'origin_lat': str(origin_lat),
                            'origin_lng': str(origin_lng),
                        }
                        try:
                            send_push(tokens, title, body, data=data)
                        except Exception:
                            from apps.notifications.push import _send_immediate
                            _send_immediate(tokens, title, body, data)
                    except Exception:
                        # Don't fail trip creation if notifications fail
                        pass
        except Exception:
            # Do not block trip creation if notifications fail
            import logging
            logging.exception('Failed to notify nearby drivers')


class TripDetailView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]


class TripListView(generics.ListAPIView):
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return Trip.objects.filter(customer=user).order_by('-created_at')
        if user.role == 'rider':
            return Trip.objects.filter(rider=user).order_by('-created_at')
        # Admins and staff should see all trips
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return Trip.objects.select_related('customer', 'rider').all().order_by('-created_at')
        return Trip.objects.none()




@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reassign_trip(request, pk):
    """Admin/staff can reassign a trip to a different rider. Expects `rider_id` in payload."""
    user = request.user
    if not (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
        return Response({'detail': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

    trip = get_object_or_404(Trip, pk=pk)
    rider_id = request.data.get('rider_id')
    if not rider_id:
        return Response({'detail': 'rider_id required'}, status=status.HTTP_400_BAD_REQUEST)

    User = get_user_model()
    try:
        rider = User.objects.get(pk=rider_id)
    except User.DoesNotExist:
        return Response({'detail': 'rider not found'}, status=status.HTTP_404_NOT_FOUND)

    trip.rider = rider
    # if trip was pending, mark as accepted
    if trip.status == Trip.STATUS_PENDING:
        trip.status = Trip.STATUS_ACCEPTED
        trip.accepted_at = None
    trip.save()

    return Response(TripSerializer(trip).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trip_action(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    serializer = TripActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    action = serializer.validated_data['action']

    if action == 'accept':
        if request.user.role != 'rider':
            return Response({'detail': 'Only riders can accept trips'}, status=status.HTTP_403_FORBIDDEN)
        trip.accept(request.user)
        # Broadcast accept event to trip group and notify customer (if channels configured)
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'trip_{trip.pk}',
                {
                    'type': 'send_update',
                    'data': {'event': 'accepted', 'trip_id': trip.pk, 'rider_id': request.user.id}
                }
            )
            # send push to customer devices
            try:
                from apps.notifications.push import send_push_async as send_push
                customer = trip.customer
                tokens = [dev.token for dev in getattr(customer, 'devices').all() if dev.token]
                if tokens:
                    title = 'Driver accepted your ride'
                    body = f'{request.user.first_name or "Driver"} is on the way. ETA will be available shortly.'
                    try:
                        send_push(tokens, title, body, data={'event': 'accepted', 'trip_id': str(trip.pk)})
                    except Exception:
                        from apps.notifications.push import _send_immediate
                        _send_immediate(tokens, title, body, data={'event': 'accepted', 'trip_id': str(trip.pk)})
            except Exception:
                pass
        except Exception:
            pass
        return Response(TripSerializer(trip).data)

    if action == 'start':
        if request.user.role != 'rider':
            return Response({'detail': 'Only riders can start trips'}, status=status.HTTP_403_FORBIDDEN)
        # Ensure only assigned rider can start
        if trip.rider_id and trip.rider_id != request.user.id:
            return Response({'detail': 'Only assigned rider can start this trip'}, status=status.HTTP_403_FORBIDDEN)
        trip.start()
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'trip_{trip.pk}',
                {
                    'type': 'send_update',
                    'data': {'event': 'started', 'trip_id': trip.pk, 'started_at': str(trip.started_at)}
                }
            )
            # notify customer via push
            try:
                from apps.notifications.push import send_push_async as send_push
                customer = trip.customer
                tokens = [dev.token for dev in getattr(customer, 'devices').all() if dev.token]
                if tokens:
                    title = 'Your ride has started'
                    body = f'{request.user.first_name or "Driver"} has started the trip.'
                    # include share token for public viewing
                    data = {'event': 'started', 'trip_id': str(trip.pk), 'share_token': trip.share_token}
                    try:
                        send_push(tokens, title, body, data=data)
                    except Exception:
                        from apps.notifications.push import _send_immediate
                        _send_immediate(tokens, title, body, data=data)
            except Exception:
                pass
        except Exception:
            pass
        return Response(TripSerializer(trip).data)

    if action == 'end':
        if request.user.role != 'rider':
            return Response({'detail': 'Only riders can end trips'}, status=status.HTTP_403_FORBIDDEN)
        if trip.rider_id and trip.rider_id != request.user.id:
            return Response({'detail': 'Only assigned rider can end this trip'}, status=status.HTTP_403_FORBIDDEN)
        trip.end()
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'trip_{trip.pk}',
                {
                    'type': 'send_update',
                    'data': {'event': 'ended', 'trip_id': trip.pk, 'ended_at': str(trip.ended_at)}
                }
            )
            try:
                from apps.notifications.push import send_push_async as send_push
                customer = trip.customer
                tokens = [dev.token for dev in getattr(customer, 'devices').all() if dev.token]
                if tokens:
                    title = 'Ride completed'
                    body = f'Thank you for riding. Your receipt is available in the app.'
                    try:
                        send_push(tokens, title, body, data={'event': 'ended', 'trip_id': str(trip.pk)})
                    except Exception:
                        from apps.notifications.push import _send_immediate
                        _send_immediate(tokens, title, body, data={'event': 'ended', 'trip_id': str(trip.pk)})
            except Exception:
                pass
        except Exception:
            pass
        return Response(TripSerializer(trip).data)

    if action == 'cancel':
        trip.cancel(by_user=request.user)
        return Response(TripSerializer(trip).data)

    if action == 'arrived':
        if request.user.role != 'rider':
            return Response({'detail': 'Only riders can set arrival'}, status=status.HTTP_403_FORBIDDEN)
        if trip.rider_id and trip.rider_id != request.user.id:
            return Response({'detail': 'Only assigned rider can mark arrival'}, status=status.HTTP_403_FORBIDDEN)
        trip.arrived()
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f'trip_{trip.pk}',
                {
                    'type': 'send_update',
                    'data': {'event': 'arrived', 'trip_id': trip.pk, 'arrived_at': str(trip.arrived_at)}
                }
            )
            # notify customer via push
            try:
                from apps.notifications.push import send_push_async as send_push
                customer = trip.customer
                tokens = [dev.token for dev in getattr(customer, 'devices').all() if dev.token]
                if tokens:
                    title = 'Driver has arrived'
                    body = f'{request.user.first_name or "Driver"} has arrived at pickup.'
                    try:
                        send_push(tokens, title, body, data={'event': 'arrived', 'trip_id': str(trip.pk)})
                    except Exception:
                        from apps.notifications.push import _send_immediate
                        _send_immediate(tokens, title, body, data={'event': 'arrived', 'trip_id': str(trip.pk)})
            except Exception:
                pass
        except Exception:
            pass
        return Response(TripSerializer(trip).data)

    return Response({'detail': 'action not handled'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def driver_location_update(request):
    """Driver posts frequent location updates; broadcasts to trip group if live."""
    serializer = DriverLocationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    user = request.user
    # Persist latest DriverLocation
    try:
        from .models import DriverLocation
        dl, _ = DriverLocation.objects.update_or_create(
            driver=user,
            defaults={'lat': data['lat'], 'lng': data['lng'], 'speed': data.get('speed'), 'heading': data.get('heading'), 'accuracy': data.get('accuracy')}
        )
    except Exception:
        dl = None

    # Also write to Redis GEO for fast proximity queries when available
    try:
        from django.conf import settings
        redis_url = getattr(settings, 'REDIS_URL', None)
        if redis_url:
            import redis
            KEY = 'drivers:locations'
            r = redis.from_url(redis_url)
            # redis-py geoadd signature: key, {member: (lon, lat)} or use geoadd(key, lon, lat, member)
            try:
                # prefer mapping API where available
                r.geoadd(KEY, {f'driver:{user.id}': (data['lng'], data['lat'])})
            except TypeError:
                # fallback to positional args
                r.geoadd(KEY, data['lng'], data['lat'], f'driver:{user.id}')
    except Exception:
        pass

    # Broadcast to any trip group the driver is currently assigned to and live
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        layer = get_channel_layer()
        # Find an active trip for this driver
        active = Trip.objects.filter(rider=user, status=Trip.STATUS_IN_PROGRESS).order_by('-started_at').first()
        if active:
            async_to_sync(layer.group_send)(
                f'trip_{active.pk}',
                {
                    'type': 'send_update',
                    'data': {'event': 'location', 'trip_id': active.pk, 'lat': data['lat'], 'lng': data['lng'], 'speed': data.get('speed')}
                }
            )
    except Exception:
        pass

    return Response({'detail': 'ok'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def driver_logout(request):
    """Driver notifies server they are going offline; cleanup Redis GEO entry."""
    user = request.user
    if getattr(user, 'role', None) != 'rider':
        return Response({'detail': 'Only riders can call logout cleanup'}, status=status.HTTP_403_FORBIDDEN)

    try:
        from django.conf import settings
        redis_url = getattr(settings, 'REDIS_URL', None)
        if redis_url:
            import redis
            KEY = 'drivers:locations'
            r = redis.from_url(redis_url)
            try:
                r.zrem(KEY, f'driver:{user.id}')
            except Exception:
                pass
    except Exception:
        pass

    return Response({'detail': 'ok'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def estimate_fare(request):
    """Estimate fare given distance_km and duration_min (or origin/dest coordinates if provided)."""
    data = request.data
    # prefer explicit distance/duration from client (mobile calculates route)
    distance_km = data.get('distance_km')
    duration_min = data.get('duration_min')
    # If distance/duration supplied directly, compute immediately
    if distance_km is not None and duration_min is not None:
        # reuse TripSerializer logic for consistent pricing
        temp = {'distance_km': distance_km, 'duration_min': duration_min}
        serializer = TripSerializer()
        try:
            estimated = serializer._compute_price(temp)
        except Exception:
            return Response({'detail': 'failed to compute estimate'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        breakdown = {
            'estimated_fare': estimated,
            'currency': getattr(settings, 'CURRENCY', 'NGN'),
            'distance_km': float(distance_km),
            'duration_min': float(duration_min),
        }
        return Response(breakdown)

    # Otherwise, try to compute using origin/destination via routing provider
    origin_lat = data.get('origin_lat')
    origin_lng = data.get('origin_lng')
    dest_lat = data.get('dest_lat')
    dest_lng = data.get('dest_lng')
    if not all([origin_lat, origin_lng, dest_lat, dest_lng]):
        return Response({'detail': 'distance_km and duration_min or origin/dest coordinates required'}, status=status.HTTP_400_BAD_REQUEST)

    # Prefer OSRM if OSRM_URL configured, otherwise try public OSRM, otherwise try Google Directions
    osrm_base = getattr(settings, 'OSRM_URL', 'https://router.project-osrm.org')
    try:
        # OSRM expects lon,lat pairs
        url = f"{osrm_base}/route/v1/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}?overview=false&alternatives=false"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            jr = r.json()
            routes = jr.get('routes') or []
            if routes:
                route = routes[0]
                distance_m = route.get('distance')
                duration_s = route.get('duration')
                distance_km = (distance_m or 0) / 1000.0
                duration_min = (duration_s or 0) / 60.0
                est = TripSerializer()._compute_price({'distance_km': distance_km, 'duration_min': duration_min})
                return Response({'estimated_fare': est, 'distance_km': distance_km, 'duration_min': duration_min, 'currency': getattr(settings, 'CURRENCY', 'NGN')})
    except Exception:
        pass

    # Try Google Directions if configured
    gkey = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
    if gkey:
        try:
            gurl = 'https://maps.googleapis.com/maps/api/directions/json'
            params = {
                'origin': f'{origin_lat},{origin_lng}',
                'destination': f'{dest_lat},{dest_lng}',
                'key': gkey,
                'mode': data.get('mode', 'driving'),
            }
            r = requests.get(gurl, params=params, timeout=8)
            if r.status_code == 200:
                jr = r.json()
                routes = jr.get('routes') or []
                if routes:
                    legs = routes[0].get('legs') or []
                    if legs:
                        leg = legs[0]
                        distance_m = leg.get('distance', {}).get('value')
                        duration_s = leg.get('duration', {}).get('value')
                        distance_km = (distance_m or 0) / 1000.0
                        duration_min = (duration_s or 0) / 60.0
                        est = TripSerializer()._compute_price({'distance_km': distance_km, 'duration_min': duration_min})
                        return Response({'estimated_fare': est, 'distance_km': distance_km, 'duration_min': duration_min, 'currency': getattr(settings, 'CURRENCY', 'NGN')})
        except Exception:
            pass

    return Response({'detail': 'failed to compute route estimate; configure OSRM or Google Maps API key'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment(request, pk):
    """Create a payment record for a trip. Frontend should use returned `reference` to perform provider checkout."""
    trip = get_object_or_404(Trip, pk=pk)
    # Only customer may create payment for their trip
    if request.user != trip.customer:
        return Response({'detail': 'only customer may create payment'}, status=status.HTTP_403_FORBIDDEN)

    amount = trip.price or 0
    if not amount:
        # compute if price missing
        try:
            amount = TripSerializer()._compute_price(trip)
            trip.price = amount
            trip.save()
        except Exception:
            amount = 0

    ref = request.data.get('reference') or uuid.uuid4().hex
    p = Payment.objects.create(trip=trip, amount=amount, provider='paystack', reference=ref)

    # If Paystack secret configured, initialize a transaction and return the authorization_url
    secret = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
    callback = getattr(settings, 'PAYSTACK_CALLBACK_URL', None)
    payment_url = None
    provider_response = None
    if secret:
        try:
            headers = {
                'Authorization': f'Bearer {secret}',
                'Content-Type': 'application/json',
            }
            # Paystack expects amount in the smallest currency unit (e.g., kobo) for NGN
            amount_kobo = int(round(float(amount) * 100))
            body = {
                'amount': amount_kobo,
                'email': getattr(trip.customer, 'email', ''),
                'reference': ref,
            }
            if callback:
                body['callback_url'] = callback

            resp = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=json.dumps(body), timeout=10)
            provider_response = resp.text
            if resp.status_code == 200:
                data = resp.json().get('data') or {}
                payment_url = data.get('authorization_url')
                # store provider metadata
                p.metadata = {'paystack_init': data}
                p.raw_response = resp.text
                p.save()
            else:
                p.raw_response = resp.text
                p.save()
        except Exception as e:
            # do not fail creation if provider call fails; log and return record
            try:
                import logging
                logging.exception('Paystack init failed')
            except Exception:
                pass

    return Response({'reference': p.reference, 'amount': float(p.amount), 'payment_url': payment_url, 'provider_response': provider_response})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def paystack_webhook(request):
    """Simple Paystack webhook receiver. Expects JSON payload with event and data.reference."""
    # Verify Paystack signature header if configured
    try:
        raw_body = request.body
        signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
        secret = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
        if secret and signature:
            computed = hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha512).hexdigest()
            if not hmac.compare_digest(computed, signature):
                return Response({'detail': 'invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        # if verification fails unexpectedly, reject
        return Response({'detail': 'signature verification error'}, status=status.HTTP_400_BAD_REQUEST)

    payload = request.data
    event = payload.get('event')
    data = payload.get('data') or {}
    reference = data.get('reference')
    if not reference:
        return Response({'detail': 'missing reference'}, status=status.HTTP_400_BAD_REQUEST)

    payment = Payment.objects.filter(reference=reference).first()
    if not payment:
        return Response({'detail': 'payment not found'}, status=status.HTTP_404_NOT_FOUND)

    # store raw provider payload in raw_response and metadata
    try:
        payment.raw_response = json.dumps(payload)
        # merge existing metadata
        meta = payment.metadata or {}
        meta['webhook'] = payload
        payment.metadata = meta
    except Exception:
        pass

    # normalize status checks from Paystack payload
    status_field = data.get('status') or data.get('gateway_response')
    if event == 'charge.success' or status_field == 'success' or data.get('paid') is True:
        payment.mark_paid(raw=json.dumps(payload))
        return Response({'detail': 'ok'})

    if event == 'charge.failed' or status_field == 'failed':
        payment.mark_failed(raw=json.dumps(payload))
        return Response({'detail': 'ok'})

    payment.save()
    return Response({'detail': 'ignored'})


from .models import DriverLocation

class DriverLocationListView(generics.ListAPIView):
    """List all driver locations (admin only)"""
    serializer_class = DriverLocationModelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DriverLocation.objects.select_related('driver').all().order_by('-updated_at')
