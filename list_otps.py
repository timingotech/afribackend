#!/usr/bin/env python
"""List last OTPs for an email"""

import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()
import django
django.setup()
from apps.users.models import OTP

target = 'taonuga01@gmail.com'

otps = OTP.objects.filter(email=target).order_by('-created_at')[:20]
print(f"Found {otps.count()} OTP(s) for {target}\n")
for o in otps:
    print(f"code={o.code}  created_at={o.created_at.isoformat()}  verified={o.verified}")
