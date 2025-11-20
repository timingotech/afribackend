#!/usr/bin/env python
"""Create an OTP row and send it to the target email using send_email_with_logging

This script mirrors production registration's behavior but runs locally.
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
# ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Make dotenv optional so the script can run in environments where it's not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # In production the environment variables are provided by Railway; dotenv isn't required
    pass
import django
django.setup()

from apps.users.models import OTP, User
from apps.users.email_utils import send_email_with_logging
import random
from django.utils import timezone

TARGET = 'taonuga01@gmail.com'

code = str(random.randint(100000, 999999))
# create OTP row
otp = OTP.objects.create(email=TARGET, code=code, method='email')
print(f"Created OTP id={otp.id} code={otp.code} created_at={otp.created_at.isoformat()}")

subject = "Your AAfri Ride Verification Code"
message = f"Your verification code is: {code}\n\nValid for 10 minutes."
res = send_email_with_logging(TARGET, subject, message, from_email='support@aafriride.com')
print("send_email_with_logging returned:", res)

# show last few lines of log file if present
LOG = 'logs/email_send.log'
if os.path.exists(LOG):
    with open(LOG, 'rb') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        seek = max(0, size - 4000)
        f.seek(seek)
        tail = f.read().decode('utf-8', errors='replace')
    print('\n--- email_send.log tail ---\n')
    print(tail)
else:
    print('\nNo local send log found.')
