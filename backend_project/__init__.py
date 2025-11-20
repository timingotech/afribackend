# Import Celery app so it gets registered with Django
from .celery import app as celery_app

__all__ = ('celery_app',)
