#!/usr/bin/env python
"""Test: Register -> Login (fail) -> Verify -> Login (success)"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
test_email = 'taonuga01@gmail.com'

# Clean up any existing user
User.objects.filter(email=test_email).delete()

print('=' * 70)
print('TEST: Register -> Login Before Verify -> Verify -> Login After Verify')
print('=' * 70)

client = Client(enforce_csrf_checks=False)

# =========================================================================
# STEP 1: Register User
# =========================================================================
print('\n[STEP 1] Registering user...\n')
register_payload = {
    'email': test_email,
    'phone': '+234902201777',
    'first_name': 'Test',
    'last_name': 'User',
    'password': 'SecurePass123!',
    'password2': 'SecurePass123!',
    'verification_method': 'email'
}

register_response = client.post(
    '/api/users/register/',
    data=json.dumps(register_payload),
    content_type='application/json'
)

if register_response.status_code == 201:
    register_data = json.loads(register_response.content)
    otp_code = register_data.get('otp_code')
    print(f'[OK] User registered successfully!')
    print(f'  Email: {register_data.get("email")}')
    print(f'  Method: {register_data.get("verification_method")}')
    print(f'  OTP Code: {otp_code}')
    print(f'  Message: {register_data.get("detail")}')
else:
    print(f'[FAIL] Registration failed with status {register_response.status_code}')
    print(register_response.content.decode()[:300])
    exit(1)

# =========================================================================
# STEP 2: Try to Login BEFORE Verifying Email (Should Fail)
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 2] Attempting login BEFORE email verification (should fail)...\n')

login_payload = {
    'email': test_email,
    'password': 'SecurePass123!'
}

login_response = client.post(
    '/api/users/token/',
    data=json.dumps(login_payload),
    content_type='application/json'
)

if login_response.status_code != 200:
    login_error = json.loads(login_response.content)
    print(f'[EXPECTED] Login failed with status {login_response.status_code}')
    print(f'  Error: {login_error}')
else:
    print(f'[UNEXPECTED] Login succeeded before verification!')
    print(f'  Response: {json.loads(login_response.content)}')

# =========================================================================
# STEP 3: Verify Email with OTP Code
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 3] Verifying email with OTP code...\n')

if not otp_code:
    print('[FAIL] No OTP code available!')
    exit(1)

verify_payload = {
    'email': test_email,
    'code': otp_code,
    'method': 'email'
}

verify_response = client.post(
    '/api/users/otp/verify/',
    data=json.dumps(verify_payload),
    content_type='application/json'
)

if verify_response.status_code == 200:
    verify_data = json.loads(verify_response.content)
    print(f'[OK] Email verified successfully!')
    print(f'  Response: {verify_data}')
else:
    print(f'[FAIL] Verification failed with status {verify_response.status_code}')
    print(verify_response.content.decode()[:300])
    exit(1)

# =========================================================================
# STEP 4: Login AFTER Verifying Email (Should Succeed)
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 4] Attempting login AFTER email verification (should succeed)...\n')

login_response = client.post(
    '/api/users/token/',
    data=json.dumps(login_payload),
    content_type='application/json'
)

if login_response.status_code == 200:
    login_data = json.loads(login_response.content)
    print(f'[OK] Login successful!')
    print(f'  Access Token: {login_data.get("access")[:50]}...')
    print(f'  Refresh Token: {login_data.get("refresh")[:50]}...')
else:
    login_error = json.loads(login_response.content)
    print(f'[FAIL] Login failed with status {login_response.status_code}')
    print(f'  Error: {login_error}')
    exit(1)

print('\n' + '=' * 70)
print('TEST COMPLETED SUCCESSFULLY!')
print('=' * 70)
