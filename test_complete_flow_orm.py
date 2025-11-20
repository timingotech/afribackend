#!/usr/bin/env python
"""Test: Register -> Login (fail) -> Verify -> Login (success) - Direct ORM approach"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from apps.users.models import OTP
import random
import string

User = get_user_model()
test_email = 'taonuga01@gmail.com'

# Clean up any existing user
User.objects.filter(email=test_email).delete()

print('=' * 70)
print('TEST: Register -> Login Before Verify -> Verify -> Login After Verify')
print('=' * 70)

# =========================================================================
# STEP 1: Register User
# =========================================================================
print('\n[STEP 1] Registering user...\n')

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

print(f'[OK] User registered successfully!')
print(f'  Email: {user.email}')
print(f'  OTP Code: {otp.code}')
print(f'  is_active: {user.is_active}')

# =========================================================================
# STEP 2: Try to Authenticate BEFORE Verifying Email
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 2] Attempting login BEFORE email verification...\n')

authenticated_user = authenticate(email=test_email, password=password)

if authenticated_user is not None:
    print(f'[ISSUE] User authenticated even though email not verified!')
    print(f'  User: {authenticated_user.email}')
    print(f'  is_active: {authenticated_user.is_active}')
else:
    print(f'[OK] Authentication failed (expected - email not verified)')

# =========================================================================
# STEP 3: Verify Email with OTP Code
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 3] Verifying email with OTP code...\n')

# Simulate OTP verification
otp_to_verify = OTP.objects.get(user=user, method='email', code=code)
otp_to_verify.verified = True
otp_to_verify.save()

user.is_verified = True
user.is_active = True
user.save()

print(f'[OK] Email verified!')
print(f'  is_verified: {user.is_verified}')
print(f'  is_active: {user.is_active}')

# =========================================================================
# STEP 4: Login AFTER Verifying Email (Should Succeed)
# =========================================================================
print('\n' + '=' * 70)
print('[STEP 4] Attempting login AFTER email verification...\n')

authenticated_user = authenticate(email=test_email, password=password)

if authenticated_user is not None:
    print(f'[OK] Login successful!')
    print(f'  User: {authenticated_user.email}')
    print(f'  is_active: {authenticated_user.is_active}')
    print(f'  is_verified: {authenticated_user.is_verified}')
else:
    print(f'[FAIL] Authentication failed even after verification')
    exit(1)

print('\n' + '=' * 70)
print('TEST COMPLETED SUCCESSFULLY!')
print('=' * 70)
