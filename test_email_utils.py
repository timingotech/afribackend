"""
Test send_email_with_logging function directly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.users.email_utils import send_email_with_logging
from apps.users.models import OTP, User

print("=" * 60)
print("TESTING send_email_with_logging FUNCTION")
print("=" * 60)

# Get a test user or create one
user = User.objects.filter(email__icontains='test').first()
if not user:
    print("No test user found, testing without OTP tracking")
    user = None

print(f"\nSending test email to: oyenugaridwan@gmail.com")

# Create OTP record if we have a user
otp = None
code = "888888"
if user:
    otp = OTP.objects.create(user=user, email='oyenugaridwan@gmail.com', code=code, method='email')
    print(f"Created OTP record: {otp.id}")

# Test the function
result = send_email_with_logging(
    to_email='oyenugaridwan@gmail.com',
    subject='Test from send_email_with_logging',
    message=f'Your test OTP code is: {code}\n\nThis tests the send_email_with_logging function.',
    otp=otp
)

print(f"\n✅ Result: {result}")

if result.get('success'):
    print("✅ EMAIL SENT SUCCESSFULLY via send_email_with_logging!")
    print("Check oyenugaridwan@gmail.com inbox")
    if otp:
        otp.refresh_from_db()
        print(f"OTP sent_at: {otp.sent_at}")
        print(f"OTP send_result: {otp.send_result}")
        print(f"OTP send_error: {otp.send_error}")
else:
    print(f"❌ EMAIL FAILED: {result.get('result')}")

print("=" * 60)
