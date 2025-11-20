from rest_framework import serializers
from .models import ErrorLog


class ErrorLogSerializer(serializers.ModelSerializer):
    error_type_display = serializers.CharField(source='get_error_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = ErrorLog
        fields = [
            'id',
            'error_type',
            'error_type_display',
            'severity',
            'severity_display',
            'title',
            'message',
            'traceback',
            'endpoint',
            'method',
            'status_code',
            'user_email',
            'request_data',
            'response_data',
            'resolved',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'error_type_display',
            'severity_display',
            'created_at',
            'updated_at',
        ]


class ErrorListSerializer(serializers.ModelSerializer):
    error_type_display = serializers.CharField(source='get_error_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = ErrorLog
        fields = [
            'id',
            'error_type',
            'error_type_display',
            'severity',
            'severity_display',
            'title',
            'message',
            'endpoint',
            'method',
            'status_code',
            'user_email',
            'resolved',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'error_type_display',
            'severity_display',
            'created_at',
        ]


class ErrorCreateSerializer(serializers.Serializer):
    error_type = serializers.ChoiceField(
        choices=['validation', 'authentication', 'authorization', 'network', 'database', 'server', 'unknown'],
        default='unknown'
    )
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    severity = serializers.ChoiceField(
        choices=['critical', 'high', 'medium', 'low'],
        default='medium'
    )
    traceback = serializers.CharField(required=False, allow_blank=True)
    endpoint = serializers.CharField(required=False, allow_blank=True)
    method = serializers.CharField(required=False, allow_blank=True)
    status_code = serializers.IntegerField(required=False, allow_null=True)
    request_data = serializers.JSONField(required=False, allow_null=True)
    response_data = serializers.JSONField(required=False, allow_null=True)

    def create(self, validated_data):
        return ErrorLog.objects.create(**validated_data)
