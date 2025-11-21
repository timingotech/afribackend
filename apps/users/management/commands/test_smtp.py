from django.core.management.base import BaseCommand
from django.conf import settings
import socket
import sys
import traceback

class Command(BaseCommand):
    help = 'Test outbound SMTP connectivity and send a test email. Usage: python manage.py test_smtp --recipient you@example.com'

    def add_arguments(self, parser):
        parser.add_argument('--host', type=str, default=getattr(settings, 'EMAIL_HOST', 'smtp.zoho.com'))
        parser.add_argument('--port', type=int, default=getattr(settings, 'EMAIL_PORT', 587))
        parser.add_argument('--recipient', type=str, default=getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@aafriride.com'))
        parser.add_argument('--send', action='store_true', help='Actually attempt to send an email using send_mail')
        parser.add_argument('--timeout', type=int, default=8, help='Socket timeout in seconds')

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        recipient = options['recipient']
        do_send = options['send']
        timeout = options['timeout']

        self.stdout.write(self.style.MIGRATE_HEADING('SMTP Connectivity Test'))
        self.stdout.write(f'Host: {host}\nPort: {port}\nTimeout: {timeout}s\n')

        # TCP socket test
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            s.close()
            self.stdout.write(self.style.SUCCESS(f'OK: TCP connection to {host}:{port} succeeded'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR: TCP connection to {host}:{port} failed: {e}'))
            tb = traceback.format_exc()
            self.stdout.write(tb)

        # Optionally attempt to send a real email using Django's send_mail
        if do_send:
            self.stdout.write('\n' + self.style.MIGRATE_HEADING('Attempting send_mail test'))
            try:
                from django.core.mail import send_mail
                subject = 'AAfri Ride SMTP test'
                message = 'This is a test message from manage.py test_smtp.'
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
                result = send_mail(subject, message, from_email, [recipient], fail_silently=False)
                self.stdout.write(self.style.SUCCESS(f'send_mail returned: {result}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'send_mail failed: {e}'))
                tb = traceback.format_exc()
                self.stdout.write(tb)

        self.stdout.write('\nDone.')
