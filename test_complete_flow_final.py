#!/usr/bin/env python
"""Test complete registration -> OTP verification -> login flow"""

import requests
import json

BASE_URL = "http://localhost:8001/api"
test_email = "taonuga01@gmail.com"
test_password = "TestPassword123!"

print("\n" + "="*70)
print("TESTING COMPLETE FLOW: REGISTER -> VERIFY -> LOGIN")
print("="*70 + "\n")

# Step 1: Get the OTP from database
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import OTP

User = get_user_model()
user = User.objects.get(email=test_email)
otp = OTP.objects.filter(user=user).first()

if not otp:
    print(f"ERROR: No OTP found for {test_email}")
    sys.exit(1)

otp_code = otp.code
print(f"Step 1: Registration completed")
print(f"  Email: {test_email}")
print(f"  OTP Code (from DB): {otp_code}\n")

# Step 2: Verify OTP
print(f"Step 2: Verifying OTP...")
verify_response = requests.post(
    f"{BASE_URL}/users/otp/verify/",
    json={
        "email": test_email,
        "code": otp_code
    }
)

print(f"  Status: {verify_response.status_code}")
if verify_response.status_code == 200:
    print(f"  ✅ OTP verified successfully\n")
else:
    print(f"  ❌ OTP verification failed")
    print(f"  Response: {verify_response.json()}\n")
    sys.exit(1)

# Step 3: Login with email and password
print(f"Step 3: Logging in...")
login_response = requests.post(
    f"{BASE_URL}/users/login/",
    json={
        "email": test_email,
        "password": test_password
    }
)

print(f"  Status: {login_response.status_code}")
if login_response.status_code == 200:
    tokens = login_response.json()
    print(f"  ✅ Login successful!")
    print(f"  Access Token: {tokens.get('access', 'N/A')[:50]}...")
    print(f"  Refresh Token: {tokens.get('refresh', 'N/A')[:50]}...\n")
    
    print("="*70)
    print("SUCCESS: COMPLETE FLOW WORKING!")
    print("="*70 + "\n")
else:
    print(f"  ❌ Login failed")
    print(f"  Response: {login_response.json()}\n")
    sys.exit(1)
