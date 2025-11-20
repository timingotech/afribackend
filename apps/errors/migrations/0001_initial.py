# Generated migration - Run migrations in order: makemigrations -> migrate

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ErrorLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('error_type', models.CharField(choices=[('validation', 'Validation Error'), ('authentication', 'Authentication Error'), ('authorization', 'Authorization Error'), ('network', 'Network Error'), ('database', 'Database Error'), ('server', 'Server Error'), ('unknown', 'Unknown Error')], db_index=True, default='unknown', max_length=20)),
                ('severity', models.CharField(choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], db_index=True, default='medium', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('traceback', models.TextField(blank=True, null=True)),
                ('endpoint', models.CharField(blank=True, max_length=500, null=True)),
                ('method', models.CharField(blank=True, choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('PATCH', 'PATCH'), ('DELETE', 'DELETE'), ('HEAD', 'HEAD'), ('OPTIONS', 'OPTIONS')], max_length=10, null=True)),
                ('status_code', models.IntegerField(blank=True, db_index=True, null=True)),
                ('user_email', models.EmailField(blank=True, db_index=True, max_length=254, null=True)),
                ('request_data', models.JSONField(blank=True, null=True)),
                ('response_data', models.JSONField(blank=True, null=True)),
                ('resolved', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['-created_at'], name='errors_error_created_idx'),
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['severity', '-created_at'], name='errors_error_severity_idx'),
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['error_type', '-created_at'], name='errors_error_type_idx'),
        ),
        migrations.AddIndex(
            model_name='errorlog',
            index=models.Index(fields=['resolved', '-created_at'], name='errors_error_resolved_idx'),
        ),
    ]
