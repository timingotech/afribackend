#!/usr/bin/env python
"""Test email configuration on Railway production"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

django.setup()

from django.conf import settings
from django.core.mail import get_connection, send_mail

print("\n" + "="*70)
print("EMAIL CONFIGURATION DIAGNOSTIC")
print("="*70 + "\n")

print("Current EMAIL Settings:")
print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"  EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

print("\n" + "-"*70)
print("Testing Connection...")
print("-"*70 + "\n")

try:
    connection = get_connection()
    print(f"Connection created: {connection.__class__.__name__}")
    
    if connection.open():
        print("✅ Connection opened successfully")
        connection.close()
    else:
        print("❌ Failed to open connection")
except Exception as e:
    print(f"❌ Error creating connection: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-"*70)
print("Testing send_mail()...")
print("-"*70 + "\n")

try:
    result = send_mail(
        subject="[TEST] AAfri Ride Email Configuration",
        message="This is a test email to verify the email configuration is working.",
        from_email='support@aafriride.com',
        recipient_list=['test.email.config@gmail.com'],
        fail_silently=False,
    )
    print(f"✅ send_mail() successful! Result: {result}")
except Exception as e:
    print(f"❌ send_mail() failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70 + "\n")
