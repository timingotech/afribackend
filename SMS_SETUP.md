# SMS Setup Guide

## Overview

The AAfri Ride backend now supports SMS notifications for OTP codes and trip updates. The system supports both **Twilio** (production) and **Mock** (testing) providers.

## Quick Start (Development/Testing)

### Option 1: Mock SMS (No Setup Required) ✅

Perfect for development and testing. SMS messages are logged to console instead of actually sent.

**Current Configuration (Default):**
- `SMS_PROVIDER=mock` (in settings.py)
- When you request OTP, the code will appear in backend console logs
- No external services needed

**Example Log Output:**
```
[MOCK SMS] To: +1234567890 | Message: Your AAfri Ride verification code is: 123456. Valid for 10 minutes.
```

### Option 2: Twilio SMS (Production Setup)

For production, integrate Twilio to send real SMS messages.

#### Step 1: Create Twilio Account
1. Go to https://www.twilio.com
2. Sign up for a free account (includes $10 trial credits)
3. Get your credentials from Twilio Console:
   - Account SID
   - Auth Token
   - Phone Number (assigned to your account)

#### Step 2: Add Environment Variables

Create/update your `.env` file:

```dotenv
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

#### Step 3: Install Twilio Package

```bash
pip install twilio>=8.0
```

Or if already in requirements.txt:
```bash
pip install -r requirements.txt
```

#### Step 4: Test the Integration

```bash
python manage.py shell
```

```python
from apps.users.sms import send_otp_sms

# Test SMS
send_otp_sms('+1234567890', '123456')
# Should print: SMS sent to +1234567890 (SID: ...)
```

## Background Tasks (Celery) - Optional

For async SMS sending (doesn't block API requests), set up Celery:

### Step 1: Start Redis Server

```bash
# Windows (if using WSL or Docker)
redis-server

# Or via Docker
docker run -d -p 6379:6379 redis
```

### Step 2: Start Celery Worker

In a separate terminal:

```bash
cd backend
.venv\Scripts\activate.bat
celery -A backend_project worker -l info
```

### Step 3: Configure Celery (Already Done)

Your `settings.py` already has:
```python
CELERY_BROKER_URL = REDIS_URL
```

Now SMS will be sent asynchronously via Celery tasks instead of blocking the API.

## Current Implementation

### Files Created:

1. **`apps/users/sms.py`**
   - SMS provider abstraction
   - `TwilioSMSProvider` - Real SMS via Twilio
   - `MockSMSProvider` - Logs SMS for testing
   - `send_otp_sms()` - Send OTP messages
   - `send_trip_notification()` - Send trip updates

2. **`apps/users/tasks.py`**
   - Celery async tasks
   - `send_otp_sms_task` - Async OTP sending
   - `send_trip_notification_task` - Async trip notifications
   - `send_email_task` - Async email sending

3. **Modified `apps/users/views.py`**
   - `generate_otp()` now calls SMS service
   - Works with or without Celery
   - Falls back to sync SMS if Celery unavailable

### Configuration Added to `settings.py`:
```python
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'mock')
```

## How to Use

### API Endpoint: Generate OTP

**Request:**
```bash
POST /api/users/otp/generate/
Content-Type: application/json

{
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "phone": "+1234567890",
  "code": "123456",
  "detail": "OTP sent to phone"
}
```

**What Happens:**
1. Backend generates 6-digit OTP code
2. Stores in database (OTP model)
3. **With Celery**: Async task queued to send SMS
4. **Without Celery**: SMS sent synchronously
5. **Mock Mode**: Logs to console
6. **Twilio Mode**: Actually sends via SMS

## Testing in Admin Dashboard

1. Go to Admin Login page
2. In browser console, manually test OTP:

```javascript
// Trigger OTP generation
fetch('http://localhost:8000/api/users/otp/generate/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ phone: '+1234567890' })
})
.then(r => r.json())
.then(console.log)

// Then verify
fetch('http://localhost:8000/api/users/otp/verify/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    phone: '+1234567890',
    code: '123456'  // Use code from previous response or logs
  })
})
.then(r => r.json())
.then(console.log)
```

## Troubleshooting

### SMS Not Sending in Production

**Check:**
1. `SMS_PROVIDER` is set to `twilio` (not `mock`)
2. Twilio credentials are set correctly
3. Twilio account has credits/active subscription
4. Phone number format is correct (E.164: +1234567890)

**Test:**
```bash
python manage.py shell
```
```python
from django.conf import settings
print(f"Provider: {settings.SMS_PROVIDER}")
print(f"Account SID: {settings.TWILIO_ACCOUNT_SID}")
print(f"Phone: {settings.TWILIO_PHONE_NUMBER}")

from apps.users.sms import send_otp_sms
result = send_otp_sms('+1234567890', '123456')
print(f"Sent: {result}")
```

### Celery Tasks Not Running

**Check:**
1. Redis is running: `redis-cli ping` → should return `PONG`
2. Celery worker started: `celery -A backend_project worker -l info`
3. Check logs for errors

**Fallback:**
If Celery not available, SMS still sends synchronously. Check backend logs for SMS status.

## Future Enhancements

- [ ] SMS delivery tracking
- [ ] SMS templates and variables
- [ ] Multiple SMS providers (AWS SNS, Vonage, etc.)
- [ ] SMS rate limiting per user
- [ ] SMS cost tracking
- [ ] Support for WhatsApp/RCS
- [ ] Scheduled SMS campaigns

## Cost Estimation (Twilio)

- Free trial: $10 credit
- Per SMS: ~$0.0075-0.015 USD (varies by country)
- Incoming SMS: ~$0.0075 USD
- Monthly estimate for 10,000 OTPs: ~$75-150

## Resources

- Twilio Docs: https://www.twilio.com/docs
- Celery Docs: https://docs.celeryproject.org
- Redis Docs: https://redis.io/docs
