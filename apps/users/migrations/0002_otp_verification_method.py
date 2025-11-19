# Generated migration for OTP model updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='otp',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='otp',
            name='method',
            field=models.CharField(
                choices=[('email', 'Email'), ('phone', 'Phone')],
                default='phone',
                max_length=10,
            ),
        ),
    ]
