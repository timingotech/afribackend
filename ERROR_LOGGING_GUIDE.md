# Error Logging System - Frontend Integration

## Overview
The backend now has a comprehensive error logging system that stores all API errors in a database. The frontend can display these errors to users and admins.

## API Endpoints

### 1. Get Recent Errors (Dashboard)
```
GET /api/notifications/errors/recent/
```

**Query Parameters:**
- `limit` (optional, default=20): Number of errors to return
- `severity` (optional): Filter by severity (critical, high, medium, low)
- `error_type` (optional): Filter by error type (validation, authentication, network, database, server, etc.)
- `hours` (optional, default=24): Get errors from last N hours

**Example:**
```javascript
// Get 10 critical errors from last 24 hours
fetch('/api/notifications/errors/recent/?limit=10&severity=critical&hours=24')
  .then(res => res.json())
  .then(data => {
    console.log(`Found ${data.count} errors`);
    data.results.forEach(error => {
      console.log(`${error.title} - ${error.severity_display}`);
    });
  });
```

**Response:**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "error_type": "validation",
      "error_type_display": "Validation Error",
      "title": "Invalid Email Format",
      "message": "The email format is not valid",
      "status_code": 400,
      "user_email": "user@example.com",
      "endpoint": "/api/users/register/",
      "method": "POST",
      "severity": "medium",
      "severity_display": "Medium",
      "resolved": false,
      "created_at": "2025-11-20T07:33:43.429385Z",
      "updated_at": "2025-11-20T07:33:43.429385Z"
    }
  ]
}
```

### 2. List All Errors (Paginated)
```
GET /api/notifications/errors/
```

**Filters:**
- Automatically filtered by user (regular users see only their own errors + critical unresolved errors)
- Admin users see all errors

### 3. Get Specific Error
```
GET /api/notifications/errors/{id}/
```

### 4. Log Frontend Error
```
POST /api/notifications/errors/log-frontend/
```

**Payload:**
```json
{
  "error_type": "network",
  "title": "API Request Failed",
  "message": "Failed to fetch user profile",
  "status_code": 500,
  "endpoint": "/api/users/profile/",
  "method": "GET",
  "severity": "high",
  "traceback": "TypeError: Cannot read property 'data' of undefined",
  "request_data": {},
  "response_data": {"detail": "Server error"}
}
```

**Example JavaScript:**
```javascript
// Log an error from frontend
fetch('/api/notifications/errors/log-frontend/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    error_type: 'network',
    title: 'API Request Failed',
    message: error.message,
    endpoint: '/api/users/profile/',
    method: 'GET',
    severity: 'high'
  })
}).then(res => res.json());
```

### 5. Mark Error as Resolved
```
PATCH /api/notifications/errors/{id}/
```

**Payload:**
```json
{
  "resolved": true
}
```

### 6. Cleanup Old Errors (Admin Only)
```
POST /api/notifications/errors/cleanup/
```

Manually trigger deletion of errors older than 30 days.

## Frontend Component Example

### Error Dashboard Component (React)
```jsx
import React, { useState, useEffect } from 'react';

function ErrorLog() {
  const [errors, setErrors] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchErrors();
    // Poll for new errors every 30 seconds
    const interval = setInterval(fetchErrors, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const fetchErrors = async () => {
    setLoading(true);
    try {
      const url = new URL('/api/notifications/errors/recent/', window.location.origin);
      url.searchParams.set('limit', '50');
      
      if (filter !== 'all') {
        url.searchParams.set('severity', filter);
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      const data = await response.json();
      setErrors(data.results || []);
    } catch (error) {
      console.error('Failed to fetch errors:', error);
    } finally {
      setLoading(false);
    }
  };

  const markResolved = async (errorId) => {
    try {
      const response = await fetch(`/api/notifications/errors/${errorId}/`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ resolved: true })
      });

      if (response.ok) {
        // Remove from list
        setErrors(errors.filter(e => e.id !== errorId));
      }
    } catch (error) {
      console.error('Failed to resolve error:', error);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#dc3545',
      high: '#fd7e14',
      medium: '#ffc107',
      low: '#28a745'
    };
    return colors[severity] || '#6c757d';
  };

  return (
    <div className="error-log">
      <h2>Error Log</h2>
      
      <div className="filter-buttons">
        {['all', 'critical', 'high', 'medium', 'low'].map(sev => (
          <button
            key={sev}
            onClick={() => setFilter(sev)}
            className={filter === sev ? 'active' : ''}
          >
            {sev === 'all' ? 'All' : sev.charAt(0).toUpperCase() + sev.slice(1)}
          </button>
        ))}
      </div>

      {loading && <p>Loading errors...</p>}

      <div className="error-list">
        {errors.map(error => (
          <div
            key={error.id}
            className="error-item"
            style={{ borderLeft: `4px solid ${getSeverityColor(error.severity)}` }}
          >
            <div className="error-header">
              <h3>{error.title}</h3>
              <span className="badge" style={{ backgroundColor: getSeverityColor(error.severity) }}>
                {error.severity_display}
              </span>
            </div>
            
            <p>{error.message}</p>
            
            <div className="error-meta">
              <small>
                {error.endpoint} ({error.method}) - {error.error_type_display}
              </small>
              <small>
                {new Date(error.created_at).toLocaleString()}
              </small>
            </div>

            {error.user_email && (
              <small>User: {error.user_email}</small>
            )}

            <button
              onClick={() => markResolved(error.id)}
              className="btn-resolve"
            >
              Mark as Resolved
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ErrorLog;
```

## Automatic Error Cleanup

Errors older than 30 days are automatically deleted. You can also:

1. **Schedule automatic cleanup** using Django's management command:
```bash
python manage.py cleanup_error_logs
```

2. **Set up a cron job** to run the command daily:
```bash
# Add to crontab
0 2 * * * cd /path/to/backend && python manage.py cleanup_error_logs
```

3. **Manually trigger cleanup** via admin endpoint:
```javascript
fetch('/api/notifications/errors/cleanup/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${admin_token}`
  }
}).then(res => res.json());
```

## Error Types

- `validation` - Form/input validation errors
- `authentication` - Login/auth errors
- `authorization` - Permission/access errors
- `network` - Network/connection errors
- `database` - Database operation errors
- `server` - Server/internal errors
- `unknown` - Uncategorized errors

## Severity Levels

- `critical` - System-breaking errors
- `high` - Important errors that affect functionality
- `medium` - Standard errors
- `low` - Minor issues

## Backend Usage

### In Views/Serializers:
```python
from apps.notifications.utils import log_error, log_exception

# Log a simple error
log_error(
    error_type='validation',
    title='Invalid input',
    message='Email format is invalid',
    status_code=400,
    user=request.user,
    endpoint=request.path,
    severity='medium'
)

# Log an exception
try:
    # some code
except Exception as e:
    log_exception(
        exception=e,
        title='Database error',
        user=request.user,
        endpoint=request.path,
        error_type='database',
        severity='critical'
    )
```

## Database Schema

```sql
- id: Primary key
- error_type: Error type (choice field)
- title: Short error title
- message: Full error message
- status_code: HTTP status code
- user: Foreign key to User (optional)
- endpoint: API endpoint
- method: HTTP method
- traceback: Full stack trace
- request_data: Request JSON
- response_data: Response JSON
- severity: Severity level (choice field)
- resolved: Boolean flag
- created_at: Timestamp (auto indexed)
- updated_at: Timestamp
```

All errors are automatically indexed by created_at for efficient queries and cleanup.
