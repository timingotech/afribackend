#!/usr/bin/env python
"""Simple SMTP connectivity checker.

Usage: run this on the environment you want to test (local or production).
It will attempt a TCP connect to the SMTP host:port, then try an SMTP EHLO/STARTTLS.

Set the environment variables SMTP_HOST and SMTP_PORT or edit the defaults below.
"""
import os
import socket
import smtplib
import sys

SMTP_HOST = os.getenv('EMAIL_HOST', 'smtp.zoho.com')
SMTP_PORT = int(os.getenv('EMAIL_PORT', '587'))
TIMEOUT = 10

print(f"Testing SMTP connectivity to {SMTP_HOST}:{SMTP_PORT} (timeout={TIMEOUT}s)")

# TCP connect test
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(TIMEOUT)
try:
    s.connect((SMTP_HOST, SMTP_PORT))
    print(f"TCP connect: SUCCESS to {SMTP_HOST}:{SMTP_PORT}")
    s.close()
except Exception as e:
    print(f"TCP connect: FAILED -> {e}")
    sys.exit(2)

# SMTP handshake
try:
    server = smtplib.SMTP(host=SMTP_HOST, port=SMTP_PORT, timeout=TIMEOUT)
    server.set_debuglevel(1)
    code, msg = server.ehlo()
    print(f"EHLO returned: {code} {msg}")
    if server.has_extn('starttls'):
        print("Server supports STARTTLS — trying STARTTLS()")
        server.starttls()
        code, msg = server.ehlo()
        print(f"EHLO after STARTTLS returned: {code} {msg}")
    else:
        print("Server does not advertise STARTTLS")
    # Do not attempt login here; only handshake
    server.quit()
    print("SMTP handshake completed successfully.")
    sys.exit(0)
except Exception as e:
    print(f"SMTP handshake FAILED -> {type(e).__name__}: {e}")
    sys.exit(3)
