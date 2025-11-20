#!/usr/bin/env python
"""Test registration with actual HTTP requests to running Django server"""

import requests
import json
import time

test_email = f"test_register_{int(time.time())}@gmail.com"

print(f"\n{'='*70}")
print(f"Testing registration with email verification")
print(f"Email: {test_email}")
print(f"{'='*70}\n")

url = "http://localhost:8000/api/users/register/"

payload = {
    'email': test_email,
    'password': 'TestPassword123!',
    'first_name': 'Test',
    'last_name': 'User',
    'verification_method': 'email'
}

print(f"POST {url}")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(url, json=payload)
    
    print(f"Response Status: {response.status_code}")
    try:
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response Body (raw): {response.text}")
    
    if response.status_code == 201:
        print("\n✅ Registration successful!")
        print(f"Check Django logs for OTP email sending status.")
        print(f"\nNote: The OTP email should have been sent to {test_email}")
        print(f"If you see '[REGISTER] OTP email sent successfully' in Django logs, the fix works!")
    else:
        print("\n❌ Registration failed!")
        
except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure Django development server is running on localhost:8000")
