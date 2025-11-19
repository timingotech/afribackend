# Email/Phone Verification API Updates

## Overview
The registration system now supports both email and phone-based OTP verification. Users can choose their preferred verification method during registration.

## Registration Endpoint
**POST** `/api/users/register/`

### Request Body
```json
{
  "email": "user@example.com",
  "phone": "+234901234567",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "password2": "securepassword123",
  "role": "customer",
  "verification_method": "email"  // or "phone"
}
```

### Response (201 Created)
```json
{
  "id": 1,
  "email": "user@example.com",
  "phone": "+234901234567",
  "first_name": "John",
  "last_name": "Doe",
  "role": "customer",
  "is_active": true,
  "is_staff": false,
  "detail": "User registered successfully. Check your email for OTP verification code.",
  "verification_method": "email",
  "contact": "user@example.com",
  "otp_code": "123456"  // For testing only
}
```

## Generate OTP Endpoint
**POST** `/api/users/otp/generate/`

### For Email Verification
```json
{
  "method": "email",
  "email": "user@example.com"
}
```

### For Phone Verification
```json
{
  "method": "phone",
  "phone": "+234901234567"
}
```

### Response
```json
{
  "email": "user@example.com",  // or "phone" field for phone method
  "code": "123456",
  "method": "email",  // or "phone"
  "detail": "OTP sent to email"
}
```

## Verify OTP Endpoint
**POST** `/api/users/otp/verify/`

### For Email Verification
```json
{
  "method": "email",
  "email": "user@example.com",
  "code": "123456"
}
```

### For Phone Verification
```json
{
  "method": "phone",
  "phone": "+234901234567",
  "code": "123456"
}
```

### Response
```json
{
  "detail": "verified",
  "method": "email"
}
```

## Frontend Implementation Notes

1. **On Registration Page**: Add a radio button or select dropdown for users to choose "Email" or "Phone" verification
2. **Email Method**: Users receive OTP at their email address
3. **Phone Method**: Users receive OTP via SMS
4. **OTP Validity**: OTP codes expire after 10 minutes (300 seconds)
5. **Testing**: In development mode, the OTP code is returned in the registration response for testing

## Key Changes Made

- OTP model now has `email`, `method`, and `verified` fields
- `verification_method` parameter required during registration
- Generate OTP endpoint accepts `method` parameter
- Verify OTP endpoint accepts `method` parameter
- Email OTPs are sent via Zoho Mail SMTP
- Phone OTPs are sent via Twilio SMS
