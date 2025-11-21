"""
Custom SMTP email backend for Zoho Mail with SSL certificate bypass
This is needed for Windows Python SSL certificate verification issues
"""
import ssl
import smtplib
import socket
import time
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend


class ZohoEmailBackend(DjangoEmailBackend):
    """
    Custom SMTP backend for Zoho Mail that bypasses SSL verification
    """
    
    def open(self):
        """
        Initiate a TLS (encrypted) connection with shorter timeout and retry logic.
        """
        if self.connection is not None:
            return False

        # Try with shorter timeout and retry up to 2 times
        max_retries = 3
        timeout = 20  # Increased timeout for production latency
        
        for attempt in range(max_retries):
            try:
                if self.use_ssl:
                    # Create SSL context that doesn't verify certificates
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    self.connection = smtplib.SMTP_SSL(
                        self.host, self.port,
                        timeout=timeout,
                        context=ssl_context
                    )
                else:
                    self.connection = smtplib.SMTP(
                        self.host, self.port,
                        timeout=timeout
                    )
                    
                    if self.use_tls:
                        # Create SSL context that doesn't verify certificates for TLS
                        ssl_context = ssl.create_default_context()
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE
                        self.connection.starttls(context=ssl_context)
                
                if self.username and self.password:
                    self.connection.login(self.username, self.password)
                return True
                
            except (smtplib.SMTPException, socket.timeout, socket.error, OSError) as err:
                if attempt < max_retries - 1:
                    # Wait briefly before retry
                    time.sleep(0.5)
                    continue
                else:
                    # Final attempt failed
                    if not self.fail_silently:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Failed to connect to SMTP server after {max_retries} attempts: {err}")
                    return False
        
        return False

