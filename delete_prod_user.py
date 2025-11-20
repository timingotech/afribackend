#!/usr/bin/env python
"""Delete user from production database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Delete the test user if it exists
user = User.objects.filter(email='oyenugaridwan@gmail.com').first()
if user:
    print(f"Deleting user: {user.email}")
    user.delete()
    print("User deleted from production database successfully")
else:
    print("User not found in production database")
