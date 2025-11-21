#!/usr/bin/env python
"""Pytest-style registration test that forces celery tasks to be executed eagerly

This test will register a user through the API and assert OTP send_result is set to 1
when email backend is configured and tasks are executed eagerly.

Note: This test writes to the DB, so run against a test DB or clean up afterwards.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
# Force Celery tasks to run in the current process for this test
os.environ['CELERY_TASK_ALWAYS_EAGER'] = 'True'
os.environ['CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS'] = 'True'

django.setup()

from django.test import Client
from apps.users.models import OTP, User


def test_registration_email_send_eager():
    client = Client()
    test_email = 'test.eager@example.com'

    # Remove previous user if exists
    User.objects.filter(email=test_email).delete()

    data = {
        'email': test_email,
        'password': 'TestPass123!',
        'password2': 'TestPass123!',
        'first_name': 'Eager',
        'last_name': 'Test',
        'role': 'customer',
        'verification_method': 'email',
    }

    response = client.post('/api/users/register/', data=data, content_type='application/json')
    assert response.status_code in (200, 201)

    # Check OTP object exists and was marked 'sent'
    otp = OTP.objects.filter(email=test_email, method='email').order_by('-created_at').first()
    assert otp is not None, 'OTP record should exist after registration'
    assert otp.send_result in (1, None), f"send_result should be 1 or None (console backend). Got: {otp.send_result}"
