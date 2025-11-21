#!/usr/bin/env python
"""Post the Railway payload to the Railway registration endpoint."""
import requests
import json

print("\n" + "="*70)
print("TESTING RAILWAY REGISTRATION WITH RAILWAY PAYLOAD")
print("="*70 + "\n")

data = {
  "email": "oyenugaridwan@gmail.com",
  "phone": "+234902013174",
  "password": "TestPass123!",
  "password2": "TestPass123!",
  "first_name": "Ridwan",
  "last_name": "Oyenung",
  "role": "customer",
  "verification_method": "email"
}

print(f"Test Email: {data['email']}")
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
    except Exception:
        print(f"Response Body: {response.text}\n")

    if response.status_code == 201:
        print("SUCCESS: Railway registration completed using Railway payload!")
        print(f"Check email inbox for {data['email']} for OTP code.")
    else:
        print("FAILED: Railway registration did not return 201")

except requests.exceptions.ConnectionError as e:
    print("ERROR: Could not connect to Railway URL")
    print(f"Details: {e}")
except Exception as e:
    print(f"ERROR: {e}")
