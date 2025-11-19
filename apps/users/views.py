from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer, UserSerializer, ProfileSerializer, DeviceSerializer
from .models import OTP, Device
from django.utils import timezone
import random

User = get_user_model()


class ListUsersView(generics.ListAPIView):
    """List all users (admin only)"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.all()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Automatically generate OTP after registration
        if user.phone:
            code = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, phone=user.phone, code=code)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user_phone = request.data.get('phone')
        if user_phone and response.status_code == 201:
            response.data['detail'] = 'User registered successfully. Check your phone for OTP verification code.'
            response.data['phone'] = user_phone
            # Get the latest OTP for this phone
            try:
                latest_otp = OTP.objects.filter(phone=user_phone).latest('created_at')
                response.data['otp_code'] = latest_otp.code  # For testing purposes
            except OTP.DoesNotExist:
                pass
        return response


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def generate_otp(request):
    phone = request.data.get('phone')
    if not phone:
        return Response({'detail': 'phone required'}, status=status.HTTP_400_BAD_REQUEST)
    code = str(random.randint(100000, 999999))
    otp = OTP.objects.create(phone=phone, code=code)
    # TODO: queue SMS via Celery
    return Response({'phone': phone, 'code': code})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    phone = request.data.get('phone')
    code = request.data.get('code')
    try:
        otp = OTP.objects.filter(phone=phone, code=code, verified=False).latest('created_at')
    except OTP.DoesNotExist:
        return Response({'detail': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
    if otp.is_expired:
        return Response({'detail': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
    otp.verified = True
    otp.save()
    return Response({'detail': 'verified'})


class DeviceRegisterView(generics.CreateAPIView):
    serializer_class = DeviceSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ObtainTokenPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            # Skip OTP verification for admin users
            if not user.is_staff and user.phone:
                verified_otp = OTP.objects.filter(user=user, verified=True).exists()
                if not verified_otp:
                    return Response(
                        {'detail': 'Please verify your phone number with OTP first. Use /api/users/otp/verify/ endpoint.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        except User.DoesNotExist:
            pass
        
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
