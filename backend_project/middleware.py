"""
Middleware for automatic error logging
Captures errors from API responses and stores them in database
"""

import json
from django.utils.deprecation import MiddlewareNotRequired
from apps.notifications.models import ErrorLog


class ErrorLoggingMiddleware:
    """
    Middleware to automatically log HTTP errors to database
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log errors (5xx and 4xx responses)
        if response.status_code >= 400:
            try:
                # Only log for API endpoints
                if request.path.startswith('/api/'):
                    self._log_error(request, response)
            except Exception as e:
                # Don't let error logging break the request
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to log error: {e}")
        
        return response
    
    def _log_error(self, request, response):
        """Log the error to database"""
        
        try:
            # Parse response content
            response_data = None
            if response.get('content-type', '').startswith('application/json'):
                try:
                    response_data = json.loads(response.content.decode('utf-8'))
                except:
                    pass
            
            # Parse request data
            request_data = None
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    request_data = json.loads(request.body.decode('utf-8'))
                except:
                    pass
            
            # Determine error type and severity based on status code
            status_code = response.status_code
            if status_code >= 500:
                error_type = 'server'
                severity = 'critical'
                title = 'Server Error'
            elif status_code == 401:
                error_type = 'authentication'
                severity = 'high'
                title = 'Authentication Error'
            elif status_code == 403:
                error_type = 'authorization'
                severity = 'medium'
                title = 'Authorization Error'
            elif status_code == 404:
                error_type = 'unknown'
                severity = 'low'
                title = 'Not Found'
            elif status_code >= 400:
                error_type = 'validation'
                severity = 'medium'
                title = 'Validation Error'
            else:
                return  # Don't log non-error responses
            
            # Create error log
            ErrorLog.objects.create(
                error_type=error_type,
                title=title,
                message=str(response_data.get('detail', response_data.get('error', 'Unknown error'))) if response_data else 'Unknown error',
                status_code=status_code,
                user=request.user if request.user.is_authenticated else None,
                endpoint=request.path,
                method=request.method,
                request_data=request_data,
                response_data=response_data,
                severity=severity,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create error log: {e}")
