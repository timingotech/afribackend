"""
Custom SMTP email backend for Zoho Mail with SSL certificate bypass
This is needed for Windows Python SSL certificate verification issues
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend


class ZohoEmailBackend(DjangoEmailBackend):
    """
    Custom SMTP backend for Zoho Mail that bypasses SSL verification
    """
    
    def open(self):
        """
        Initiate a TLS (encrypted) connection.
        """
        if self.connection is not None:
            return False

        try:
            if self.use_ssl:
                # Create SSL context that doesn't verify certificates
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                self.connection = smtplib.SMTP_SSL(
                    self.host, self.port,
                    timeout=self.timeout,
                    context=ssl_context
                )
            else:
                self.connection = smtplib.SMTP(
                    self.host, self.port,
                    timeout=self.timeout
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
        except smtplib.SMTPException as err:
            if not self.fail_silently:
                raise

