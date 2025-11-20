#!/usr/bin/env python
"""Generate OTP and send to existing user"""
import requests
import json

API_BASE_URL = "https://afribackend-production-e293.up.railway.app/api"

print("=" * 80)
print("GENERATING AND SENDING OTP EMAIL")
print("=" * 80)

otp_request = {
    "method": "email",
    "email": "oyenugaridwan@gmail.com"
}

print(f"\nEmail: oyenugaridwan@gmail.com")
print(f"Method: email\n")
print(f"Sending OTP generation request...\n")

response = requests.post(f"{API_BASE_URL}/users/otp/generate/", json=otp_request)

print(f"Status Code: {response.status_code}")
print(f"\nResponse:")

try:
    response_data = response.json()
    print(json.dumps(response_data, indent=2))
    
    if response.status_code == 200:
        otp_code = response_data.get('code')
        print("\n" + "=" * 80)
        print("✓ OTP GENERATED AND EMAIL SENT")
        print("=" * 80)
        print(f"\nOTP Code: {otp_code}")
        print(f"\nEmail sent to: oyenugaridwan@gmail.com")
        print("Check your email inbox (and spam folder) for the verification code.")
        print(f"\nYou can use this code with the OTP verification endpoint:")
        print(f"POST {API_BASE_URL}/users/otp/verify/")
        print("Body: {\"method\": \"email\", \"email\": \"oyenugaridwan@gmail.com\", \"code\": \"" + otp_code + "\"}")
except:
    print(f"Raw response: {response.text[:500]}")
