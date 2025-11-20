#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test registration via API using Django test client"""
import os
import sys
import django

# Force UTF-8 encoding for Windows terminal
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json

User = get_user_model()

# Delete any existing test user
test_email = "apitest999@gmail.com"
User.objects.filter(email=test_email).delete()
print(f"[OK] Cleared existing test user: {test_email}\n")

# Create a test client
client = Client()

# Test registration via API
print("=" * 60)
print("Testing Registration API with Email Verification")
print("=" * 60)

payload = {
    'email': test_email,
    'phone': '+2349022013174',
    'first_name': 'API',
    'last_name': 'Test',
    'password': 'SecurePass123!',
    'password2': 'SecurePass123!',
    'verification_method': 'email'
}

response = client.post(
    '/api/users/register/',
    data=json.dumps(payload),
    content_type='application/json'
)

print(f"\nStatus Code: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
print(f"Response (raw):")
print(response.content.decode('utf-8') if isinstance(response.content, bytes) else response.content)

try:
    response_data = json.loads(response.content)
    print(json.dumps(response_data, indent=2))
except json.JSONDecodeError as e:
    print(f"Could not parse as JSON: {e}")
    response_data = None

# Check if user was created
try:
    user = User.objects.get(email=test_email)
    print(f"\n[OK] User created!")
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    
    # Check OTP
    from apps.users.models import OTP
    otp = OTP.objects.filter(user=user, method='email').latest('created_at')
    print(f"\n[OK] OTP created!")
    print(f"  Code: {otp.code}")
    print(f"  Method: {otp.method}")
except User.DoesNotExist:
    print(f"\n[FAIL] User was not created")
except OTP.DoesNotExist:
    print(f"\n[FAIL] OTP was not created")

print("\n" + "=" * 60)
