from django.urls import path
from .views import (
    RegisterView, ListUsersView, UserDetailView, ProfileView, 
    generate_otp, verify_otp, DeviceRegisterView, 
    ObtainTokenPairView, RefreshTokenView, logout_view,
    OTPListView, DeviceListView, test_email_view
)
from .views import AdminDriverViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'admin/drivers', AdminDriverViewSet, basename='admin-drivers')

urlpatterns = [
    path('', ListUsersView.as_view(), name='list_users'),
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', ObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('logout/', logout_view, name='logout'),
    path('otp/generate/', generate_otp, name='otp_generate'),
    path('otp/verify/', verify_otp, name='otp_verify'),
    path('otps/', OTPListView.as_view(), name='otp_list'),  # Admin OTP list
    path('devices/', DeviceRegisterView.as_view(), name='device_register'),
    path('devices/list/', DeviceListView.as_view(), name='device_list'),  # Admin device list
    path('test-email/', test_email_view, name='test_email'),
]

urlpatterns += router.urls

 # add explicit approve route for convenience
from django.urls import re_path
urlpatterns += [
    re_path(r'^admin/drivers/(?P<pk>\d+)/approve/$', AdminDriverViewSet.approve, name='admin_driver_approve'),
]
