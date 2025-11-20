from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import ErrorLog
from .serializers import ErrorLogSerializer, ErrorLogCreateSerializer
from django.utils import timezone
from datetime import timedelta


class ErrorLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ErrorLog management
    - GET /api/notifications/errors/ - List all errors (paginated)
    - GET /api/notifications/errors/{id}/ - Get specific error
    - POST /api/notifications/errors/ - Create new error log
    - PATCH /api/notifications/errors/{id}/ - Mark as resolved
    """
    
    queryset = ErrorLog.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ErrorLogCreateSerializer
        return ErrorLogSerializer
    
    def get_queryset(self):
        """Filter errors by user"""
        user = self.request.user
        
        # Admin users see all errors
        if user.is_staff:
            return ErrorLog.objects.all()
        
        # Regular users see only their own errors and unresolved critical errors
        return ErrorLog.objects.filter(
            models.Q(user=user) | models.Q(severity='critical', resolved=False)
        )
    
    def perform_create(self, serializer):
        """Automatically assign current user to error log"""
        serializer.save(user=self.request.user)
    
    def partial_update(self, request, *args, **kwargs):
        """Allow marking errors as resolved"""
        instance = self.get_object()
        if 'resolved' in request.data:
            instance.resolved = request.data.get('resolved', False)
            instance.save()
            return Response(ErrorLogSerializer(instance).data)
        return super().partial_update(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_recent_errors(request):
    """
    Get recent errors for dashboard
    Query params:
    - limit: number of errors to return (default 20)
    - severity: filter by severity level
    - error_type: filter by error type
    - hours: get errors from last N hours (default 24)
    """
    
    limit = int(request.query_params.get('limit', 20))
    severity = request.query_params.get('severity')
    error_type = request.query_params.get('error_type')
    hours = int(request.query_params.get('hours', 24))
    
    # Base queryset
    user = request.user
    if user.is_staff:
        queryset = ErrorLog.objects.all()
    else:
        from django.db import models as django_models
        queryset = ErrorLog.objects.filter(
            django_models.Q(user=user) | django_models.Q(severity='critical', resolved=False)
        )
    
    # Filter by time
    time_threshold = timezone.now() - timedelta(hours=hours)
    queryset = queryset.filter(created_at__gte=time_threshold)
    
    # Apply optional filters
    if severity:
        queryset = queryset.filter(severity=severity)
    if error_type:
        queryset = queryset.filter(error_type=error_type)
    
    # Get recent errors
    errors = queryset[:limit]
    serializer = ErrorLogSerializer(errors, many=True)
    
    return Response({
        'count': len(errors),
        'results': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def log_frontend_error(request):
    """
    Endpoint for frontend to log errors
    Frontend can use this to report client-side errors
    """
    
    serializer = ErrorLogCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Assign user if authenticated
        user = request.user if request.user.is_authenticated else None
        error = serializer.save(user=user)
        return Response(
            ErrorLogSerializer(error).data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cleanup_old_errors(request):
    """
    Manually trigger cleanup of errors older than 30 days
    (Usually called by a scheduled task, but can be called manually by admin)
    """
    
    if not request.user.is_staff:
        return Response(
            {'detail': 'Only admin users can trigger cleanup'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    threshold = timezone.now() - timedelta(days=30)
    deleted_count, _ = ErrorLog.objects.filter(created_at__lt=threshold).delete()
    
    return Response({
        'detail': f'Deleted {deleted_count} error logs older than 30 days',
        'deleted_count': deleted_count
    })
