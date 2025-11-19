from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser for AAfri Ride admin'

    def handle(self, *args, **options):
        username = 'adminpanel'
        email = 'afriride@gmail.com'
        password = 'AafrirideAdmin1.23#'

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser with email {email} already exists!')
            )
            return

        # Create superuser
        user = User.objects.create_superuser(
            email=email,
            password=password,
            phone='+234800000000'  # Default phone
        )
        user.first_name = 'Admin'
        user.last_name = 'Panel'
        user.role = 'admin'
        user.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created superuser:\n'
                f'Email: {email}\n'
                f'Username: {username}\n'
                f'Password: {password}'
            )
        )
