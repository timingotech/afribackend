#!/usr/bin/env python
"""Test the registration flow without actually registering"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from apps.users.tasks import send_email_task
import random

print("Testing email task...")
try:
    code = str(random.randint(100000, 999999))
    subject = "Your AAfri Ride Verification Code"
    message = f"Your AAfri Ride verification code is: {code}\n\nThis code is valid for 10 minutes."
    
    # Try to send via Celery
    result = send_email_task.delay('oyenugaridwan@gmail.com', subject, message)
    print(f"✅ Email task queued successfully!")
    print(f"Task ID: {result.id}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
