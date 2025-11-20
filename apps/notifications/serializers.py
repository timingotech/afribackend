from rest_framework import serializers
from .models import ErrorLog


class ErrorLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    error_type_display = serializers.CharField(source='get_error_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = ErrorLog
        fields = [
            'id',
            'error_type',
            'error_type_display',
            'title',
            'message',
            'status_code',
            'user',
            'user_email',
            'endpoint',
            'method',
            'traceback',
            'request_data',
            'response_data',
            'severity',
            'severity_display',
            'resolved',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'error_type_display',
            'severity_display',
            'created_at',
            'updated_at',
        ]


class ErrorLogCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating error logs from frontend/backend"""
    
    class Meta:
        model = ErrorLog
        fields = [
            'error_type',
            'title',
            'message',
            'status_code',
            'endpoint',
            'method',
            'traceback',
            'request_data',
            'response_data',
            'severity',
        ]
