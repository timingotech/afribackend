import os
import sys
import django
from django.conf import settings
from django.core.mail import send_mail, get_connection, EmailMessage

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_project.settings")
django.setup()

def debug_email():
    print("--- Email Configuration Debug ---")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_TIMEOUT: {getattr(settings, 'EMAIL_TIMEOUT', 'Not Set')}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    print("\n--- Attempting to send email ---")
    to_email = "oyenugaridwan@gmail.com"
    subject = "Debug Email Test from Railway"
    message = "This is a test email to verify configuration. If you receive this, the settings are correct."
    
    try:
        connection = get_connection()
        print(f"Connection class: {type(connection)}")
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            connection=connection
        )
        
        print(f"Sending to {to_email} from {settings.DEFAULT_FROM_EMAIL}...")
        result = email.send(fail_silently=False)
        print(f"Send result: {result}")
        
        if result == 1:
            print("SUCCESS: Email accepted by SMTP server.")
        else:
            print("FAILURE: Email not accepted (result != 1).")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_email()
