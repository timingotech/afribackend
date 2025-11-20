#!/usr/bin/env python
"""Test registration directly by simulating the serializer and view"""

import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env before Django setup
from dotenv import load_dotenv
load_dotenv()

django.setup()

from apps.users.serializers import RegisterSerializer
from rest_framework.test import APIRequestFactory
import json

print(f"\n{'='*70}")
print("TESTING REGISTRATION WITH DETAILED EMAIL LOGGING")
print(f"{'='*70}\n")

factory = APIRequestFactory()
test_email = "taonuga01@gmail.com"

# Create registration data
data = {
    'email': test_email,
    'password': 'TestPassword123!',
    'password2': 'TestPassword123!',
    'first_name': 'Test',
    'last_name': 'User',
    'role': 'customer',
    'verification_method': 'email'
}

print(f"Test Email: {test_email}\n")

# Simulate what the view does
serializer = RegisterSerializer(data=data)

if serializer.is_valid():
    print(f"✅ Serializer validation passed")
    print(f"   Validated data: {json.dumps({k: v for k, v in serializer.validated_data.items() if k != 'password'}, indent=6)}\n")
    
    # Call perform_create (which is what the view does)
    print("Calling perform_create (simulating registration view)...\n")
    
    # Manually do what the view does
    user = serializer.save()
    print(f"✅ User created: {user.email} (ID: {user.id})")
    
    # Check if _verification_method was set
    verification_method = getattr(user, '_verification_method', 'NOT SET')
    print(f"   verification_method on user: {verification_method}\n")
    
    # Check OTP
    from apps.users.models import OTP
    otp = OTP.objects.filter(user=user).first()
    if otp:
        print(f"✅ OTP created: {otp.code}")
        print(f"   Email: {otp.email}")
        print(f"   Method: {otp.method}\n")
    else:
        print(f"❌ No OTP found for user!\n")
    
    print("✅ Registration simulation completed successfully!")
    print(f"\nNote: Check your email at {test_email} for the OTP code.")
    print(f"If you received an email, the fix works!")
    
else:
    print(f"❌ Serializer validation failed:")
    print(f"   Errors: {serializer.errors}")
