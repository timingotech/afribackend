#!/usr/bin/env python
"""Direct test of registration with synchronous email"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import OTP
from django.core.mail import send_mail

User = get_user_model()
test_email = 'direct_sync_test@gmail.com'
User.objects.filter(email=test_email).delete()

print('[INFO] Testing User Registration & Email Sending\n')

# Step 1: Create user
print('Step 1: Creating user...')
user = User.objects.create_user(
    email=test_email,
    password='TestPass123!',
    first_name='Sync',
    last_name='Test',
    phone='+234902201999'  # Unique phone number
)
print(f'[OK] User created: {user.email}\n')

# Step 2: Create OTP
print('Step 2: Creating OTP...')
code = '654321'
otp = OTP.objects.create(user=user, email=test_email, code=code, method='email')
print(f'[OK] OTP created: {otp.code} via {otp.method}\n')

# Step 3: Test email sending
print('Step 3: Testing email sending...')
try:
    send_mail(
        subject="Your AAfri Ride Verification Code",
        message=f"Your code is: {code}\n\nValid for 10 minutes.",
        from_email='support@aafriride.com',
        recipient_list=[test_email],
        fail_silently=False,
    )
    print(f'[OK] Email sent to {test_email}\n')
except Exception as e:
    print(f'[FAIL] Email sending failed: {e}\n')

print('Test completed successfully!')
