import logging
from django.core.mail import get_connection, EmailMessage
import requests
import os
import json

logger = logging.getLogger(__name__)

LOG_PATH = 'logs/email_send.log'

def _ensure_log_dir():
    import os
    d = os.path.dirname(LOG_PATH)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def send_email_with_logging(to_email: str, subject: str, message: str, from_email: str = 'support@aafriride.com', otp=None):
    """Send an email using Django email backend and log the attempt to a file.

    If `otp` is provided (either an `OTP` instance or an OTP id), this function
    will attempt to persist `sent_at`, `send_result` and `send_error` to the DB
    for that OTP record.

    Returns a dict: {"success": bool, "result": int_or_error}
    """
    _ensure_log_dir()
    timestamp = None
    try:
        from django.utils import timezone
        timestamp = timezone.now().isoformat()
    except Exception:
        import datetime
        timestamp = datetime.datetime.utcnow().isoformat()

    log_line = f"{timestamp} | TO={to_email} | SUBJECT={subject} | "
    
    # Try sending (no retries to prevent Gunicorn timeout)
    last_error = None
    try:
        # Check if we should use EmailJS (via environment variable)
        import os
        import requests
        
        emailjs_service_id = os.getenv('EMAILJS_SERVICE_ID')
        emailjs_template_id = os.getenv('EMAILJS_TEMPLATE_ID')
        # Historically some environments use EMAILJS_USER_ID while others use
        # EMAILJS_PUBLIC_KEY for the public key; accept either for compatibility.
        emailjs_user_id = os.getenv('EMAILJS_USER_ID') or os.getenv('EMAILJS_PUBLIC_KEY')
        emailjs_private_key = os.getenv('EMAILJS_PRIVATE_KEY') # Private Key
        
        if emailjs_service_id and emailjs_template_id and emailjs_user_id:
            # Use EmailJS API
            logger.info(f"Sending email via EmailJS to {to_email}")
            
            payload = {
                "service_id": emailjs_service_id,
                "template_id": emailjs_template_id,
                "user_id": emailjs_user_id,
                "accessToken": emailjs_private_key,
                "template_params": {
                    "to_email": to_email,
                    "subject": subject,
                    "message": message,
                    "otp_code": message.split("is: ")[1].split("\n")[0] if "is: " in message else "" # Extract OTP if possible
                }
            }
            
            response = requests.post(
                "https://api.emailjs.com/api/v1.0/email/send",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = 1
                logger.info(f"EmailJS sent successfully to {to_email}")
            else:
                raise Exception(f"EmailJS failed: {response.text}")
                
        else:
            # Fallback to standard Django SMTP
            connection = get_connection()
            email = EmailMessage(subject=subject, body=message, from_email=from_email, to=[to_email], connection=connection)
            result = email.send(fail_silently=False)
            
        log_line += f"RESULT={result}\n"
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_line)
        logger.info(f"Email sent to {to_email} (result={result})")

        # Persist send result to DB if otp provided
        if otp is not None:
            try:
                from django.utils import timezone as _tz
                # Accept either OTP instance or numeric id
                if hasattr(otp, 'save') and hasattr(otp, 'pk'):
                    otp.sent_at = _tz.now()
                    otp.send_result = int(result) if isinstance(result, int) else 1
                    otp.send_error = ''
                    otp.save(update_fields=['sent_at', 'send_result', 'send_error'])
                else:
                    from .models import OTP as _OTP
                    o = _OTP.objects.filter(pk=otp).first()
                    if o:
                        o.sent_at = _tz.now()
                        o.send_result = int(result) if isinstance(result, int) else 1
                        o.send_error = ''
                        o.save(update_fields=['sent_at', 'send_result', 'send_error'])
            except Exception:
                logger.exception('Failed to persist OTP send result to DB')

        return {"success": True, "result": result}
        
    except Exception as e:
        last_error = e
        logger.warning(f"Email attempt failed for {to_email}: {e}")
    
    # Attempt failed
    if last_error:
        log_line += f"ERROR={last_error} (all attempts failed)\n"
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_line)
        logger.error(f"Failed to send email to {to_email} after 2 attempts: {last_error}", exc_info=True)
        # Persist failure to DB if otp provided
        if otp is not None:
            try:
                from django.utils import timezone as _tz
                if hasattr(otp, 'save') and hasattr(otp, 'pk'):
                    otp.sent_at = _tz.now()
                    otp.send_result = 0
                    otp.send_error = str(last_error)
                    otp.save(update_fields=['sent_at', 'send_result', 'send_error'])
                else:
                    from .models import OTP as _OTP
                    o = _OTP.objects.filter(pk=otp).first()
                    if o:
                        o.sent_at = _tz.now()
                        o.send_result = 0
                        o.send_error = str(last_error)
                        o.save(update_fields=['sent_at', 'send_result', 'send_error'])
            except Exception:
                logger.exception('Failed to persist OTP send failure to DB')

        return {"success": False, "result": str(last_error)}

def send_email_via_emailjs(to_email, subject, message, otp=None, code=None):
    """
    Send email using EmailJS REST API
    """
    service_id = os.getenv('EMAILJS_SERVICE_ID')
    template_id = os.getenv('EMAILJS_TEMPLATE_ID')
    user_id = os.getenv('EMAILJS_PUBLIC_KEY')
    private_key = os.getenv('EMAILJS_PRIVATE_KEY')

    if not all([service_id, template_id, user_id, private_key]):
        logger.error("EmailJS configuration missing. Check environment variables.")
        return {"success": False, "result": "Missing EmailJS configuration"}

    url = "https://api.emailjs.com/api/v1.0/email/send"
    
    from django.utils import timezone
    import datetime
    
    # Prepare the data payload
    payload = {
        "service_id": service_id,
        "template_id": template_id,
        "user_id": user_id,
        "accessToken": private_key,
        "template_params": {
            "to_email": to_email,
            "subject": subject,
            "message": message,
            "passcode": code if code else (message.split("is: ")[1].split("\n")[0] if "is: " in message else ""),
            "time": "5 Minutes"
        }
    }

    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200 or response.text == 'OK':
            logger.info(f"EmailJS sent to {to_email}")
            
            # Log to DB if OTP provided
            if otp:
                try:
                    from django.utils import timezone
                    if hasattr(otp, 'save'):
                        otp.sent_at = timezone.now()
                        otp.send_result = 1
                        otp.save(update_fields=['sent_at', 'send_result'])
                except Exception:
                    pass
            
            return {"success": True, "result": "OK"}
        else:
            logger.error(f"EmailJS failed: {response.text}")
            return {"success": False, "result": response.text}
            
    except Exception as e:
        logger.error(f"EmailJS error: {e}")
        return {"success": False, "result": str(e)}
