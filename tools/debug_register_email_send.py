#!/usr/bin/env python
"""Debug helper: trigger registration and force Celery tasks to run eagerly

Usage:
    python tools/debug_register_email_send.py --email you@example.com

This will:
 - Force Celery tasks to run synchronously (task_always_eager)
 - Post to the registration view using Django's test client
 - Print server response, resulting OTP and OTP DB fields
 - Print tail of `logs/email_send.log` so we can see whether a real send was attempted

Note: This script depends on Django settings and will use SMTP settings found in environment. To actually send an email you must ensure SMTP env vars are populated
and the email backend is not `console.EmailBackend`.
"""

import os
import sys
import django
import argparse
import json
import time

# Ensure we use local Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
# Ensure the project root is in sys.path so `backend_project` is importable when running the script from tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Force celery tasks to run eagerly for this run
os.environ['CELERY_TASK_ALWAYS_EAGER'] = 'True'
# Propagate exceptions to see failures
os.environ['CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS'] = 'True'

def main(email):
    # Debug prints to ensure environment is set correctly
    import sys
    print('SCRIPT CWD:', sys.path[0])
    print('DJANGO_SETTINGS_MODULE BEFORE:', os.environ.get('DJANGO_SETTINGS_MODULE'))
    print('sys.path sample:', sys.path[:5])
    django.setup()
    from django.test import Client
    from django.conf import settings
    from django.utils import timezone
    from apps.users.models import OTP, User

    client = Client()
    data = {
        'email': email,
        'password': 'Password123!',
        'password2': 'Password123!',
        'first_name': 'Debug',
        'last_name': 'User',
        'role': 'customer',
        'verification_method': 'email',
    }

    url = '/api/users/register/'
    print(f"Posting to {url} with email: {email}")

    response = client.post(url, data=json.dumps(data), content_type='application/json')
    print(f"Status: {response.status_code}")
    try:
        body = response.json()
        print(json.dumps(body, indent=2))
    except Exception:
        print(response.content)

    # Find latest OTP for this email
    latest_otp = OTP.objects.filter(email=email, method='email').order_by('-created_at').first()
    if latest_otp:
        print("Found OTP in DB:")
        print(f"  id: {latest_otp.id}")
        print(f"  code: {latest_otp.code}")
        print(f"  sent_at: {latest_otp.sent_at}")
        print(f"  send_result: {latest_otp.send_result}")
        print(f"  send_error: {latest_otp.send_error}")
        print(f"  created_at: {latest_otp.created_at}")
        print(f"  verified: {latest_otp.verified}")
    else:
        print("No OTP record found for this email.")

    # Print tail of email logic log file
    log_path = 'logs/email_send.log'
    if os.path.exists(log_path):
        print('\nTail of logs/email_send.log:\n')
        with open(log_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            seek = max(0, size - 8000)
            f.seek(seek)
            print(f.read().decode('utf-8', errors='replace'))
    else:
        print('\nNo logs/email_send.log present.')

    # Print the django email backend used
    print('\nEmail backend setting:', settings.EMAIL_BACKEND)
    print('EMAIL_HOST:', settings.EMAIL_HOST, 'EMAIL_PORT:', settings.EMAIL_PORT)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', '-e', required=True, help='Email to register and test')
    args = parser.parse_args()
    main(args.email)
