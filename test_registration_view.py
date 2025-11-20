#!/usr/bin/env python
"""Test registration by making actual HTTP request"""

import requests
import json

print("\n" + "="*70)
print("TESTING REGISTRATION WITH ACTUAL EMAIL")
print("="*70 + "\n")

test_email = "taonuga01@gmail.com"

data = {
    'email': test_email,
    'password': 'TestPassword123!',
    'password2': 'TestPassword123!',
    'first_name': 'Test',
    'last_name': 'User',
    'role': 'customer',
    'verification_method': 'email'
}

print(f"Test Email: {test_email}")
print("Making POST request to https://afribackend-production-e293.up.railway.app/api/users/register/\n")

try:
    response = requests.post(
        'https://afribackend-production-e293.up.railway.app/api/users/register/',
        json=data,
        timeout=30
    )
    
    print(f"Response Status: {response.status_code}")
    try:
        resp_data = response.json()
        print(f"Response Body: {json.dumps(resp_data, indent=2)}\n")
    except:
        print(f"Response Body: {response.text}\n")
    
    if response.status_code == 201:
        print("SUCCESS: Registration completed!")
        print(f"\nCheck your email {test_email} for OTP code.")
        print("Check Django server logs for '[REGISTER]' messages.")
    else:
        print("FAILED: Registration did not return 201")
        
except requests.exceptions.ConnectionError:
    print("ERROR: Could not connect to http://localhost:8000")
    print("Make sure Django development server is running")
except Exception as e:
    print(f"ERROR: {e}")
