import smtplib
import socket
import ssl
import os
import sys
import time

# Add backend directory to path so we can setup django if needed, 
# but for this script we want to be as standalone as possible to test raw connectivity.

SMTP_HOST = os.environ.get('EMAIL_HOST', 'smtp.zoho.com')
SMTP_PORT = int(os.environ.get('EMAIL_PORT', 587))
SMTP_USER = os.environ.get('EMAIL_HOST_USER', 'support@aafriride.com')
SMTP_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

print(f"--- SMTP Connectivity Check ---")
print(f"Host: {SMTP_HOST}")
print(f"Port: {SMTP_PORT}")
print(f"User: {SMTP_USER}")
print(f"Password: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'NOT SET'}")
print(f"-----------------------------")

def check_dns():
    print(f"\n[1] Checking DNS resolution for {SMTP_HOST}...")
    try:
        ip = socket.gethostbyname(SMTP_HOST)
        print(f"    SUCCESS: Resolved to {ip}")
        return ip
    except Exception as e:
        print(f"    FAILURE: DNS resolution failed: {e}")
        return None

def check_socket(ip):
    print(f"\n[2] Checking TCP connection to {ip}:{SMTP_PORT}...")
    try:
        start_time = time.time()
        sock = socket.create_connection((ip, SMTP_PORT), timeout=10)
        elapsed = time.time() - start_time
        print(f"    SUCCESS: Connected in {elapsed:.2f}s")
        sock.close()
        return True
    except Exception as e:
        print(f"    FAILURE: TCP connection failed: {e}")
        return False

def check_smtp_handshake():
    print(f"\n[3] Checking SMTP Handshake & TLS...")
    try:
        print(f"    Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)
        server.set_debuglevel(1)
        
        print("    EHLO...")
        server.ehlo()
        
        if server.has_extn('STARTTLS'):
            print("    Starting TLS...")
            context = ssl.create_default_context()
            # Mimic the production backend settings that might be loose
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            server.starttls(context=context)
            print("    EHLO after TLS...")
            server.ehlo()
        else:
            print("    Server does not support STARTTLS")

        if SMTP_USER and SMTP_PASSWORD:
            print("    Attempting Login...")
            server.login(SMTP_USER, SMTP_PASSWORD)
            print("    SUCCESS: Login successful")
        
        server.quit()
        print("    SUCCESS: SMTP session completed")
        return True
    except Exception as e:
        print(f"    FAILURE: SMTP interaction failed: {e}")
        return False

if __name__ == "__main__":
    ip = check_dns()
    if ip:
        if check_socket(ip):
            check_smtp_handshake()
