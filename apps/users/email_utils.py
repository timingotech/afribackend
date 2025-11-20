import logging
from django.core.mail import get_connection, EmailMessage

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
    try:
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
        log_line += f"ERROR={e}\n"
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_line)
        logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
        # Persist failure to DB if otp provided
        if otp is not None:
            try:
                from django.utils import timezone as _tz
                if hasattr(otp, 'save') and hasattr(otp, 'pk'):
                    otp.sent_at = _tz.now()
                    otp.send_result = 0
                    otp.send_error = str(e)
                    otp.save(update_fields=['sent_at', 'send_result', 'send_error'])
                else:
                    from .models import OTP as _OTP
                    o = _OTP.objects.filter(pk=otp).first()
                    if o:
                        o.sent_at = _tz.now()
                        o.send_result = 0
                        o.send_error = str(e)
                        o.save(update_fields=['sent_at', 'send_result', 'send_error'])
            except Exception:
                logger.exception('Failed to persist OTP send failure to DB')

        return {"success": False, "result": str(e)}
