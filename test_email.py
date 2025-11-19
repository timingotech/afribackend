"""
Test email sending with Zoho Mail
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail

print("=" * 60)
print("EMAIL TEST WITH ZOHO MAIL")
print("=" * 60)
print(f"\nEmail Host: {settings.EMAIL_HOST}")
print(f"Email Port: {settings.EMAIL_PORT}")
print(f"From Email: {settings.EMAIL_HOST_USER}")
print(f"Use TLS: {settings.EMAIL_USE_TLS}")

try:
    # Send test email
    send_mail(
        subject='Test Email from AAfri Ride',
        message='This is a test email from your AAfri Ride backend. If you received this, Zoho Mail is working!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['support@aafriride.com'],
        fail_silently=False,
    )
    print("\n✅ EMAIL SENT SUCCESSFULLY!")
    print("Check support@aafriride.com inbox for the test email.")
except Exception as e:
    print(f"\n❌ Email Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
