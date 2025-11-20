import logging
from django.core.mail import get_connection, EmailMessage

logger = logging.getLogger(__name__)

LOG_PATH = 'logs/email_send.log'

def _ensure_log_dir():
    import os
    d = os.path.dirname(LOG_PATH)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def send_email_with_logging(to_email: str, subject: str, message: str, from_email: str = 'support@aafriride.com'):
    """Send an email using Django email backend and log the attempt to a file.

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
        return {"success": True, "result": result}
    except Exception as e:
        log_line += f"ERROR={e}\n"
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_line)
        logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
        return {"success": False, "result": str(e)}
