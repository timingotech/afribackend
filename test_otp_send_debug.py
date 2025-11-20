#!/usr/bin/env python
"""Test OTP email sending directly like registration does"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import random

print("=" * 80)
print("TESTING OTP EMAIL SENDING LIKE REGISTRATION DOES")
print("=" * 80)

email = "test.otp@gmail.com"
code = str(random.randint(100000, 999999))

print(f"\nEmail: {email}")
print(f"Code: {code}")
print(f"Backend: {settings.EMAIL_BACKEND}")

# Simulate what perform_create does
try:
    print(f"\nAttempting to send OTP email...")
    result = send_mail(
        subject="Your AAfri Ride Verification Code",
        message=f"Your code is: {code}\n\nValid for 10 minutes.",
        from_email='support@aafriride.com',
        recipient_list=[email],
        fail_silently=False,  # Don't fail silently
    )
    print(f"✓ OTP email sent successfully (result: {result})")
except Exception as e:
    print(f"✗ OTP email FAILED: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIRECT SEND MAIL TEST")
print("=" * 80)

# Compare with direct send_mail
try:
    print(f"\nAttempting direct email...")
    result = send_mail(
        subject="Direct Test Email",
        message="This is a direct test email.",
        from_email='support@aafriride.com',
        recipient_list=[email],
        fail_silently=False,
    )
    print(f"✓ Direct email sent successfully (result: {result})")
except Exception as e:
    print(f"✗ Direct email FAILED: {e}")
