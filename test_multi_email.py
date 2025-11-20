#!/usr/bin/env python
"""Test sending emails to multiple addresses"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

test_emails = [
    'adebolaaaaa@gmail.com',
    'oyenugaridwan@gmail.com',
    'taonuga01@gmail.com',
]

print("=" * 80)
print("TESTING EMAIL DELIVERY TO MULTIPLE ADDRESSES")
print("=" * 80)
print(f"\nTimestamp: {datetime.now()}")
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
print(f"SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print(f"Use TLS: {settings.EMAIL_USE_TLS}")

print("\n" + "=" * 80)
print("SENDING TEST EMAILS")
print("=" * 80)

results = {}

for email in test_emails:
    print(f"\n📧 Sending to: {email}")
    
    try:
        result = send_mail(
            subject=f"Test Email from AAfri Ride - {datetime.now().strftime('%H:%M:%S')}",
            message=f"""
Hello,

This is a test email from AAfri Ride backend to verify email delivery.

Test ID: {datetime.now().isoformat()}
Recipient: {email}

If you received this, please let us know!

Best regards,
AAfri Ride Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        
        results[email] = {
            'status': 'SUCCESS',
            'result': result,
            'timestamp': datetime.now()
        }
        print(f"   ✓ Sent successfully (result: {result})")
        
    except Exception as e:
        results[email] = {
            'status': 'FAILED',
            'error': str(e),
            'timestamp': datetime.now()
        }
        print(f"   ✗ Failed: {e}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

for email, result in results.items():
    status = result['status']
    symbol = "✓" if status == "SUCCESS" else "✗"
    print(f"{symbol} {email}: {status}")
    if status == "FAILED":
        print(f"    Error: {result['error']}")

print("\n" + "=" * 80)
print("INSTRUCTIONS")
print("=" * 80)
print("""
Please check your inbox (and spam/junk folder) for emails from: support@aafriride.com

Let me know:
1. Which emails received the test message
2. Which ones didn't
3. If they went to spam
4. How long it took to arrive

This will help diagnose the email delivery issue.
""")
