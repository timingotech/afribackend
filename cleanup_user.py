#!/usr/bin/env python
"""Delete existing test user and clean test"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Delete the test user
user = User.objects.filter(email="taonuga01@gmail.com").first()
if user:
    print(f"Deleting user: {user.email} (ID: {user.id})")
    user.delete()
    print("Deleted!")
else:
    print("No existing user found")
