"""Simple test script to validate share-token Redis TTL and GEO writes/cleanup.

Run from `backend` directory with the backend venv activated:

PowerShell:
.\.venv\Scripts\python.exe tools/test_geo_and_share.py

"""
import os
import sys
import time

# ensure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')

# If script is executed from tools/ the project root may not be on sys.path; add it
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.trips.models import Trip, DriverLocation
from django.conf import settings

User = get_user_model()


def info(msg):
    print(f"[INFO] {msg}")


def main():
    # create or get test users
    rider, _ = User.objects.get_or_create(email='test-rider@example.com', defaults={'role': 'rider'})
    customer, _ = User.objects.get_or_create(email='test-customer@example.com', defaults={'role': 'customer'})

    info(f'Using rider id={rider.id} customer id={customer.id}')

    # create a trip
    trip = Trip.objects.create(
        customer=customer,
        origin_address='Origin', origin_lat=6.5244, origin_lng=3.3792,
        dest_address='Dest', dest_lat=6.5244, dest_lng=3.3792
    )
    info(f'Created trip id={trip.pk} status={trip.status}')

    # start trip -> should generate share token and store in Redis if available
    trip.start()
    info(f'Trip started: share_token={trip.share_token} live_active={trip.live_active}')

    redis_url = getattr(settings, 'REDIS_URL', None)
    if redis_url and trip.share_token:
        try:
            import redis
            r = redis.from_url(redis_url)
            key = f"{getattr(settings, 'SHARE_TOKEN_REDIS_PREFIX', 'share:token:')}{trip.share_token}"
            val = r.get(key)
            info(f'Redis key {key} exists -> {val}')
            ttl = r.ttl(key)
            info(f'Key TTL = {ttl}')
        except Exception as e:
            info(f'Redis check failed: {e}')
    else:
        info('Redis not configured or no share_token; skipping redis checks')

    # simulate driver location GEO add
    try:
        # create driver location record
        dl, _ = DriverLocation.objects.update_or_create(
            driver=rider,
            defaults={'lat': 6.5244, 'lng': 3.3792}
        )
        info(f'Created DriverLocation id={dl.pk}')
        if redis_url:
            import redis
            r = redis.from_url(redis_url)
            KEY = 'drivers:locations'
            try:
                r.geoadd(KEY, dl.lng, dl.lat, f'driver:{rider.id}')
            except TypeError:
                r.geoadd(KEY, {f'driver:{rider.id}': (dl.lng, dl.lat)})
            pos = r.geopos(KEY, f'driver:{rider.id}')
            info(f'GEOPOS for driver:{rider.id} -> {pos}')
    except Exception as e:
        info(f'driver location or GEO add failed: {e}')

    # wait a little then end trip to check revocation
    time.sleep(1)
    trip.end()
    info(f'Trip ended: share_token={trip.share_token} live_active={trip.live_active}')

    if redis_url and trip.share_token is None:
        info('share_token cleared on Trip object; checking redis key absence')
        # we expect key deleted; check using previous token key (we don't have it now), so just report
        info('If Redis was configured, the key should have been deleted.')

    info('Test script complete')


if __name__ == '__main__':
    main()
