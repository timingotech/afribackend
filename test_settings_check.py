#!/usr/bin/env python
"""Check current Django settings and email backend configuration"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env file BEFORE Django setup
from dotenv import load_dotenv
load_dotenv()

django.setup()

from django.conf import settings

print("\n" + "="*70)
print("DJANGO EMAIL CONFIGURATION CHECK")
print("="*70)

print(f"\nDEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"DATABASE_URL env: {os.getenv('DATABASE_URL', 'NOT SET')[:50]}...")
print(f"EMAIL_BACKEND env: {os.getenv('EMAIL_BACKEND', 'NOT SET')}")
print(f"\nDjango Settings:")
print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"  EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Test the backend directly
print(f"\n{'='*70}")
print("TESTING EMAIL BACKEND")
print(f"{'='*70}")

from django.core.mail import get_connection
from django.core.mail import send_mail

backend_class = settings.EMAIL_BACKEND
print(f"\nBackend class path: {backend_class}")

try:
    connection = get_connection()
    print(f"Connection class: {connection.__class__.__module__}.{connection.__class__.__name__}")
    
    # Try to open connection
    if connection.open():
        print(f"✅ Connection opened successfully")
        connection.close()
    else:
        print(f"❌ Failed to open connection")
        
except Exception as e:
    print(f"❌ Error creating connection: {e}")

# Now test sending a test email
print(f"\n{'='*70}")
print("TESTING SEND_MAIL")
print(f"{'='*70}")

try:
    result = send_mail(
        subject="Test Email - Settings Check",
        message="This is a test email from settings check",
        from_email='support@aafriride.com',
        recipient_list=['test.settings.check@gmail.com'],
        fail_silently=False,
    )
    print(f"✅ send_mail() returned: {result}")
    
except Exception as e:
    print(f"❌ send_mail() failed: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*70}\n")
