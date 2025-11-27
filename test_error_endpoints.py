#!/usr/bin/env python
"""Quick test of error logging endpoints"""
import requests
import json

BASE_URL = "http://localhost:8001/api"

print("Testing Error Logging Endpoints\n")

# Test 1: Log a frontend error (public endpoint)
print("1. Testing POST /api/errors/errors/log/ (PUBLIC)")
print("-" * 60)

error_data = {
    "error_type": "network",
    "title": "Test Frontend Error",
    "message": "This is a test error from the frontend",
    "severity": "high"
}

response = requests.post(f"{BASE_URL}/errors/errors/log/", json=error_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Test 2: Get recent errors (admin endpoint - needs token)
print("\n2. Testing GET /api/errors/errors/recent/ (ADMIN ONLY)")
print("-" * 60)

# Without token
response = requests.get(f"{BASE_URL}/errors/errors/recent/?limit=10&hours=24")
print(f"Status (no token): {response.status_code}")
print(f"Response: {response.text[:200]}")

print("\nNote: Admin endpoints require authentication token.")
print("Run the comprehensive auth flow test to get a token first.")
