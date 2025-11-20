from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Trip
from .serializers import TripSerializer, TripActionSerializer, DriverLocationSerializer


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

    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return Trip.objects.filter(customer=user).order_by('-created_at')
        if user.role == 'rider':
            return Trip.objects.filter(rider=user).order_by('-created_at')
        return Trip.objects.none()


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
