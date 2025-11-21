AAfri Ride Backend — Local Email OTP Debugging

Purpose
-------
This file explains how to debug OTP email sending during registration. If registration queues a Celery task but no email arrives, follow these steps to reproduce and diagnose the problem.

Prerequisites
-------------
- Python and pip in your environment
- Virtualenv for Python (recommended)
- Local DB setup (run `python manage.py migrate`)
- Optional: Redis + Celery if you want async tasks

Steps to reproduce/fix locally
------------------------------
1. Activate the virtualenv and install dependencies

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Set SMTP environment variables (if you want real email delivery). Use your real SMTP provider or Gmail (recommended for test mailbox). If testing with SMTP provider, fill in the values below:

```powershell
$env:EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
$env:EMAIL_HOST='smtp.example.com'
$env:EMAIL_PORT='587'
$env:EMAIL_USE_TLS='True'
$env:EMAIL_HOST_USER='smtp-user@example.com'
$env:EMAIL_HOST_PASSWORD='your-password'
$env:DEFAULT_FROM_EMAIL='webmaster@example.com'
```

If you just want to test and don't need real email delivery, you can leave `EMAIL_BACKEND` as the default `console.EmailBackend` (it logs to console only).

3. Set `CELERY_TASK_ALWAYS_EAGER=True` to force Celery to execute tasks synchronously in the same process for debugging. This avoids needing to run a separate Celery worker:

```powershell
$env:CELERY_TASK_ALWAYS_EAGER = 'True'
$env:CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS = 'True'
```

4. Run Django migrations and create a simple superuser if needed

```powershell
python manage.py migrate
python manage.py createsuperuser
```

5. Run the `tools/debug_register_email_send.py` script with the target email (e.g., your test address)

```powershell
# Using the user's test email
python tools/debug_register_email_send.py --email oyenugaridwan@gmail.com
```

This will:
- Force Celery tasks to execute eagerly
- Register a user via the internal Django test client (no dev server required)
- Print the response and OTP DB info
- Print the tail of `logs/email_send.log` if present

6. If you still don't receive the email:
- Verify `logs/email_send.log` contains a `RESULT=...` entry
- Check OTP DB object for `send_result` and `send_error`
- If using SMTP, check provider logs and ensure credentials and TLS settings are correct

Start Celery + Redis for real async flow
---------------------------------------
If you prefer the true async flow, start Redis and a Celery worker:

```powershell
# On Windows we'll usually use Docker for redis or WSL
docker run -d -p 6379:6379 redis
# In a new terminal with venv activated
cd backend
celery -A backend_project worker -l info
# In another terminal, start Django server
python manage.py runserver
```

Then use the registration endpoint (via curl or Postman) to register a user with `verification_method: 'email'` and observe the logs. The Celery worker will process the task and call the email send task.

Notes / Tips
------------
- If Celery is installed but no worker is running, .delay() returns a queued AsyncResult that won't be executed.
- In DEBUG mode we added a fallback: if Celery remains pending for ~0.75s it will attempt direct send to help local debugging. This will log a fallback message and attempt a direct send.
- For production deploys, ensure you have Redis and Celery worker running and proper SMTP credentials.

If you want me to carry out a remote run:
- Make sure the repo is set up locally and SMTP env vars are set; run the `tools/debug_register_email_send.py` script above and share the console output. Then tell me whether you received the email at `oyenugaridwan@gmail.com`.

Alternatively, I'll be happy to help you run these steps and inspect logs step-by-step.