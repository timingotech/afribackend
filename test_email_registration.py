#!/usr/bin/env python
"""Test user registration and OTP email"""
import requests
import json

API_BASE_URL = "https://afribackend-production-e293.up.railway.app/api"

# Test registration
registration_data = {
    "email": "oyenugaridwan@gmail.com",
    "phone": "00908884084",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "first_name": "Ridwan",
    "last_name": "Oyenuga",
    "role": "customer",
    "verification_method": "email"
}

print("=" * 80)
print("REGISTERING USER AND SENDING OTP EMAIL")
print("=" * 80)
print(f"\nEmail: {registration_data['email']}")
print(f"Phone: {registration_data['phone']}")
print(f"Verification Method: email")
print(f"\nSending registration request to: {API_BASE_URL}/users/register/\n")

response = requests.post(f"{API_BASE_URL}/users/register/", json=registration_data)

print(f"Status Code: {response.status_code}")
print(f"\nResponse:")

# Try to parse as JSON, fall back to text if it's HTML
try:
    response_data = response.json()
    print(json.dumps(response_data, indent=2))
except:
    print(f"Raw response (first 500 chars): {response.text[:500]}")
    response_data = None

if response.status_code == 201:
    print("\n" + "=" * 80)
    print("✓ REGISTRATION SUCCESSFUL")
    print("=" * 80)
    
    if response_data and 'otp_code' in response_data:
        print(f"\nOTP Code (for testing): {response_data['otp_code']}")
    
    print(f"\nEmail verification code sent to: {registration_data['email']}")
    print("Check your email inbox (and spam folder) for the verification code.")
    
elif response.status_code == 400:
    print("\n⚠ User may already exist or validation error")
    print("You can proceed to verify the existing account with the OTP code sent to the email.")
else:
    print(f"\n✗ Error occurred: {response.status_code}")
    if response_data:
        print(f"Error details: {response_data}")
    else:
        print("Server returned HTML error page (check logs)")
