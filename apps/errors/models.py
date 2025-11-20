import uuid
from django.db import models


class ErrorLog(models.Model):
    ERROR_TYPES = [
        ('validation', 'Validation Error'),
        ('authentication', 'Authentication Error'),
        ('authorization', 'Authorization Error'),
        ('network', 'Network Error'),
        ('database', 'Database Error'),
        ('server', 'Server Error'),
        ('unknown', 'Unknown Error'),
    ]

    SEVERITY_LEVELS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    error_type = models.CharField(
        max_length=20,
        choices=ERROR_TYPES,
        default='unknown',
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='medium',
        db_index=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    traceback = models.TextField(blank=True, null=True)
    endpoint = models.CharField(max_length=500, blank=True, null=True)
    method = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=[
            ('GET', 'GET'),
            ('POST', 'POST'),
            ('PUT', 'PUT'),
            ('PATCH', 'PATCH'),
            ('DELETE', 'DELETE'),
            ('HEAD', 'HEAD'),
            ('OPTIONS', 'OPTIONS'),
        ]
    )
    status_code = models.IntegerField(blank=True, null=True, db_index=True)
    user_email = models.EmailField(blank=True, null=True, db_index=True)
    request_data = models.JSONField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['error_type', '-created_at']),
            models.Index(fields=['resolved', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title} ({self.created_at})"

    @property
    def error_type_display(self):
        return dict(self.ERROR_TYPES).get(self.error_type, 'Unknown')

    @property
    def severity_display(self):
        return dict(self.SEVERITY_LEVELS).get(self.severity, 'Unknown')
