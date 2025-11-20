#!/usr/bin/env python
"""Register new user with OTP and test email sending"""
import requests
import json
from datetime import datetime

API_BASE_URL = "https://afribackend-production-e293.up.railway.app/api"

print("=" * 80)
print("TEST REGISTRATION WITH OTP EMAIL")
print("=" * 80)
print(f"Timestamp: {datetime.now()}")

# Register with adebolaaaaa@gmail.com
registration_data = {
    "email": "adebolaaaaa@gmail.com",
    "phone": "+2349012345678",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "customer",
    "verification_method": "email"
}

print(f"\nRegistering user: {registration_data['email']}")
print(f"Verification method: email")

response = requests.post(f"{API_BASE_URL}/users/register/", json=registration_data)

print(f"\nStatus: {response.status_code}")

try:
    response_data = response.json()
    print(json.dumps(response_data, indent=2))
    
    if response.status_code == 201:
        otp_code = response_data.get('otp_code')
        print(f"\n✓ Registration successful")
        print(f"OTP Code: {otp_code}")
        print(f"\nCheck your email ({registration_data['email']}) for the verification code.")
        print(f"An email should be sent from: support@aafriride.com")
    elif response.status_code == 400 and 'already exists' in str(response_data):
        print(f"\n⚠ User already exists")
        print("Generating new OTP for existing user...")
        
        # Generate OTP for existing user
        otp_request = {
            "method": "email",
            "email": registration_data['email']
        }
        
        otp_response = requests.post(f"{API_BASE_URL}/users/otp/generate/", json=otp_request)
        print(f"\nOTP Generation Status: {otp_response.status_code}")
        otp_data = otp_response.json()
        print(json.dumps(otp_data, indent=2))
        
        if otp_response.status_code == 200:
            otp_code = otp_data.get('code')
            print(f"\n✓ OTP generated and email sent")
            print(f"OTP Code: {otp_code}")
            print(f"Check email for verification code from: support@aafriride.com")
except:
    print(f"Raw response: {response.text[:500]}")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"""
Test Email Sent To: adebolaaaaa@gmail.com
From: support@aafriride.com
Time: {datetime.now()}

Please check:
1. Inbox for registration/OTP emails
2. Spam/Junk folder
3. Let me know what you receive
""")
