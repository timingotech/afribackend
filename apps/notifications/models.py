from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class ErrorLog(models.Model):
    """
    Model to store application errors for frontend display and debugging
    Automatically deletes errors older than 30 days
    """
    
    ERROR_TYPES = [
        ('validation', 'Validation Error'),
        ('authentication', 'Authentication Error'),
        ('authorization', 'Authorization Error'),
        ('network', 'Network Error'),
        ('database', 'Database Error'),
        ('server', 'Server Error'),
        ('unknown', 'Unknown Error'),
    ]

    # Error details
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES, default='unknown')
    title = models.CharField(max_length=255)  # Short error title
    message = models.TextField()  # Full error message
    status_code = models.IntegerField(null=True, blank=True)  # HTTP status code if applicable
    
    # Context information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='error_logs')
    endpoint = models.CharField(max_length=255, null=True, blank=True)  # API endpoint where error occurred
    method = models.CharField(max_length=10, null=True, blank=True)  # GET, POST, etc.
    
    # Additional debugging info
    traceback = models.TextField(null=True, blank=True)  # Full stack trace
    request_data = models.JSONField(null=True, blank=True)  # Request payload
    response_data = models.JSONField(null=True, blank=True)  # Response payload
    
    # Metadata
    severity = models.CharField(
        max_length=10,
        choices=[
            ('critical', 'Critical'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        default='medium'
    )
    resolved = models.BooleanField(default=False)  # Whether error has been addressed
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['error_type', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_error_type_display()} - {self.title}"

    @property
    def is_old(self):
        """Check if error is older than 30 days"""
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        return self.created_at < thirty_days_ago
