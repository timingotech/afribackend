#!/usr/bin/env python
"""Test synchronous email sending (what registration will use as fallback)"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.users.email import send_otp_email
import random

print("Testing synchronous email send (registration fallback)...")
try:
    code = str(random.randint(100000, 999999))
    result = send_otp_email('oyenugaridwan@gmail.com', code)
    if result:
        print(f"✅ Email sent successfully!")
        print(f"Code: {code}")
    else:
        print(f"❌ Email send returned False")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
