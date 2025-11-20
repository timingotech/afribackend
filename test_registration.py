#!/usr/bin/env python
"""Test registration with Celery fallback"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.users.models import User, OTP
from apps.users.serializers import RegisterSerializer
import json

# Test registration
print("=" * 60)
print("Testing Registration with Celery Fallback")
print("=" * 60)

# Delete any existing test user first
test_email = "taonuga01@gmail.com"
User.objects.filter(email=test_email).delete()
print(f"\n✓ Cleared existing test user: {test_email}")

data = {
    'email': test_email,
    'first_name': 'Test',
    'last_name': 'User',
    'password': 'SecurePass123!',
    'verification_method': 'email'
}

serializer = RegisterSerializer(data=data)
if serializer.is_valid():
    print(f"\n✓ Serializer validation passed")
    print(f"  Email: {data['email']}")
    print(f"  Method: {data['verification_method']}")
    
    # Save will trigger perform_create in views
    user = serializer.save()
    print(f"\n✓ User created successfully!")
    print(f"  User ID: {user.id}")
    print(f"  Email: {user.email}")
    
    # Check if OTP was created
    try:
        otp = OTP.objects.filter(user=user, method='email').latest('created_at')
        print(f"\n✓ OTP created!")
        print(f"  Code: {otp.code}")
        print(f"  Method: {otp.method}")
    except OTP.DoesNotExist:
        print(f"\n✗ No OTP found for this user")
else:
    print(f"\n✗ Serializer validation failed:")
    print(json.dumps(serializer.errors, indent=2))

print("\n" + "=" * 60)
