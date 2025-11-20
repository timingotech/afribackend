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
        # Get verification_method from user object (set in serializer.create())
        verification_method = getattr(user, '_verification_method', self.request.data.get('verification_method', 'phone'))
        
        try:
            if verification_method == 'email':
                # Send OTP via email
                code = str(random.randint(100000, 999999))
                otp = OTP.objects.create(user=user, email=user.email, code=code, method='email')
                
                # Send email synchronously with explicit error handling
                from django.core.mail import send_mail
                from django.db import connection
                
                # Ensure database transaction is committed before sending email
                connection.commit()
                
                try:
                    result = send_mail(
                        subject="Your AAfri Ride Verification Code",
                        message=f"Your code is: {code}\n\nValid for 10 minutes.",
                        from_email='support@aafriride.com',
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    print(f"[OK] OTP email sent to {user.email}, result: {result}")
                except Exception as email_error:
                    print(f"[ERROR] Failed to send OTP email: {email_error}")
                    import traceback
                    traceback.print_exc()
            
            elif verification_method == 'phone':
                # Send OTP via SMS
                if user.phone:
                    code = str(random.randint(100000, 999999))
                    OTP.objects.create(user=user, phone=user.phone, code=code, method='phone')
                    
                    from .sms import send_otp_sms
                    try:
                        send_otp_sms(user.phone, code)
                        print(f"[OK] OTP SMS sent to {user.phone}")
                    except Exception as sms_error:
                        print(f"[ERROR] Failed to send OTP SMS: {sms_error}")
        except Exception as e:
            # Don't fail registration if OTP sending fails
            print(f"[ERROR] in perform_create: {e}")
            import traceback
            traceback.print_exc()

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            verification_method = request.data.get('verification_method', 'phone')
            
            if response.status_code == 201:
                if verification_method == 'email':
                    user_email = request.data.get('email')
                    response.data['detail'] = 'User registered successfully. Check your email for OTP verification code.'
                    response.data['verification_method'] = 'email'
                    response.data['contact'] = user_email
                    # Get the latest OTP for this email
                    try:
                        latest_otp = OTP.objects.filter(email=user_email, method='email').latest('created_at')
                        response.data['otp_code'] = latest_otp.code  # For testing purposes
                    except OTP.DoesNotExist:
                        pass
                else:
                    user_phone = request.data.get('phone')
                    response.data['detail'] = 'User registered successfully. Check your phone for OTP verification code.'
                    response.data['verification_method'] = 'phone'
                    response.data['contact'] = user_phone
                    # Get the latest OTP for this phone
                    try:
                        latest_otp = OTP.objects.filter(phone=user_phone, method='phone').latest('created_at')
                        response.data['otp_code'] = latest_otp.code  # For testing purposes
                    except OTP.DoesNotExist:
                        pass
            
            return response
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in registration create: {e}")
            return Response(
                {'detail': f'Registration error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def generate_otp(request):
    method = request.data.get('method', 'phone')  # 'email' or 'phone'
    
    if method == 'email':
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'email required'}, status=status.HTTP_400_BAD_REQUEST)
        code = str(random.randint(100000, 999999))
        otp = OTP.objects.create(email=email, code=code, method='email')
        
        # Queue async email task (non-blocking)
        from .tasks import send_email_task
        try:
            send_email_task.delay(email, "Your AAfri Ride Verification Code", 
                                 f"Your code is: {code}\n\nValid for 10 minutes.")
        except Exception as e:
            print(f"Warning: Could not queue email task: {e}")
        
        return Response({'email': email, 'code': code, 'method': 'email', 'detail': 'OTP sent to email'})
    
    else:  # phone method
        phone = request.data.get('phone')
        if not phone:
            return Response({'detail': 'phone required'}, status=status.HTTP_400_BAD_REQUEST)
        code = str(random.randint(100000, 999999))
        otp = OTP.objects.create(phone=phone, code=code, method='phone')
        
        # Queue async SMS task (non-blocking)
        from .tasks import send_otp_sms_task
        try:
            send_otp_sms_task.delay(phone, code)
        except Exception as e:
            print(f"Warning: Could not queue SMS task: {e}")
        
        return Response({'phone': phone, 'code': code, 'method': 'phone', 'detail': 'OTP sent to phone'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp(request):
    code = request.data.get('code')
    
    if not code:
        return Response({'detail': 'code required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Determine method based on what fields are provided
    method = request.data.get('method')
    email = request.data.get('email')
    phone = request.data.get('phone')
    
    # If method not specified, infer from provided fields
    if not method:
        if email:
            method = 'email'
        elif phone:
            method = 'phone'
        else:
            return Response({'detail': 'Either email or phone required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if method == 'email':
        if not email:
            return Response({'detail': 'email required when using email verification method'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            otp = OTP.objects.filter(email=email, code=code, verified=False, method='email').latest('created_at')
        except OTP.DoesNotExist:
            return Response({'detail': 'Invalid OTP or already verified'}, status=status.HTTP_400_BAD_REQUEST)
    else:  # phone method
        if not phone:
            return Response({'detail': 'phone required when using phone verification method'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            otp = OTP.objects.filter(phone=phone, code=code, verified=False, method='phone').latest('created_at')
        except OTP.DoesNotExist:
            return Response({'detail': 'Invalid OTP or already verified'}, status=status.HTTP_400_BAD_REQUEST)
    
    if otp.is_expired:
        return Response({'detail': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
    
    otp.verified = True
    otp.save()
    
    # Mark user as verified
    if otp.user:
        # If OTP has associated user, use it
        otp.user.is_verified = True
        otp.user.save()
    elif method == 'email' and email:
        # If OTP was for email, find user by email
        try:
            user = User.objects.get(email=email)
            user.is_verified = True
            user.save()
        except User.DoesNotExist:
            pass
    elif method == 'phone' and phone:
        # If OTP was for phone, find user by phone
        try:
            user = User.objects.get(phone=phone)
            user.is_verified = True
            user.save()
        except User.DoesNotExist:
            pass
    
    return Response({'detail': 'verified', 'method': method})


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
            # Require email/phone verification for non-staff users
            if not user.is_staff and not user.is_verified:
                return Response(
                    {'detail': 'Please verify your email/phone with OTP first. Use /api/users/otp/verify/ endpoint.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except User.DoesNotExist:
            pass
        
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
