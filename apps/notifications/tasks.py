"""
Celery tasks for notifications (push)
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, time_limit=30)
def send_push_task(self, device_tokens, title, body, data=None):
    """Async task to send push notifications via FCM.

    Args:
        device_tokens: list of device registration tokens
        title: notification title
        body: notification body
        data: optional dict payload
    """
    try:
        import firebase_admin
        from firebase_admin import messaging
        # Initialize app lazily in worker if not already
        try:
            firebase_admin.get_app()
        except Exception:
            import os
            import json
            from firebase_admin import credentials
            cred_env = os.getenv('FCM_CREDENTIALS_JSON')
            cred_path = os.getenv('FCM_CREDENTIALS_PATH')
            if cred_env:
                cred_dict = json.loads(cred_env)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            elif cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                logger.warning('FCM credentials not configured for Celery worker')

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=device_tokens,
            data=data or {}
        )
        response = messaging.send_multicast(message)
        logger.info(f'FCM sent (task): success={response.success_count} failure={response.failure_count}')
        return {'success': True, 'success_count': response.success_count, 'failure_count': response.failure_count}

    except ModuleNotFoundError:
        logger.info('firebase_admin not installed in worker; push skipped (mock)')
        return {'success': True, 'mock': True, 'delivered': len(device_tokens)}
    except Exception as e:
        logger.exception('Failed to send push notification in task')
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60)
