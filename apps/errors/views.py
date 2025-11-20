from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from .models import ErrorLog
from .serializers import ErrorLogSerializer, ErrorListSerializer, ErrorCreateSerializer
from .services import ErrorTrackingService


class ErrorLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing error logs"""
    
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['severity', 'error_type', 'resolved']
    search_fields = ['title', 'message', 'endpoint', 'user_email']
    ordering_fields = ['created_at', 'severity', 'error_type']
    ordering = ['-created_at']
    pagination_class = None  # Allow large result sets for admin view

    def get_permissions(self):
        """Override permissions based on action"""
        if self.action == 'log':
            # Public endpoint for logging frontend errors
            return []
        else:
            # Admin-only for other endpoints
            return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'log':
            return ErrorCreateSerializer
        elif self.action == 'list':
            return ErrorListSerializer
        return ErrorLogSerializer

    @action(detail=False, methods=['post'], permission_classes=[])
    def log(self, request):
        """Log a frontend error - public endpoint"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            error_log = ErrorTrackingService.log_frontend_error(
                serializer.validated_data,
                request=request
            )
            return Response(
                {'id': str(error_log.id), 'created_at': error_log.created_at},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def recent(self, request):
        """Get recent errors with optional filtering"""
        limit = int(request.query_params.get('limit', 100))
        hours = int(request.query_params.get('hours', 24))
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        queryset = self.get_queryset().filter(created_at__gte=cutoff_time)[:limit]
        
        serializer = ErrorListSerializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def resolve(self, request, pk=None):
        """Mark an error as resolved"""
        error_log = self.get_object()
        error_log.resolved = True
        error_log.save(update_fields=['resolved', 'updated_at'])
        serializer = self.get_serializer(error_log)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def cleanup(self, request):
        """Delete errors older than 30 days"""
        days = int(request.data.get('days', 30))
        deleted_count = ErrorTrackingService.cleanup_old_errors(days=days)
        return Response({
            'deleted_count': deleted_count,
            'days': days
        })

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get error statistics"""
        stats = ErrorTrackingService.get_error_stats()
        return Response(stats)
