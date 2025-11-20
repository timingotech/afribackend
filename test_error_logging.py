#!/usr/bin/env python
"""Test error logging system"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.notifications.models import ErrorLog
from apps.notifications.utils import log_error, log_exception
from django.contrib.auth import get_user_model

User = get_user_model()

print('=' * 70)
print('Testing Error Logging System')
print('=' * 70)

# Get or create a test user
test_user = User.objects.filter(email='errortest@test.com').first()
if not test_user:
    test_user = User.objects.create_user(
        email='errortest@test.com',
        password='TestPass123!'
    )
    print(f'\n[OK] Created test user: {test_user.email}')
else:
    print(f'\n[OK] Using existing test user: {test_user.email}')

# Clear existing errors for this user
ErrorLog.objects.filter(user=test_user).delete()
print(f'[OK] Cleared existing error logs for this user')

# =========================================================================
# Test 1: Log a validation error
# =========================================================================
print('\n[TEST 1] Logging a validation error...')

error1 = log_error(
    error_type='validation',
    title='Invalid Email Format',
    message='The email format is not valid. Expected format: user@example.com',
    status_code=400,
    user=test_user,
    endpoint='/api/users/register/',
    method='POST',
    request_data={'email': 'invalid-email', 'password': 'test'},
    severity='medium'
)

if error1:
    print(f'[OK] Error logged: {error1.id}')
    print(f'  Title: {error1.title}')
    print(f'  Severity: {error1.get_severity_display()}')
else:
    print(f'[FAIL] Failed to log error')

# =========================================================================
# Test 2: Log an authentication error
# =========================================================================
print('\n[TEST 2] Logging an authentication error...')

error2 = log_error(
    error_type='authentication',
    title='Invalid Credentials',
    message='The email or password provided is incorrect.',
    status_code=401,
    user=test_user,
    endpoint='/api/users/token/',
    method='POST',
    severity='high'
)

if error2:
    print(f'[OK] Error logged: {error2.id}')
    print(f'  Title: {error2.title}')
    print(f'  Severity: {error2.get_severity_display()}')
else:
    print(f'[FAIL] Failed to log error')

# =========================================================================
# Test 3: Log a server error with exception
# =========================================================================
print('\n[TEST 3] Logging a server error with exception...')

try:
    # Intentionally cause an error
    1 / 0
except ZeroDivisionError as e:
    error3 = log_exception(
        exception=e,
        title='Division by Zero Error',
        user=test_user,
        endpoint='/api/trips/calculate/',
        method='POST',
        error_type='server',
        severity='critical'
    )
    
    if error3:
        print(f'[OK] Error logged: {error3.id}')
        print(f'  Title: {error3.title}')
        print(f'  Severity: {error3.get_severity_display()}')
        if error3.traceback:
            print(f'  Has traceback: Yes')
    else:
        print(f'[FAIL] Failed to log error')

# =========================================================================
# Test 4: Query recent errors
# =========================================================================
print('\n[TEST 4] Querying recent errors...')

recent_errors = ErrorLog.objects.filter(user=test_user).order_by('-created_at')[:5]
print(f'[OK] Found {recent_errors.count()} errors')
for error in recent_errors:
    print(f'  - {error.title} ({error.error_type}) [{error.get_severity_display()}]')

# =========================================================================
# Test 5: Check auto-deletion property
# =========================================================================
print('\n[TEST 5] Checking auto-deletion property...')

if error1:
    print(f'  Error is_old: {error1.is_old}')
    print(f'  Error created_at: {error1.created_at}')
    print(f'  Errors older than 30 days will be auto-deleted')

print('\n' + '=' * 70)
print('All Tests Completed!')
print('=' * 70)
