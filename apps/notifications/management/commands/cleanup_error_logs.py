from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.notifications.models import ErrorLog


class Command(BaseCommand):
    help = 'Delete error logs older than 30 days'

    def handle(self, *args, **options):
        threshold = timezone.now() - timedelta(days=30)
        deleted_count, _ = ErrorLog.objects.filter(created_at__lt=threshold).delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_count} error logs older than 30 days'
            )
        )
