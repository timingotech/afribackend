import traceback as tb
from django.utils import timezone
from .models import ErrorLog


class ErrorTrackingService:
    """Service for logging and tracking application errors"""

    @staticmethod
    def log_error(request, exception, user_email=None, status_code=None):
        """
        Log an error to the database
        
        Args:
            request: Django request object
            exception: The exception that occurred
            user_email: Email of user encountering error (optional)
            status_code: HTTP status code if applicable (optional)
        """
        try:
            error_type = ErrorTrackingService.classify_error(exception)
            severity = ErrorTrackingService.set_severity(exception, status_code)
            
            error_log = ErrorLog(
                error_type=error_type,
                severity=severity,
                title=exception.__class__.__name__,
                message=str(exception),
                traceback=tb.format_exc(),
                endpoint=ErrorTrackingService.get_endpoint(request),
                method=request.method if request else None,
                status_code=status_code,
                user_email=user_email or ErrorTrackingService.get_user_email(request),
                request_data=ErrorTrackingService.get_request_data(request),
                response_data=None,
            )
            
            error_log.save()
            return error_log
        except Exception as e:
            print(f"Error logging failed: {str(e)}")
            return None

    @staticmethod
    def log_frontend_error(error_data, request=None):
        """
        Log a frontend error
        
        Args:
            error_data: Dictionary containing error information
            request: Django request object (optional)
        """
        try:
            error_log = ErrorLog(
                error_type=error_data.get('error_type', 'unknown'),
                severity=error_data.get('severity', 'medium'),
                title=error_data.get('title', 'Frontend Error'),
                message=error_data.get('message', ''),
                traceback=error_data.get('traceback', ''),
                endpoint=error_data.get('endpoint', ''),
                method=error_data.get('method', ''),
                status_code=error_data.get('status_code', None),
                user_email=error_data.get('user_email') or (
                    ErrorTrackingService.get_user_email(request) if request else None
                ),
                request_data=error_data.get('request_data', None),
                response_data=error_data.get('response_data', None),
            )
            
            error_log.save()
            return error_log
        except Exception as e:
            print(f"Frontend error logging failed: {str(e)}")
            return None

    @staticmethod
    def classify_error(exception):
        """
        Classify an error based on exception type
        
        Args:
            exception: The exception to classify
            
        Returns:
            String representing error type
        """
        exception_type = type(exception).__name__
        
        validation_errors = [
            'ValidationError',
            'ValueError',
            'TypeError',
            'AttributeError',
        ]
        
        auth_errors = [
            'AuthenticationFailed',
            'InvalidToken',
            'PermissionDenied',
        ]
        
        db_errors = [
            'DatabaseError',
            'IntegrityError',
            'DataError',
            'OperationalError',
        ]
        
        if exception_type in validation_errors:
            return 'validation'
        elif exception_type in auth_errors:
            return 'authentication'
        elif exception_type in db_errors:
            return 'database'
        elif 'Connection' in exception_type or 'Timeout' in exception_type:
            return 'network'
        elif 'Server' in exception_type or 'Internal' in exception_type:
            return 'server'
        
        return 'unknown'

    @staticmethod
    def set_severity(exception, status_code=None):
        """
        Determine error severity based on exception and status code
        
        Args:
            exception: The exception
            status_code: HTTP status code (optional)
            
        Returns:
            String representing severity level
        """
        # Check status code first
        if status_code:
            if status_code >= 500:
                return 'critical'
            elif status_code >= 400:
                return 'high'
        
        # Check exception type
        exception_type = type(exception).__name__
        if 'Database' in exception_type or 'Operational' in exception_type:
            return 'critical'
        elif 'Authentication' in exception_type or 'Permission' in exception_type:
            return 'high'
        elif 'Validation' in exception_type:
            return 'medium'
        
        return 'medium'

    @staticmethod
    def get_endpoint(request):
        """Extract endpoint from request"""
        if request:
            return str(request.path)
        return None

    @staticmethod
    def get_user_email(request):
        """Extract user email from request"""
        try:
            if request and hasattr(request, 'user') and request.user.is_authenticated:
                return request.user.email
        except:
            pass
        return None

    @staticmethod
    def get_request_data(request):
        """Extract request data (safe version)"""
        try:
            if request:
                data = {
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET) if request.GET else {},
                }
                
                # Try to get body data safely
                if request.method in ['POST', 'PUT', 'PATCH']:
                    try:
                        if hasattr(request, 'data'):
                            # For DRF requests
                            data['body'] = request.data
                        elif hasattr(request, 'POST') and request.POST:
                            # For form data
                            data['body'] = dict(request.POST)
                    except:
                        pass
                
                return data
        except:
            pass
        return None

    @staticmethod
    def mark_resolved(error_id):
        """Mark an error as resolved"""
        try:
            error = ErrorLog.objects.get(id=error_id)
            error.resolved = True
            error.save(update_fields=['resolved', 'updated_at'])
            return error
        except ErrorLog.DoesNotExist:
            return None

    @staticmethod
    def cleanup_old_errors(days=30):
        """Delete errors older than specified days"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = ErrorLog.objects.filter(created_at__lt=cutoff_date).delete()
        return deleted_count

    @staticmethod
    def get_error_stats():
        """Get error statistics"""
        from django.db.models import Count
        
        return {
            'total': ErrorLog.objects.count(),
            'unresolved': ErrorLog.objects.filter(resolved=False).count(),
            'critical': ErrorLog.objects.filter(severity='critical').count(),
            'high': ErrorLog.objects.filter(severity='high').count(),
            'medium': ErrorLog.objects.filter(severity='medium').count(),
            'low': ErrorLog.objects.filter(severity='low').count(),
            'by_type': dict(
                ErrorLog.objects.values('error_type').annotate(count=Count('id'))
            ),
        }
