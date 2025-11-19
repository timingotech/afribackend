"""
Quick SMS test script to verify Twilio integration
Run: python test_sms.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.conf import settings
from apps.users.sms import send_otp_sms, get_sms_provider

print("=" * 60)
print("SMS CONFIGURATION TEST")
print("=" * 60)

# Check settings
print(f"\n1. SMS Provider: {settings.SMS_PROVIDER}")
print(f"2. Twilio Account SID: {settings.TWILIO_ACCOUNT_SID[:10]}...")
print(f"3. Twilio Auth Token: {settings.TWILIO_AUTH_TOKEN[:10]}...")
print(f"4. Twilio Phone Number: {settings.TWILIO_PHONE_NUMBER}")

# Test SMS sending
print("\n" + "=" * 60)
print("SENDING TEST SMS")
print("=" * 60)

test_phone = settings.TWILIO_PHONE_NUMBER
test_code = "123456"

print(f"\nSending SMS to: {test_phone}")
print(f"Test Code: {test_code}")
print(f"Message: Your AAfri Ride verification code is: {test_code}. Valid for 10 minutes.")

try:
    result = send_otp_sms(test_phone, test_code)
    print(f"\n✅ SMS Send Result: {result}")
    
    if result:
        print("\n✅ SMS SENT SUCCESSFULLY!")
        print("Check your phone for the SMS message.")
    else:
        print("\n❌ SMS sending failed. Check Twilio credentials.")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
