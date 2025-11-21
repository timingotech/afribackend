import ssl
from django.core.mail.backends.smtp import EmailBackend

class UnverifiedEmailBackend(EmailBackend):
    """
    Custom EmailBackend that disables SSL certificate verification.
    Useful for fixing [SSL: CERTIFICATE_VERIFY_FAILED] errors on some hosting providers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create an SSL context that ignores certificate verification
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
