#!/usr/bin/env python
"""Test registration with synchronous email"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
test_email = 'sync_test@gmail.com'
User.objects.filter(email=test_email).delete()
print('[INFO] Testing Registration with Synchronous Email...\n')

# Disable CSRF for testing
client = Client(enforce_csrf_checks=False)
payload = {
    'email': test_email,
    'phone': '+2349022013174',
    'first_name': 'Sync',
    'last_name': 'Test',
    'password': 'SecurePass123!',
    'password2': 'SecurePass123!',
    'verification_method': 'email'
}

response = client.post('/api/users/register/', data=json.dumps(payload), content_type='application/json')
print(f'Status Code: {response.status_code}')
print(f'Content-Type: {response.get("Content-Type")}')
print(f'Raw response: {response.content.decode()}\n')

if response.status_code == 201:
    data = json.loads(response.content)
    print('[OK] Registration successful!')
    print(f"  Email: {data.get('email')}")
    print(f"  Method: {data.get('verification_method')}")
    print(f"  OTP Code: {data.get('otp_code')}")
    print(f"  Message: {data.get('detail')}")
else:
    print('[FAIL] Registration failed')
    print(response.content.decode()[:200])
