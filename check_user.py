#!/usr/bin/env python
"""Check if user exists and show OTP"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import OTP

User = get_user_model()

user = User.objects.filter(email="taonuga01@gmail.com").first()

if user:
    print(f"\nUser exists: {user.email} (ID: {user.id})")
    print(f"Created: {user.date_joined}")
    
    otp = OTP.objects.filter(user=user).first()
    if otp:
        print(f"\nOTP exists: {otp.code}")
        print(f"Email: {otp.email}")
        print(f"Method: {otp.method}")
        print(f"Created: {otp.created_at}")
    else:
        print("\nNO OTP FOUND for this user")
else:
    print("User does not exist")
