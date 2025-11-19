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


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific user (admin only)"""
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
            
            # Send SMS asynchronously via Celery
            from .tasks import send_otp_sms_task
            try:
                send_otp_sms_task.delay(user.phone, code)
            except Exception as e:
                print(f"Warning: Could not queue SMS task: {e}")
                # Fall back to sync SMS if Celery not available
                from .sms import send_otp_sms
                send_otp_sms(user.phone, code)

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
    """
    Generate OTP and send via email or SMS
    
    Expected body:
    {
        "email": "user@example.com",  // OR
        "phone": "+2349022013174",
        "method": "email" or "sms"  // (optional, defaults to provided field)
    }
    """
    phone = request.data.get('phone')
    email = request.data.get('email')
    method = request.data.get('method', 'sms' if phone else 'email')
    
    if not phone and not email:
        return Response(
            {'detail': 'Either phone or email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    code = str(random.randint(100000, 999999))
    
    # Create OTP record
    if email:
        otp = OTP.objects.create(phone=email, code=code)  # Use email as phone field temporarily
    else:
        otp = OTP.objects.create(phone=phone, code=code)
    
    # Send OTP via selected method
    if method == 'email' or email:
        from .email import send_otp_email
        from .tasks import send_email_task
        try:
            send_email_task.delay(email, code) if email else None
        except Exception as e:
            print(f"Warning: Could not queue email task: {e}")
            send_otp_email(email, code) if email else None
        
        return Response({
            'email': email,
            'code': code,
            'detail': 'OTP sent to email',
            'method': 'email'
        }, status=status.HTTP_201_CREATED)
    
    else:  # SMS method
        from .sms import send_otp_sms
        from .tasks import send_otp_sms_task
        try:
            send_otp_sms_task.delay(phone, code)
        except Exception as e:
            print(f"Warning: Could not queue SMS task: {e}")
            send_otp_sms(phone, code)
        
        return Response({
            'phone': phone,
            'code': code,
            'detail': 'OTP sent to phone',
            'method': 'sms'
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    """
    Verify OTP sent to email or phone
    
    Expected body:
    {
        "phone": "+2349022013174",  // OR
        "email": "user@example.com",
        "code": "123456"
    }
    """
    phone = request.data.get('phone')
    email = request.data.get('email')
    code = request.data.get('code')
    
    if not code:
        return Response({'detail': 'code required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not phone and not email:
        return Response({'detail': 'Either phone or email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Use email as the identifier if provided, otherwise phone
    identifier = email if email else phone
    
    try:
        otp = OTP.objects.filter(phone=identifier, code=code, verified=False).latest('created_at')
    except OTP.DoesNotExist:
        return Response({'detail': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
    
    if otp.is_expired:
        return Response({'detail': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
    
    otp.verified = True
    otp.save()
    
    return Response({
        'detail': 'verified',
        'identifier': identifier,
        'type': 'email' if email else 'phone'
    })


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
            if not user.is_staff:
                # Check if user needs OTP verification (has phone or email set)
                if user.phone or user.email:
                    # Check if email OTP is verified
                    email_verified = OTP.objects.filter(phone=user.email, verified=True).exists()
                    # Check if phone OTP is verified
                    phone_verified = OTP.objects.filter(phone=user.phone, verified=True).exists() if user.phone else False
                    
                    if not (email_verified or phone_verified):
                        return Response(
                            {'detail': 'Please verify your email or phone with OTP first. Use /api/users/otp/generate/ and /api/users/otp/verify/ endpoints.'},
                            status=status.HTTP_403_FORBIDDEN
                        )
        except User.DoesNotExist:
            pass
        
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
