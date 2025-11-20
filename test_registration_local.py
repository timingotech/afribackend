#!/usr/bin/env python
"""Post to local registration endpoint to trigger OTP send locally."""
import requests
import json
import time

print("\n" + "="*70)
print("TESTING LOCAL REGISTRATION WITH ACTUAL EMAIL")
print("="*70 + "\n")

test_email = "taonuga01@gmail.com"

data = {
    'email': test_email,
    'password': 'TestPassword123!',
    'password2': 'TestPassword123!',
    'first_name': 'LocalTest',
    'last_name': 'User',
    'role': 'customer',
    'verification_method': 'email'
}

print(f"Test Email: {test_email}")
print("Making POST request to http://localhost:8000/api/users/register/\n")

try:
    response = requests.post(
        'http://localhost:8000/api/users/register/',
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
        print("SUCCESS: Local registration completed!")
        print(f"Check local logs and inbox for {test_email} for OTP code.")
    else:
        print("FAILED: Local registration did not return 201")

except requests.exceptions.ConnectionError as e:
    print("ERROR: Could not connect to local server at http://localhost:8000")
    print("Make sure Django development server is running (e.g. 'python manage.py runserver')")
    print(f"Details: {e}")
except Exception as e:
    print(f"ERROR: {e}")

# After request, if local log file exists show the tail
import os
log_path = 'logs/email_send.log'
if os.path.exists(log_path):
    print('\nLocal email_send.log tail:\n')
    with open(log_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        seek = max(0, size - 4000)
        f.seek(seek)
        print(f.read().decode('utf-8', errors='replace'))
else:
    print('\nNo local `logs/email_send.log` found.')
