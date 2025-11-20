**Registration & Login API (Mobile) — AAfri Ride**

- **Purpose:** concise reference for mobile (iOS/Android) clients to integrate user registration, OTP verification, and JWT-based authentication.
- **Base URL (production example):** `https://afribackend-production-e293.up.railway.app`

**Common headers**
- `Content-Type: application/json`
- `Accept: application/json`
- Use HTTPS for all requests.

---

**1) Register (Create account + send OTP)**
- **Endpoint:** `POST /api/users/register/`
- **Description:** Creates a user and (depending on `verification_method`) generates an OTP and attempts to send it via email or SMS. Returns a 201 on success and include the `otp_code` in the response when enabled.
- **Request body (email flow):**
  ```json
  {
    "email": "user@example.com",
    "password": "YourPassword123!",
    "password2": "YourPassword123!",
    "first_name": "First",
    "last_name": "Last",
    "role": "customer",
    "verification_method": "email"
  }
  ```
- **Request body (phone flow):**
  ```json
  {
    "phone": "+1234567890",
    "password": "YourPassword123!",
    "password2": "YourPassword123!",
    "first_name": "First",
    "last_name": "Last",
    "role": "customer",
    "verification_method": "phone"
  }
  ```
- **Success response (201):**
  - JSON includes `detail`, `verification_method`, `contact`.

**Notes for mobile:**
- After 201, prompt user to check their email/SMS for the OTP.
- Do not assume immediate delivery — handle delays and allow the user to request a resend.

---

**2) Verify OTP**
- **Endpoint:** `POST /api/users/otp/verify/`
- **Description:** Validates the OTP code and marks the user as verified. After verification, the user can obtain tokens.
- **Request body (email):**
  ```json
  {
    "method": "email",
    "email": "user@example.com",
    "code": "123456"
  }
  ```
- **Request body (phone):**
  ```json
  {
    "method": "phone",
    "phone": "+1234567890",
    "code": "123456"
  }
  ```
- **Success response (200):**
  ```json
  {"detail": "verified", "method": "email"}
  ```
- **Failure cases:**
  - 400: missing fields, invalid code, or expired OTP.

**Mobile tips:**
- Show clear messages for expired/invalid codes and allow re-requesting an OTP.
- Disable repeated immediate resends to avoid rate-limits.

---

**3) Obtain JWT Tokens (Login)**
- **Endpoint:** (standard Simple JWT endpoints)
  - `POST /api/token/` — obtain access & refresh tokens
  - `POST /api/token/refresh/` — refresh access token using refresh token
- **Login flow notes:**
  - The server requires the account to be verified (non-staff users) before issuing tokens. If a user tries to log in without verification, the server returns 403 with a message asking them to verify first.
  - Use the verified `email` (or phone) and password to obtain tokens.
- **Example request:**
  ```json
  {
    "email": "user@example.com",
    "password": "YourPassword123!"
  }
  ```
- **Response (200):**
  ```json
  {
    "access": "<jwt-access-token>",
    "refresh": "<jwt-refresh-token>"
  }
  ```

**Client handling**
- Store the `access` token in secure storage (Keychain / EncryptedSharedPreferences).
- Store the `refresh` token securely as well.
- Add `Authorization: Bearer <access>` to protected requests.
- When `access` expires (401), call `/api/token/refresh/` with the `refresh` token.

---

**4) Resend / Generate OTP (direct)**
- **Endpoint:** `POST /api/users/otp/` (view: `generate_otp`)
- **Description:** Create an OTP for a given email or phone and queue/send it (the code currently uses a background task if available). Useful for explicit resend flows.
- **Request examples:**
  - Email:
    ```json
    {"method": "email", "email": "user@example.com"}
    ```
  - Phone:
    ```json
    {"method": "phone", "phone": "+1234567890"}
    ```

---

**5) Logout / Revoke**
- Implement client-side logout by clearing stored tokens.
- If you use server-side token blacklisting, call the relevant API (project contains `token_blacklist` app; follow its endpoints if enabled).

---

**6) Errors & troubleshooting**
- Common responses:
  - 400 Bad Request — missing/invalid fields, invalid OTP
  - 403 Forbidden — login blocked because account unverified
  - 500 Server Error — transient; report with request timestamp and payload
- If OTP emails are not received:
  - Ensure the address is correct.
  - Check spam/junk folders.

**8) Example mobile pseudo-code (fetch)**
- Register then verify (email) — simplified flow:
  ```js
  // 1) Register
  await fetch(BASE + '/api/users/register/', { method: 'POST', headers, body: JSON.stringify(regBody) })

  // 2) Prompt user for OTP & verify
  await fetch(BASE + '/api/users/otp/verify/', { method: 'POST', headers, body: JSON.stringify({ method: 'email', email, code }) })

  // 3) Obtain tokens
  const tokenRes = await fetch(BASE + '/api/token/', { method: 'POST', headers, body: JSON.stringify({ email, password }) })
  const { access, refresh } = await tokenRes.json()
  secureStore.set('access', access)
  secureStore.set('refresh', refresh)
  ```

---
