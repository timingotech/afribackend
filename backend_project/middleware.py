"""
Middleware for automatic error logging
Captures errors from API responses and stores them in database
"""

import json
from apps.errors.services import ErrorTrackingService


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
            
            # Create error log using ErrorTrackingService
            user_email = request.user.email if request.user.is_authenticated else None
            
            # Extract detailed error message
            if response_data:
                # Try multiple common error field names
                message = response_data.get('detail') or response_data.get('error') or response_data.get('message')
                if isinstance(message, list):
                    message = str(message[0]) if message else 'Unknown error'
                else:
                    message = str(message) if message else 'Unknown error'
            else:
                message = 'Unknown error'
            
            ErrorTrackingService.log_frontend_error(
                {
                    'error_type': error_type,
                    'title': title,
                    'message': message,
                    'severity': severity,
                    'status_code': status_code,
                    'endpoint': request.path,
                    'method': request.method,
                    'request_data': request_data,
                    'response_data': response_data,
                    'user_email': user_email,
                },
                request=request
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create error log: {e}")
