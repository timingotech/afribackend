import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_sending():
    recipient = 'oyenugaridwan@gmail.com'
    subject = 'Test Email from AAfri Ride Debugger'
    message = 'This is a test email to verify the email configuration is working correctly.'
    
    print(f"Attempting to send email to {recipient}...")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    
    try:
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        
        if result == 1:
            print(f"SUCCESS: Email sent to {recipient}")
        else:
            print(f"FAILURE: Email returned {result} (expected 1)")
            
    except Exception as e:
        print(f"ERROR: Failed to send email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_email_sending()
