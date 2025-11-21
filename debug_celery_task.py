import os
import django
import sys
import time

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.users.tasks import send_otp_email_task
from apps.users.models import OTP
from django.conf import settings
# from backend_project.celery import app

def test_celery_task():
    print(f"DEBUG: {settings.DEBUG}")
    print(f"CELERY_TASK_ALWAYS_EAGER (settings): {getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)}")
    # print(f"app.conf.task_always_eager: {app.conf.task_always_eager}")
    recipient = 'oyenugaridwan@gmail.com'
    code = '123456'
    
    print(f"Attempting to queue Celery task for {recipient}...")
    
    try:
        # Create a dummy OTP to track
        # We need a user or just email. The task takes otp_id.
        # Let's create an OTP object first.
        otp = OTP.objects.create(email=recipient, code=code, method='email')
        print(f"Created OTP ID: {otp.id}")
        
        # Call delay()
        result = send_otp_email_task.delay(recipient, code, otp.id)
        print(f"Task queued. Task ID: {result.id}")
        print(f"Task status: {result.status}")
        
        # Wait a bit to see if it changes (it won't if no worker)
        print("Waiting 5 seconds...")
        time.sleep(5)
        print(f"Task status after 5s: {result.status}")
        
        # Check if OTP was updated (send_result should be 1 if successful)
        otp.refresh_from_db()
        print(f"OTP send_result: {otp.send_result}")
        print(f"OTP send_error: {otp.send_error}")
        
        if otp.send_result == 1:
            print("SUCCESS: OTP marked as sent in DB.")
        else:
            print("FAILURE: OTP NOT marked as sent in DB. (Likely no Celery worker running)")

    except Exception as e:
        print(f"ERROR: Failed to queue task: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_celery_task()
