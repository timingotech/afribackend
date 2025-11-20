"""
Utility functions for error logging
Use these functions throughout the codebase to log errors to the database
"""

from apps.notifications.models import ErrorLog
import traceback
import logging

logger = logging.getLogger(__name__)


def log_error(
    error_type='unknown',
    title='An error occurred',
    message='',
    status_code=None,
    user=None,
    endpoint=None,
    method=None,
    traceback_str=None,
    request_data=None,
    response_data=None,
    severity='medium',
):
    """
    Log an error to the database for frontend display
    
    Args:
        error_type: Type of error (validation, authentication, network, etc.)
        title: Short error title
        message: Full error message
        status_code: HTTP status code if applicable
        user: User object associated with error (optional)
        endpoint: API endpoint where error occurred
        method: HTTP method (GET, POST, etc.)
        traceback_str: Full stack trace
        request_data: Request payload
        response_data: Response payload
        severity: Error severity (critical, high, medium, low)
    
    Returns:
        ErrorLog instance
    """
    
    try:
        error_log = ErrorLog.objects.create(
            error_type=error_type,
            title=title,
            message=message,
            status_code=status_code,
            user=user,
            endpoint=endpoint,
            method=method,
            traceback=traceback_str,
            request_data=request_data,
            response_data=response_data,
            severity=severity,
        )
        logger.info(f"Error logged: {title} ({error_type})")
        return error_log
    except Exception as e:
        logger.error(f"Failed to log error: {e}")
        return None


def log_exception(
    exception,
    title='An error occurred',
    user=None,
    endpoint=None,
    method=None,
    error_type='unknown',
    severity='high',
    request_data=None,
    response_data=None,
):
    """
    Log an exception with full traceback
    
    Args:
        exception: The exception instance
        title: Short error title
        user: User object
        endpoint: API endpoint
        method: HTTP method
        error_type: Type of error
        severity: Error severity
        request_data: Request payload
        response_data: Response payload
    
    Returns:
        ErrorLog instance
    """
    
    tb_str = traceback.format_exc()
    message = str(exception)
    status_code = getattr(exception, 'status_code', None)
    
    return log_error(
        error_type=error_type,
        title=title,
        message=message,
        status_code=status_code,
        user=user,
        endpoint=endpoint,
        method=method,
        traceback_str=tb_str,
        request_data=request_data,
        response_data=response_data,
        severity=severity,
    )
