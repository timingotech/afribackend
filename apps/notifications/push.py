import logging
logger = logging.getLogger(__name__)


def send_push_notification(device_tokens, title, body, data=None):
    """Send push notification via FCM if available. `device_tokens` is a list of FCM tokens.

    This function is resilient: if `firebase_admin` is not installed or credentials are
    not configured, it will log and return a mock success.
    """
    if not device_tokens:
        return {'success': False, 'error': 'no_tokens'}

    return _send_immediate(device_tokens, title, body, data)


def _send_immediate(device_tokens, title, body, data=None):
    try:
        import firebase_admin
        from firebase_admin import messaging
        # Initialize app lazily if not already
        try:
            firebase_admin.get_app()
        except Exception:
            cred_json = None
            import os
            # Optionally load credentials from env (JSON string) or a path
            cred_env = os.getenv('FCM_CREDENTIALS_JSON')
            cred_path = os.getenv('FCM_CREDENTIALS_PATH')
            if cred_env:
                import json
                cred_dict = json.loads(cred_env)
                from firebase_admin import credentials
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            elif cred_path:
                from firebase_admin import credentials
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # No credentials available; fall back to logging
                logger.warning('FCM credentials not configured')

        # Build message
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=device_tokens,
            data=data or {}
        )
        response = messaging.send_multicast(message)
        logger.info(f'FCM sent: success={response.success_count} failure={response.failure_count}')
        return {'success': True, 'success_count': response.success_count, 'failure_count': response.failure_count}

    except ModuleNotFoundError:
        logger.info('firebase_admin not installed; push notification skipped (mock)')
        # Return a fake success for development
        return {'success': True, 'mock': True, 'delivered': len(device_tokens)}
    except Exception as e:
        logger.exception('Failed to send push notification')
        return {'success': False, 'error': str(e)}


def send_push_async(device_tokens, title, body, data=None):
    """Attempt to send push notification asynchronously via Celery task.

    Falls back to synchronous send if Celery is not configured.
    """
    try:
        from .tasks import send_push_task
        # Call Celery task
        try:
            send_push_task.delay(device_tokens, title, body, data or {})
            return {'queued': True}
        except Exception:
            # If Celery or broker not available, fallback
            return _send_immediate(device_tokens, title, body, data)
    except Exception:
        # tasks module not available or import failed; fallback to immediate
        return _send_immediate(device_tokens, title, body, data)
