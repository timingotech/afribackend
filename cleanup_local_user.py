#!/usr/bin/env python
"""Delete test user from local Django database (for local re-registration)."""
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

target_email = "taonuga01@gmail.com"
user = User.objects.filter(email=target_email).first()
if user:
    print(f"Deleting local user: {user.email} (ID: {user.id})")
    user.delete()
    print("Deleted local user.")
else:
    print("No existing local user found for deletion.")
