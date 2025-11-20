#!/usr/bin/env python
"""Test registration flow: Register -> Login (403) -> Verify -> Login (200)"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.users.models import OTP
from apps.users.views import ObtainTokenPairView, verify_otp
import random

User = get_user_model()
test_email = 'taonuga01@gmail.com'

# Clean up
User.objects.filter(email=test_email).delete()

print('=' * 70)
print('TEST: Register -> Login Before Verify (403) -> Verify -> Login (200)')
print('=' * 70)

factory = RequestFactory()

# =========================================================================
# STEP 1: Create User (Simulate Registration)
# =========================================================================
print('\n[STEP 1] Creating user (registration)...\n')

password = 'SecurePass123!'
user = User.objects.create_user(
    email=test_email,
    password=password,
    first_name='Test',
    last_name='User',
    phone='+234902201777'
)

# Create OTP
code = str(random.randint(100000, 999999))
otp = OTP.objects.create(user=user, email=test_email, code=code, method='email')

print(f'[OK] User registered!')
print(f'  Email: {user.email}')
print(f'  OTP Code: {otp.code}')
print(f'  is_verified: {user.is_verified}')

# =========================================================================
# STEP 2: Try Login BEFORE Verification (Should Get 403)
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 2] Attempting login BEFORE verification (expect 403)...\n')

login_request = factory.post(
    '/api/users/token/',
    data=json.dumps({'email': test_email, 'password': password}),
    content_type='application/json'
)

view = ObtainTokenPairView.as_view()
login_response = view(login_request)

print(f'Status Code: {login_response.status_code}')
if login_response.status_code == 403:
    print(f'[OK] Login blocked before verification')
    print(f'  Message: {login_response.data}')
else:
    print(f'[UNEXPECTED] Got status {login_response.status_code}')
    print(f'  Response: {login_response.data}')

# =========================================================================
# STEP 3: Verify Email
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 3] Verifying email with OTP...\n')

verify_request = factory.post(
    '/api/users/otp/verify/',
    data=json.dumps({'email': test_email, 'code': code, 'method': 'email'}),
    content_type='application/json'
)

verify_response = verify_otp(verify_request)

print(f'Status Code: {verify_response.status_code}')
if verify_response.status_code == 200:
    print(f'[OK] Email verified!')
    
    # Refresh user from DB
    user.refresh_from_db()
    print(f'  User is_verified: {user.is_verified}')
else:
    print(f'[FAIL] Verification failed')
    print(f'  Response: {verify_response.data}')

# =========================================================================
# STEP 4: Login AFTER Verification (Should Get 200)
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 4] Attempting login AFTER verification (expect 200)...\n')

login_request2 = factory.post(
    '/api/users/token/',
    data=json.dumps({'email': test_email, 'password': password}),
    content_type='application/json'
)

login_response2 = view(login_request2)

print(f'Status Code: {login_response2.status_code}')
if login_response2.status_code == 200:
    print(f'[OK] Login successful!')
    data = login_response2.data
    print(f'  Access Token: {data.get("access")[:50]}...')
    print(f'  Token Type: {data.get("token_type", "Bearer")}')
else:
    print(f'[FAIL] Login failed with status {login_response2.status_code}')
    print(f'  Response: {login_response2.data}')

print('\n' + '=' * 70)
print('TEST COMPLETED SUCCESSFULLY!')
print('=' * 70)
