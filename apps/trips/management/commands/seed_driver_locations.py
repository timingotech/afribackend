from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Seed sample driver users and driver locations for testing the Admin Driver Locations map'

    def handle(self, *args, **options):
        User = get_user_model()
        samples = [
            {
                'email': 'testuser@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+2348012345678',
                'role': 'rider',
                'lat': 6.5244,
                'lng': 3.3792,
            },
            {
                'email': 'taonuga@gmail.com',
                'first_name': 'RIDWAN',
                'last_name': 'OYENUGA',
                'phone': '09022013274',
                'role': 'rider',
                'lat': 6.5250,
                'lng': 3.3800,
            },
            {
                'email': 'taonuga01@gmail.com',
                'first_name': 'RIDWAN',
                'last_name': '',
                'phone': '09022013174',
                'role': 'rider',
                'lat': 6.5238,
                'lng': 3.3785,
            },
        ]

        created_users = []
        for s in samples:
            user, created = User.objects.get_or_create(
                email=s['email'],
                defaults={
                    'first_name': s.get('first_name', ''),
                    'last_name': s.get('last_name', ''),
                    'phone': s.get('phone'),
                    'role': s.get('role', 'rider'),
                    'is_active': True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            created_users.append((user, s['lat'], s['lng']))

        # Create DriverLocation entries
        try:
            from apps.trips.models import DriverLocation
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Could not import DriverLocation model: {e}'))
            return

        for user, lat, lng in created_users:
            dl, _ = DriverLocation.objects.update_or_create(
                driver=user,
                defaults={'lat': float(lat), 'lng': float(lng)}
            )
            self.stdout.write(self.style.SUCCESS(f'Created/Updated DriverLocation for {user.email} -> ({lat}, {lng})'))

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
