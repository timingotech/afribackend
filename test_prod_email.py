import os
import django
import sys
import time

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_prod_email():
    recipient = 'oyenugaridwan@gmail.com'
    subject = 'Production Test Email from AAfri Ride'
    message = 'This is a test email sent from the Railway production environment using npx railway run.'
    
    print(f"Attempting to send email to {recipient}...")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    
    try:
        start_time = time.time()
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        elapsed = time.time() - start_time
        
        if result == 1:
            print(f"SUCCESS: Email sent to {recipient} in {elapsed:.2f}s")
        else:
            print(f"FAILURE: Email returned {result} (expected 1)")
            
    except Exception as e:
        print(f"ERROR: Failed to send email: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_prod_email()
