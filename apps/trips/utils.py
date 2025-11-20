import math
from django.contrib.auth import get_user_model
from .models import DriverLocation
from django.conf import settings

User = get_user_model()


def haversine_distance_km(lat1, lng1, lat2, lng2):
    # returns distance in kilometers between two lat/lng points
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def get_nearby_drivers(lat, lng, radius_km=5.0, limit=20):
    """Return a list of driver User objects nearest to given lat/lng within radius_km.

    Implementation uses Redis GEO if `REDIS_URL` is configured; otherwise
    falls back to the simple Haversine in-DB scan. For production scale use PostGIS.
    """
    redis_url = getattr(settings, 'REDIS_URL', None)
    if redis_url:
        try:
            import redis
            # key where driver locations are stored
            KEY = 'drivers:locations'
            r = redis.from_url(redis_url)
            # GEOSEARCH is preferred, but use GEORADIUS for compatibility
            # redis-py expects longitude then latitude
            res = r.georadius(KEY, lng, lat, radius_km, unit='km', withdist=True, sort='ASC', count=limit)
            drivers = []
            for item in res:
                # item: (member, dist)
                member = item[0].decode() if isinstance(item[0], bytes) else item[0]
                try:
                    uid = int(member.split(':')[-1])
                    user = User.objects.filter(pk=uid).first()
                    if user:
                        drivers.append(user)
                except Exception:
                    continue
            return drivers
        except Exception:
            # Fall through to DB scan on any redis error
            pass

    # Fallback: compute Haversine distances against persisted DriverLocation rows
    locations = DriverLocation.objects.select_related('driver').all()
    nearby = []
    for loc in locations:
        if loc.lat is None or loc.lng is None:
            continue
        dist = haversine_distance_km(lat, lng, loc.lat, loc.lng)
        if dist <= radius_km:
            nearby.append((dist, loc.driver))

    nearby.sort(key=lambda x: x[0])
    drivers = [d for _, d in nearby[:limit]]
    return drivers
import math
from typing import List, Tuple
from .models import DriverLocation


def haversine_distance(lat1, lng1, lat2, lng2):
    # returns distance in kilometers
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def bounding_box(lat, lng, radius_km):
    # very small approximation for bounding box in degrees
    lat_deg = radius_km / 111.0
    lng_deg = radius_km / (111.320 * math.cos(math.radians(lat)))
    return (lat - lat_deg, lat + lat_deg, lng - lng_deg, lng + lng_deg)


def find_nearby_drivers(lat: float, lng: float, radius_km: float = 5.0, limit: int = 20) -> List[Tuple[DriverLocation, float]]:
    """Return up to `limit` DriverLocation objects closest to (lat, lng) within radius_km.
    Returns list of tuples (DriverLocation, distance_km) ordered by distance.
    """
    min_lat, max_lat, min_lng, max_lng = bounding_box(lat, lng, radius_km)
    qs = DriverLocation.objects.filter(lat__gte=min_lat, lat__lte=max_lat, lng__gte=min_lng, lng__lte=max_lng)
    results = []
    for dl in qs:
        d = haversine_distance(lat, lng, dl.lat, dl.lng)
        if d <= radius_km:
            results.append((dl, d))
    results.sort(key=lambda x: x[1])
    return results[:limit]
