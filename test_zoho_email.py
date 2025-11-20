#!/usr/bin/env python
"""Test Zoho email backend directly"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("=" * 80)
print("TESTING ZOHO EMAIL BACKEND")
print("=" * 80)

print(f"\nEmail Configuration:")
print(f"  Backend: {settings.EMAIL_BACKEND}")
print(f"  Host: {settings.EMAIL_HOST}")
print(f"  Port: {settings.EMAIL_PORT}")
print(f"  Use TLS: {settings.EMAIL_USE_TLS}")
print(f"  User: {settings.EMAIL_HOST_USER}")
print(f"  From: {settings.DEFAULT_FROM_EMAIL}")

# Test sending email with error details
print(f"\nAttempting to send test email...\n")

try:
    result = send_mail(
        subject="Test Email from AAfri Ride",
        message="This is a test email to verify the Zoho mail backend is working.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['oyenugaridwan@gmail.com'],
        fail_silently=False  # Don't fail silently so we see the error
    )
    print(f"✓ Email sent successfully! Result: {result}")
except Exception as e:
    print(f"✗ Email sending failed:")
    print(f"  Error: {e}")
    print(f"  Type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
