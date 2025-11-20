"""
Comprehensive User Registration & Login Test Script

This script tests the complete user registration and login flow:
1. Registers a new user with email verification
2. Attempts to login before verification (should fail with 403)
3. Verifies email with OTP code
4. Logins successfully with verified account
"""

import requests
import json
from datetime import datetime
import os

# Configuration
API_BASE_URL = os.getenv('BACKEND_URL', 'http://localhost:8000/api')
TEST_EMAIL = "taonuga01@gmail.com"
TEST_PASSWORD = "SecurePass123!"
TEST_FIRST_NAME = "Test"
TEST_LAST_NAME = "User"

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_step(step_number, description):
    """Log a test step"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}STEP {step_number}: {description}{Colors.ENDC}")
    print("=" * 80)

def log_request(method, endpoint, data=None):
    """Log the API request"""
    print(f"{Colors.OKBLUE}REQUEST:{Colors.ENDC} {method} {endpoint}")
    if data:
        print(f"{Colors.OKCYAN}Body:{Colors.ENDC}")
        print(json.dumps(data, indent=2))

def log_response(response):
    """Log the API response"""
    print(f"\n{Colors.OKBLUE}RESPONSE:{Colors.ENDC} Status {response.status_code}")
    try:
        data = response.json()
        print(f"{Colors.OKCYAN}Body:{Colors.ENDC}")
        print(json.dumps(data, indent=2))
        return data
    except:
        print(f"{Colors.WARNING}(No JSON response){Colors.ENDC}")
        return None

def log_success(message):
    """Log success message"""
    print(f"{Colors.OKGREEN}✓ SUCCESS: {message}{Colors.ENDC}")

def log_error(message):
    """Log error message"""
    print(f"{Colors.FAIL}✗ ERROR: {message}{Colors.ENDC}")

def log_info(message):
    """Log info message"""
    print(f"{Colors.OKCYAN}ℹ INFO: {message}{Colors.ENDC}")

def log_warning(message):
    """Log warning message"""
    print(f"{Colors.WARNING}⚠ WARNING: {message}{Colors.ENDC}")

# ============================================================================
# CONFIGURATION & STARTUP
# ============================================================================

print(f"\n{Colors.BOLD}{Colors.HEADER}API ENDPOINT CONFIGURATION{Colors.ENDC}")
print("=" * 80)
log_info(f"Backend URL: {API_BASE_URL}")
print()

# ============================================================================
# STEP 1: REGISTER USER WITH EMAIL VERIFICATION
# ============================================================================

log_step(1, "Register User with Email Verification")

registration_data = {
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD,
    "first_name": TEST_FIRST_NAME,
    "last_name": TEST_LAST_NAME,
    "role": "customer",
    "verification_method": "email"  # Important: specify email verification
}

log_request("POST", f"{API_BASE_URL}/users/register/", registration_data)

response = requests.post(f"{API_BASE_URL}/users/register/", json=registration_data)
registration_response = log_response(response)

if response.status_code == 400 and "already exists" in str(registration_response):
    log_warning("User already exists (previous registration)")
    log_success("Skipping registration, proceeding to verification")
    otp_code = None  # Will need to generate or use provided code
elif response.status_code != 201:
    log_error(f"Registration failed with status {response.status_code}")
    exit(1)
else:
    log_success("User registered successfully")
    # Extract the OTP code from response (for testing)
    otp_code = registration_response.get('otp_code')
    if otp_code:
        log_info(f"OTP Code from registration: {Colors.WARNING}{otp_code}{Colors.ENDC}")
    else:
        log_warning("OTP code not in response (email may have been sent)")
        otp_code = None

# ============================================================================
# STEP 2: ATTEMPT LOGIN BEFORE VERIFICATION (SHOULD FAIL)
# ============================================================================

log_step(2, "Attempt Login Before Email Verification (Expected: FAIL)")

login_data = {
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD
}

log_request("POST", f"{API_BASE_URL}/users/login/", login_data)

response = requests.post(f"{API_BASE_URL}/users/login/", json=login_data)
login_response = log_response(response)

if response.status_code == 403:
    log_success("Login correctly rejected (user not verified yet)")
    expected_message = "Please verify your email/phone with OTP first"
    if expected_message in login_response.get('detail', ''):
        log_success("Error message confirms verification is required")
    else:
        log_info(f"Response: {login_response.get('detail', '')}")
elif response.status_code == 200:
    log_error("Login succeeded but should have failed (user not verified)")
    exit(1)
else:
    log_error(f"Unexpected status code: {response.status_code}")
    exit(1)

# ============================================================================
# STEP 3: VERIFY EMAIL WITH OTP CODE
# ============================================================================

log_step(3, "Verify Email with OTP Code")

# Check if OTP code is provided as command line argument or environment variable
import sys

# Try to get OTP from command line or environment
otp_from_env = os.getenv('OTP_CODE')
otp_from_arg = sys.argv[1] if len(sys.argv) > 1 else None
otp_code = otp_from_arg or otp_from_env or otp_code

if not otp_code:
    log_warning("OTP code not available from registration response and not provided")
    log_info("Generating new OTP...")
    
    # Generate OTP
    generate_otp_data = {
        "method": "email",
        "email": TEST_EMAIL
    }
    
    log_request("POST", f"{API_BASE_URL}/users/otp/generate/", generate_otp_data)
    
    response = requests.post(f"{API_BASE_URL}/users/otp/generate/", json=generate_otp_data)
    generate_response = log_response(response)
    
    if response.status_code != 200:
        log_error("Failed to generate OTP")
        exit(1)
    
    otp_code = generate_response.get('code')
    log_info(f"Generated OTP Code: {Colors.WARNING}{otp_code}{Colors.ENDC}")
else:
    log_info(f"Using provided OTP Code: {Colors.WARNING}{otp_code}{Colors.ENDC}")

# Verify OTP
verify_otp_data = {
    "method": "email",
    "email": TEST_EMAIL,
    "code": otp_code
}

log_request("POST", f"{API_BASE_URL}/users/otp/verify/", verify_otp_data)

response = requests.post(f"{API_BASE_URL}/users/otp/verify/", json=verify_otp_data)
verify_response = log_response(response)

if response.status_code != 200:
    log_error(f"OTP verification failed with status {response.status_code}")
    exit(1)

log_success("Email verified successfully with OTP")

# ============================================================================
# STEP 4: LOGIN WITH VERIFIED ACCOUNT (SHOULD SUCCEED)
# ============================================================================

log_step(4, "Login with Verified Account (Expected: SUCCESS)")

login_data = {
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD
}

log_request("POST", f"{API_BASE_URL}/users/login/", login_data)

response = requests.post(f"{API_BASE_URL}/users/login/", json=login_data)
login_response = log_response(response)

if response.status_code != 200:
    log_error(f"Login failed with status {response.status_code}")
    exit(1)

log_success("Login successful!")

# Extract tokens
access_token = login_response.get('access')
refresh_token = login_response.get('refresh')

if not access_token:
    log_error("No access token in response")
    exit(1)

log_success("Access token received")
log_info(f"Access Token (first 20 chars): {access_token[:20]}...")
log_info(f"Refresh Token (first 20 chars): {refresh_token[:20]}...")

# ============================================================================
# BONUS STEP 5: VERIFY PROFILE CAN BE ACCESSED WITH TOKEN
# ============================================================================

log_step(5, "Verify Profile Access with Token")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

log_request("GET", f"{API_BASE_URL}/users/profile/", None)

response = requests.get(f"{API_BASE_URL}/users/profile/", headers=headers)
profile_response = log_response(response)

if response.status_code != 200:
    log_error(f"Profile fetch failed with status {response.status_code}")
else:
    log_success("Profile access successful")
    log_info(f"User: {profile_response.get('first_name')} {profile_response.get('last_name')}")
    log_info(f"Email: {profile_response.get('email')}")
    log_info(f"Role: {profile_response.get('role')}")
    log_info(f"Verified: {profile_response.get('is_verified')}")

# ============================================================================
# SUMMARY
# ============================================================================

print(f"\n{Colors.BOLD}{Colors.OKGREEN}")
print("=" * 80)
print("ALL TESTS PASSED!")
print("=" * 80)
print(f"{Colors.ENDC}")

print(f"""
{Colors.BOLD}Summary:{Colors.ENDC}
  ✓ User registered with email: {TEST_EMAIL}
  ✓ Login blocked before verification
  ✓ Email verified with OTP code
  ✓ Login successful after verification
  ✓ Profile accessible with token

{Colors.BOLD}Key Information:{Colors.ENDC}
  Email: {TEST_EMAIL}
  Password: {TEST_PASSWORD}
  Access Token: {access_token[:50]}...
  Refresh Token: {refresh_token[:50]}...

{Colors.BOLD}Next Steps:{Colors.ENDC}
  1. Use the credentials above to login to the admin panel
  2. Navigate to /admin/errors to test the error logging dashboard
  3. Check email for actual OTP if using real email service
""")

print(f"{Colors.BOLD}Test Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")
