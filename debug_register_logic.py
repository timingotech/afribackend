import os
import django
import sys
import random
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.users.tasks import send_otp_email_task
from apps.users.models import OTP
from django.core.mail import send_mail
from django.conf import settings

def test_register_logic():
    recipient = 'oyenugaridwan@gmail.com'
    code = str(random.randint(100000, 999999))
    
    print(f"Simulating registration email logic for {recipient}...")
    
    # Create OTP
    otp = OTP.objects.create(email=recipient, code=code, method='email')
    print(f"Created OTP ID: {otp.id}")
    
    try:
        print("Attempting to queue via Celery...")
        send_otp_email_task.delay(recipient, code, otp.id)
        print(f"[OK] OTP email queued via Celery for {recipient}")
    except Exception as celery_error:
        print(f"[WARN] Celery unavailable ({celery_error}), sending email directly")
        try:
            send_mail(
                subject="Your AAfri Ride Verification Code (Fallback Test)",
                message=f"Your code is: {code}\n\nValid for 5 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            otp.sent_at = timezone.now()
            otp.send_result = 1
            otp.save(update_fields=['sent_at', 'send_result'])
            print(f"[OK] OTP email sent directly to {recipient}")
        except Exception as email_error:
            print(f"[ERROR] Direct email failed: {email_error}")
            otp.send_error = str(email_error)
            otp.save(update_fields=['send_error'])

if __name__ == '__main__':
    test_register_logic()
