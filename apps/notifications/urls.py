from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ErrorLogViewSet, get_recent_errors, log_frontend_error, cleanup_old_errors

router = DefaultRouter()
router.register(r'errors', ErrorLogViewSet, basename='error-log')

urlpatterns = [
    path('', include(router.urls)),
    path('errors/recent/', get_recent_errors, name='recent-errors'),
    path('errors/log-frontend/', log_frontend_error, name='log-frontend-error'),
    path('errors/cleanup/', cleanup_old_errors, name='cleanup-errors'),
]
