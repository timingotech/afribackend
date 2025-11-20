from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ErrorLogViewSet

router = DefaultRouter()
router.register(r'errors', ErrorLogViewSet, basename='error-log')

urlpatterns = [
    path('', include(router.urls)),
]
