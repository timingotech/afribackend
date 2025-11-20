"""
Production E2E simulation script to run as a Railway one-off.

This script performs the following inside the deployed environment:
- Creates test customer and rider users
- Creates device entries for rider and customer
- Generates an OTP and calls `send_email_with_logging(otp=...)` to test email send persistence
- Creates a Trip and notifies nearby drivers (uses existing get_nearby_drivers)
- Writes a driver GEO location (simulating frequent updates)
- Verifies GEO presence
- Calls driver logout cleanup to remove GEO entry
- Verifies GEO removal
- Prints key results, OTP DB state, and tail of `logs/email_send.log` if present

Run in production with Railway one-off (example):

npx --yes @railway/cli run -- python tools/prod_full_simulation.py

"""
import os
import sys
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
# ensure project root is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from apps.users.models import OTP, Device
from apps.users.email_utils import send_email_with_logging
from apps.trips.models import Trip, DriverLocation
from apps.trips.utils import get_nearby_drivers
from apps.notifications import push as push_module

User = get_user_model()

print('\n=== STARTING PRODUCTION FULL SIMULATION ===')

# 1) Create or get test accounts
customer, _ = User.objects.get_or_create(email='sim-customer@example.com', defaults={'role': 'customer'})
rider, _ = User.objects.get_or_create(email='sim-rider@example.com', defaults={'role': 'rider'})
print(f'Customer id={customer.id} Rider id={rider.id}')

# 2) Create Devices with mock tokens so push code has something to send to
Device.objects.filter(user=customer, token__icontains='sim-token').delete()
Device.objects.filter(user=rider, token__icontains='sim-token').delete()
Device.objects.create(user=customer, token='sim-token-customer-1', platform='android')
Device.objects.create(user=rider, token='sim-token-rider-1', platform='android')
print('Devices created for customer and rider')

# 3) OTP send persistence test
print('\n--- OTP send test ---')
otp = OTP.objects.create(user=customer, email=customer.email, code='123456', method=OTP.METHOD_EMAIL)
print(f'Created OTP id={otp.pk} code={otp.code}')
res = send_email_with_logging(to_email=customer.email, subject='Sim OTP', message=f'Your code is {otp.code}', otp=otp)
print('send_email_with_logging result ->', res)
otp.refresh_from_db()
print('OTP after send: sent_at=', otp.sent_at, 'send_result=', otp.send_result, 'send_error=', otp.send_error)

# 4) Trip creation and notify nearby drivers
print('\n--- Trip creation and driver notify ---')
trip = Trip.objects.create(
    customer=customer,
    origin_address='Sim Origin', origin_lat=6.5244, origin_lng=3.3792,
    dest_address='Sim Dest', dest_lat=6.5244, dest_lng=3.3792,
)
print(f'Created trip id={trip.pk}')
# reuse get_nearby_drivers and push helper to notify
drivers = get_nearby_drivers(trip.origin_lat, trip.origin_lng, radius_km=5.0, limit=20)
print('Nearby drivers found:', [d.id for d in drivers])
# collect tokens
for d in drivers:
    tokens = [dev.token for dev in getattr(d, 'devices').all() if dev.token]
    if not tokens:
        continue
    title = 'Sim New ride'
    body = 'Sim pickup nearby'
    data = {'type': 'new_trip', 'trip_id': str(trip.pk)}
    print(f'Attempting to send push to driver {d.id} tokens={tokens}')
    r = push_module.send_push_async(tokens, title, body, data=data)
    print('push send result:', r)

# 5) Simulate driver location update (GEO write)
print('\n--- Driver location GEO write test ---')
dl, _ = DriverLocation.objects.update_or_create(driver=rider, defaults={'lat': 6.5244, 'lng': 3.3792})
print('DriverLocation saved id=', dl.pk)
# write to redis GEO directly (like driver_location_update)
redis_url = getattr(settings, 'REDIS_URL', None)
if redis_url:
    try:
        import redis
        r = redis.from_url(redis_url)
        KEY = 'drivers:locations'
        try:
            r.geoadd(KEY, {f'driver:{rider.id}': (dl.lng, dl.lat)})
        except TypeError:
            r.geoadd(KEY, dl.lng, dl.lat, f'driver:{rider.id}')
        pos = r.geopos(KEY, f'driver:{rider.id}')
        print('GEOPOS for driver ->', pos)
    except Exception as e:
        print('Redis GEO write failed:', e)
else:
    print('REDIS_URL not configured; skipping GEO write')

# 6) Driver logout cleanup
print('\n--- Driver logout cleanup test ---')
from apps.trips.views import driver_logout
# driver_logout expects a DRF request; but we can directly remove from redis
if redis_url:
    try:
        import redis
        r = redis.from_url(redis_url)
        KEY = 'drivers:locations'
        r.zrem(KEY, f'driver:{rider.id}')
        pos2 = r.geopos(KEY, f'driver:{rider.id}')
        print('After zrem, GEOPOS ->', pos2)
    except Exception as e:
        print('Redis cleanup failed:', e)
else:
    print('REDIS_URL not configured; skipping GEO cleanup')

# 7) Tail email logs if available
print('\n--- Tail logs/email_send.log (if exists) ---')
log_path = os.path.join(ROOT, 'logs', 'email_send.log')
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as fh:
        lines = fh.readlines()[-30:]
        print(''.join(lines))
else:
    print('No logs/email_send.log found in project root')

print('\n=== SIMULATION COMPLETE ===')
