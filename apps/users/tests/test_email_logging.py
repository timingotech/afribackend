#!/usr/bin/env python
"""Quick test of send_email_with_logging in Django context"""

import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE','backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))+"/..\..\..")
from dotenv import load_dotenv
load_dotenv()
import django
django.setup()

from apps.users.email_utils import send_email_with_logging

print('Testing send_email_with_logging...')
res = send_email_with_logging('taonuga01@gmail.com','[TEST] email_utils','This is a test from email_utils')
print('Result:', res)
print('\nLog tail:\n')
print(open('logs/email_send.log','r',encoding='utf-8').read()[-1000:])
