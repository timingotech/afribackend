"""
SMS service for sending OTP and notifications via Twilio or mock provider
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSProvider:
    """Base SMS provider class"""
    
    def send(self, phone: str, message: str) -> bool:
        raise NotImplementedError


class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider"""
    
    def __init__(self):
        try:
            from twilio.rest import Client
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            
            if not account_sid or not auth_token:
                logger.error("Twilio credentials not configured in settings")
                self.client = None
                return
            
            self.client = Client(account_sid, auth_token)
            self.from_number = settings.TWILIO_PHONE_NUMBER
            logger.info(f"Twilio initialized with account: {account_sid[:5]}...")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {e}")
            self.client = None
    
    def send(self, phone: str, message: str) -> bool:
        """Send SMS via Twilio"""
        if not self.client or not self.from_number:
            logger.error(f"Twilio not properly configured. Client: {self.client is not None}, From: {self.from_number}")
            return False
        
        try:
            logger.info(f"Attempting to send SMS to {phone} from {self.from_number}")
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone,
            )
            logger.info(f"✅ SMS sent successfully to {phone} (SID: {msg.sid})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send SMS to {phone}: {str(e)}")
            return False


class MockSMSProvider(SMSProvider):
    """Mock SMS provider for development/testing"""
    
    def send(self, phone: str, message: str) -> bool:
        """Log SMS instead of sending (for development)"""
        logger.info(f"[MOCK SMS] To: {phone} | Message: {message}")
        return True


def get_sms_provider() -> SMSProvider:
    """Get the configured SMS provider"""
    provider_name = settings.SMS_PROVIDER.lower()
    
    if provider_name == 'twilio':
        return TwilioSMSProvider()
    else:
        # Default to mock for development
        return MockSMSProvider()


def send_otp_sms(phone: str, code: str) -> bool:
    """
    Send OTP via SMS
    
    Args:
        phone: Phone number to send to
        code: OTP code (6 digits)
    
    Returns:
        True if sent successfully, False otherwise
    """
    message = f"Your AAfri Ride verification code is: {code}. Valid for 10 minutes."
    provider = get_sms_provider()
    return provider.send(phone, message)


def send_trip_notification(phone: str, trip_status: str, trip_details: str = "") -> bool:
    """
    Send trip notification via SMS
    
    Args:
        phone: Recipient phone number
        trip_status: Status (accepted, started, completed, etc)
        trip_details: Additional trip information
    
    Returns:
        True if sent successfully, False otherwise
    """
    message = f"Your AAfri Ride trip {trip_status}. {trip_details}"
    provider = get_sms_provider()
    return provider.send(phone, message)
