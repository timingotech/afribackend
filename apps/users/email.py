"""
Email service for sending OTP and notifications via Zoho Mail or mock provider
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_otp_email(email: str, otp_code: str) -> bool:
    """
    Send OTP via email
    
    Args:
        email: Recipient email address
        otp_code: OTP code (6 digits)
    
    Returns:
        True if sent successfully, False otherwise
    """
    subject = "Your AAfri Ride Verification Code"
    message = f"""
    Hello,
    
    Your AAfri Ride verification code is: {otp_code}
    
    This code is valid for 10 minutes. Do not share this code with anyone.
    
    If you didn't request this code, please ignore this email.
    
    Best regards,
    AAfri Ride Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"✅ OTP email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send OTP email to {email}: {e}")
        return False


def send_welcome_email(email: str, first_name: str = "") -> bool:
    """
    Send welcome email to new user
    
    Args:
        email: Recipient email address
        first_name: User's first name
    
    Returns:
        True if sent successfully, False otherwise
    """
    name = first_name if first_name else "Welcome"
    subject = "Welcome to AAfri Ride!"
    message = f"""
    Hello {name},
    
    Welcome to AAfri Ride! We're excited to have you on board.
    
    Get started by exploring our app and booking your first ride.
    
    If you have any questions, feel free to contact our support team.
    
    Best regards,
    AAfri Ride Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"✅ Welcome email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send welcome email to {email}: {e}")
        return False


def send_trip_email(email: str, trip_status: str, trip_details: str = "") -> bool:
    """
    Send trip notification via email
    
    Args:
        email: Recipient email address
        trip_status: Trip status (accepted, started, completed, etc)
        trip_details: Additional trip information
    
    Returns:
        True if sent successfully, False otherwise
    """
    subject = f"Trip {trip_status.title()}"
    message = f"Your AAfri Ride trip has been {trip_status}. {trip_details}"
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"✅ Trip email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send trip email to {email}: {e}")
        return False
