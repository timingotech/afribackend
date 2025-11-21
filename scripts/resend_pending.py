"""
Resend pending OTP emails for given addresses.
Usage: edit `TARGET_EMAILS` below or pass via env var `TARGET_EMAILS` (comma-separated)
This script runs within Django context and uses `send_email_with_logging` to resend.
"""
import os
import django
import time
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend_project.settings')
django.setup()

from apps.users.models import OTP
from apps.users.email_utils import send_email_with_logging
from django.db.models import Q

TARGET_EMAILS = os.getenv('TARGET_EMAILS', 'oyenugaridwan@gmail.com,adebolaaaaa@gmail.com').split(',')
MAX_ATTEMPTS = 3

print('Target emails:', TARGET_EMAILS)

for email in TARGET_EMAILS:
    email = email.strip()
    if not email:
        continue
    print('\nChecking pending OTPs for', email)
    pending = OTP.objects.filter(email__iexact=email).filter(Q(send_result__isnull=True) | ~Q(send_result=1)).order_by('created_at')[:10]
    if not pending:
        print('  No pending OTPs found for', email)
        continue
    for otp in pending:
        print(f"  OTP id={otp.pk} code={otp.code} created_at={otp.created_at} send_result={otp.send_result}")
        attempt = 0
        while attempt < MAX_ATTEMPTS:
            attempt += 1
            print(f"    Attempt {attempt}/{MAX_ATTEMPTS} sending to {otp.email}...")
            try:
                res = send_email_with_logging(
                    to_email=otp.email,
                    subject='Your AAfri Ride Verification Code',
                    message=f'Your code is: {otp.code}\\n\\nValid for 5 minutes.',
                    otp=otp,
                )
                print('    send_email_with_logging returned:', res)
                if res.get('success'):
                    print('    Success — breaking')
                    break
                else:
                    print('    Failed result, retrying in 2s...')
            except Exception as e:
                print('    Exception during send:', repr(e))
            time.sleep(2)
        # Refresh from DB
        otp.refresh_from_db()
        print(f"  Final status: sent_at={otp.sent_at} send_result={otp.send_result} send_error={otp.send_error}")

print('\nDone.')
