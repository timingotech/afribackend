"""
Celery tasks for background processing (SMS, emails, notifications)
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_otp_sms_task(self, phone: str, code: str):
    """
    Async task to send OTP via SMS
    
    Args:
        phone: Phone number
        code: OTP code
    """
    from .sms import send_otp_sms
    
    try:
        success = send_otp_sms(phone, code)
        if success:
            logger.info(f"OTP SMS sent to {phone}")
        else:
            logger.error(f"Failed to send OTP SMS to {phone}")
        return {"success": success, "phone": phone}
    except Exception as e:
        logger.error(f"Error in send_otp_sms_task: {e}")
        # Retry up to 3 times with exponential backoff
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_trip_notification_task(self, phone: str, trip_status: str, trip_details: str = ""):
    """
    Async task to send trip notification via SMS
    
    Args:
        phone: Phone number
        trip_status: Trip status (accepted, started, completed, etc)
        trip_details: Additional trip information
    """
    from .sms import send_trip_notification
    
    try:
        success = send_trip_notification(phone, trip_status, trip_details)
        if success:
            logger.info(f"Trip notification sent to {phone}: {trip_status}")
        else:
            logger.error(f"Failed to send trip notification to {phone}")
        return {"success": success, "phone": phone, "status": trip_status}
    except Exception as e:
        logger.error(f"Error in send_trip_notification_task: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3, time_limit=30)
def send_email_task(self, to_email: str, subject: str, message: str):
    """
    Async task to send email
    
    Args:
        to_email: Email address
        subject: Email subject
        message: Email body
    """
    from django.core.mail import send_mail
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='support@aafriride.com',
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info(f"Email sent to {to_email}")
        return {"success": True, "email": to_email}
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        # Retry up to 3 times with exponential backoff
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3, time_limit=30)
def send_otp_email_task(self, user_email: str, code: str, otp_id=None):
    """Send OTP email asynchronously via Celery"""
    try:
        from .email_utils import send_email_with_logging
        from uuid import uuid4
        msg_id = f"<{uuid4().hex}@aafriride.local>"
        result = send_email_with_logging(
            to_email=user_email,
            subject="Your AAfri Ride Verification Code",
            message=f"Your verification code is: {code}\n\nThis code is valid for 5 minutes.\n\nIf you didn't request this code, please ignore this email.",
            otp=otp_id,
            headers={'X-AAfriRide-Message-Id': msg_id, 'Message-ID': msg_id},
        )
        
        if result.get('success'):
            logger.info(f"OTP email sent successfully to {user_email}")
            return {'success': True, 'result': result.get('result')}
        else:
            logger.error(f"OTP email failed for {user_email}: {result.get('result')}")
            # Retry on failure
            raise Exception(f"Email send failed: {result.get('result')}")
            
    except Exception as exc:
        logger.exception(f"Error sending OTP email to {user_email}")
        # Retry with exponential backoff (60s, 120s, 180s)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
