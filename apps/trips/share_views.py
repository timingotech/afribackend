from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from .models import Trip, DriverLocation


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def share_trip(request, token):
    try:
        trip = Trip.objects.get(share_token=token)
    except Trip.DoesNotExist:
        return Response({'detail': 'not found'}, status=404)

    data = {
        'trip_id': trip.pk,
        'status': trip.status,
        'origin': {'lat': trip.origin_lat, 'lng': trip.origin_lng, 'address': trip.origin_address},
        'destination': {'lat': trip.dest_lat, 'lng': trip.dest_lng, 'address': trip.dest_address},
        'rider': None,
    }
    if trip.rider:
        data['rider'] = {
            'id': trip.rider.id,
            'name': f"{trip.rider.first_name} {trip.rider.last_name}".strip(),
        }
        # include current driver location if available
        loc = DriverLocation.objects.filter(driver=trip.rider).order_by('-updated_at').first()
        if loc:
            data['rider']['lat'] = loc.lat
            data['rider']['lng'] = loc.lng

    return Response(data)
