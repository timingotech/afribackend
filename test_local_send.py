import os
import sys
import traceback

# Ensure Django settings are configured
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')

try:
    import django
    django.setup()

    from django.contrib.auth import get_user_model
    from apps.users.email_utils import send_email_with_logging
    from apps.users.models import OTP

    User = get_user_model()

    # Create or reset a test user and OTP
    TEST_EMAIL = 'test.delivery@example.com'
    print('Removing any existing test user and OTPs...')
    try:
        User.objects.filter(email=TEST_EMAIL).delete()
    except Exception:
        pass

    print('Creating test user...')
    u = User.objects.create_user(email=TEST_EMAIL, password='pass1234')
    print('Creating OTP...')
    otp = OTP.objects.create(user=u, email=u.email, code='123456', method='email')

    print('Sending email via send_email_with_logging...')
    res = send_email_with_logging(to_email=u.email, subject='Test Delivery', message='Code 123456', otp=otp)
    print('send result:', res)

    otp.refresh_from_db()
    print('OTP sent_at:', otp.sent_at)
    print('OTP send_result:', otp.send_result)
    print('OTP send_error:', otp.send_error)

except Exception:
    traceback.print_exc()
    sys.exit(1)

print('Test script finished')
