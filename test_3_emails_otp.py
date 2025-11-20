#!/usr/bin/env python
"""Register with all 3 emails to test OTP delivery"""
import requests
import json
from datetime import datetime

API_BASE_URL = "https://afribackend-production-e293.up.railway.app/api"

test_emails = [
    {
        "email": "adebolaaaaa@gmail.com",
        "phone": "+2349012345671",
    },
    {
        "email": "oyenugaridwan@gmail.com",
        "phone": "+2349012345672",
    },
    {
        "email": "taonuga01@gmail.com",
        "phone": "+2349012345673",
    },
]

print("=" * 80)
print("REGISTERING 3 USERS WITH OTP EMAIL TEST")
print("=" * 80)
print(f"Timestamp: {datetime.now()}\n")

results = []

for i, test_user in enumerate(test_emails, 1):
    email = test_user["email"]
    phone = test_user["phone"]
    
    print(f"\n{'='*80}")
    print(f"TEST {i}: {email}")
    print(f"{'='*80}")
    
    registration_data = {
        "email": email,
        "phone": phone,
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": f"Test{i}",
        "last_name": "OTPEmail",
        "role": "customer",
        "verification_method": "email"
    }
    
    print(f"Email: {email}")
    print(f"Phone: {phone}")
    print(f"Sending registration request...")
    
    response = requests.post(f"{API_BASE_URL}/users/register/", json=registration_data)
    
    print(f"Status: {response.status_code}")
    
    try:
        response_data = response.json()
        
        if response.status_code == 201:
            otp_code = response_data.get('otp_code')
            print(f"✓ Registration successful")
            print(f"✓ OTP Code: {otp_code}")
            
            results.append({
                'email': email,
                'status': 'REGISTERED',
                'otp_code': otp_code,
                'timestamp': datetime.now()
            })
        elif response.status_code == 400 and 'already exists' in str(response_data):
            print(f"⚠ User already exists")
            results.append({
                'email': email,
                'status': 'ALREADY_EXISTS',
                'timestamp': datetime.now()
            })
        else:
            print(f"✗ Failed: {response_data}")
            results.append({
                'email': email,
                'status': 'FAILED',
                'error': str(response_data),
                'timestamp': datetime.now()
            })
    except Exception as e:
        print(f"✗ Error: {e}")
        results.append({
            'email': email,
            'status': 'ERROR',
            'error': str(e),
            'timestamp': datetime.now()
        })

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

for result in results:
    email = result['email']
    status = result['status']
    symbol = "✓" if status == "REGISTERED" else "⚠" if status == "ALREADY_EXISTS" else "✗"
    
    print(f"\n{symbol} {email}")
    print(f"   Status: {status}")
    
    if result['status'] == 'REGISTERED':
        print(f"   OTP Code: {result['otp_code']}")
    elif result['status'] == 'FAILED' or result['status'] == 'ERROR':
        print(f"   Error: {result.get('error', 'Unknown')}")

print("\n" + "=" * 80)
print("INSTRUCTIONS")
print("=" * 80)
print(f"""
OTP registration emails should have been sent to:
1. adebolaaaaa@gmail.com
2. oyenugaridwan@gmail.com
3. taonuga01@gmail.com

From: support@aafriride.com

Please check all 3 inboxes (and spam folders) and let me know:
- Which emails received the OTP verification code?
- Which ones didn't?
- Did any go to spam?

This will help identify the root cause of the OTP email delivery issue.
""")
