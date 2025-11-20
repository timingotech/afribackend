#!/usr/bin/env python
"""Test registration with detailed logging to see where email sending fails"""

import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.test import Client
import json

# Enable Django logging to see all logs
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

client = Client()

test_email = f"test_register_{int(time.time())}@gmail.com"

print(f"\n{'='*70}")
print(f"Testing registration with email verification")
print(f"Email: {test_email}")
print(f"{'='*70}\n")

# Make registration request
response = client.post(
    'http://localhost:8000/api/users/register/',
    data=json.dumps({
        'email': test_email,
        'password': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User',
        'verification_method': 'email'
    }),
    content_type='application/json'
)

print(f"\nResponse Status: {response.status_code}")
print(f"Response Body: {response.json()}")

if response.status_code == 201:
    print("\n✅ Registration successful! Check logs above for OTP email sending status.")
else:
    print("\n❌ Registration failed!")
