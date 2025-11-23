"""
Generated migration to add disapproval fields to RiderProfile.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_remove_riderprofile_id_document_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='riderprofile',
            name='disapproval_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='riderprofile',
            name='disapproved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
