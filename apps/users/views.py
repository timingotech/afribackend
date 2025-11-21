from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer
from .serializers import RegisterSerializer, UserSerializer, ProfileSerializer, DeviceSerializer, OTPSerializer
from .models import OTP, Device
from django.utils import timezone
import random
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Blacklist the provided refresh token or all outstanding tokens for the authenticated user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

    refresh = request.data.get('refresh')
    if refresh:
        try:
            token = RefreshToken(refresh)
            token.blacklist()
            return Response({'detail': 'Refresh token blacklisted'})
        except Exception:
            return Response({'detail': 'Invalid token provided'}, status=status.HTTP_400_BAD_REQUEST)

    # No specific token provided: blacklist all outstanding tokens for this user
    try:
        tokens = OutstandingToken.objects.filter(user=request.user)
        for t in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=t)
            except Exception:
                pass
    except Exception:
        pass

    return Response({'detail': 'All sessions logged out'})

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
                # Send OTP via email asynchronously using Celery
                code = str(random.randint(100000, 999999))
                otp = OTP.objects.create(user=user, email=user.email, code=code, method='email')
                
                # Try Celery first, fall back to direct send if Celery unavailable
                try:
                    from .tasks import send_otp_email_task
                    # Queue email task - will be processed by Celery worker
                    # Use apply_async with retry policy to ensure it's picked up
                    # Wrap in try/except to catch SystemExit or other critical errors if eager execution fails
                    try:
                        send_otp_email_task.apply_async(
                            args=[user.email, code, otp.id],
                            retry=True,
                            retry_policy={
                                'max_retries': 3,
                                'interval_start': 0,
                                'interval_step': 0.2,
                                'interval_max': 0.2,
                            }
                        )
                        print(f"[OK] OTP email queued via Celery for {user.email}")
                    except (Exception, SystemExit) as task_error:
                        # If task execution fails (e.g. timeout in eager mode), fall back to direct send
                        # Note: SystemExit is raised by Gunicorn on timeout, but catching it might not save the request
                        # if the worker is being killed. However, it's worth a try or at least logging it.
                        print(f"[WARN] Celery task execution failed ({task_error}), falling back to direct send")
                        raise task_error  # Re-raise to trigger the outer except block
                except (Exception, SystemExit) as celery_error:
                    # Celery not available, send directly (will block but reliable)
                    print(f"[WARN] Celery unavailable ({celery_error}), sending email directly")
                    from django.core.mail import send_mail
                    from django.conf import settings
                    try:
                        send_mail(
                            subject="Your AAfri Ride Verification Code",
                            message=f"Your code is: {code}\n\nValid for 5 minutes.",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[user.email],
                            fail_silently=False,
                        )
                        otp.sent_at = timezone.now()
                        otp.send_result = 1
                        otp.save(update_fields=['sent_at', 'send_result'])
                        print(f"[OK] OTP email sent directly to {user.email}")
                    except Exception as email_error:
                        print(f"[ERROR] Direct email failed: {email_error}")
                        otp.send_error = str(email_error)
                        otp.save(update_fields=['send_error'])
            
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
    serializer_class = CustomTokenObtainPairSerializer

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


class OTPListView(generics.ListAPIView):
    """List all OTPs (admin only)"""
    serializer_class = OTPSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = OTP.objects.all().order_by('-created_at')
        
        # Filter by method
        method = self.request.query_params.get('method')
        if method:
            queryset = queryset.filter(method=method)
        
        # Filter by verification status
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        # Search by email or phone
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(phone__icontains=search) | Q(code__icontains=search)
            )
        
        return queryset


class DeviceListView(generics.ListAPIView):
    """List all devices (admin only)"""
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Device.objects.all().order_by('-created_at')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_email_view(request):
    """Debug endpoint to test email sending from the server"""
    email = request.query_params.get('email', 'oyenugaridwan@gmail.com')
    from django.core.mail import send_mail
    from django.conf import settings
    import time
    import platform
    
    debug_info = {
        'backend': settings.EMAIL_BACKEND,
        'host': settings.EMAIL_HOST,
        'port': settings.EMAIL_PORT,
        'tls': settings.EMAIL_USE_TLS,
        'ssl': settings.EMAIL_USE_SSL,
        'timeout': getattr(settings, 'EMAIL_TIMEOUT', 'Not Set'),
        'system': platform.system(),
    }
    
    try:
        start = time.time()
        # Use a simpler send_mail call for debugging
        from django.core.mail import get_connection
        from django.core.mail.message import EmailMessage
        
        connection = get_connection()
        email_msg = EmailMessage(
            'Test Email from Debug Endpoint',
            f'This is a test email from {settings.EMAIL_BACKEND}.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            connection=connection,
        )
        email_msg.send(fail_silently=False)
        
        duration = time.time() - start
        return Response({'status': 'success', 'duration': duration, 'debug_info': debug_info})
    except Exception as e:
        return Response({'status': 'error', 'error': str(e), 'debug_info': debug_info}, status=500)
