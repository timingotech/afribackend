#!/usr/bin/env python
"""Verify OTP and login"""
import requests
import json

API_BASE_URL = "https://afribackend-production-e293.up.railway.app/api"
OTP_CODE = "948231"
EMAIL = "oyenugaridwan@gmail.com"
PASSWORD = "TestPass123!"

print("=" * 80)
print("STEP 1: VERIFY OTP")
print("=" * 80)

verify_data = {
    "method": "email",
    "email": EMAIL,
    "code": OTP_CODE
}

response = requests.post(f"{API_BASE_URL}/users/otp/verify/", json=verify_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("\n✓ OTP VERIFIED SUCCESSFULLY\n")
    
    print("=" * 80)
    print("STEP 2: LOGIN WITH VERIFIED ACCOUNT")
    print("=" * 80)
    
    login_data = {
        "email": EMAIL,
        "password": PASSWORD
    }
    
    response = requests.post(f"{API_BASE_URL}/users/login/", json=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        login_response = response.json()
        print(f"\n✓ LOGIN SUCCESSFUL")
        print(f"Access Token: {login_response['access'][:50]}...")
        print(f"\nYou can now login to the app with:")
        print(f"  Email: {EMAIL}")
        print(f"  Password: {PASSWORD}")
    else:
        print(f"Login failed: {response.json()}")
else:
    print(f"OTP verification failed: {response.json()}")
