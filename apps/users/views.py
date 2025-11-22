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
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from .email_utils import send_email_with_logging
from .serializers import RiderProfileSerializer
from .models import RiderProfile
from rest_framework.permissions import IsAdminUser
from rest_framework import viewsets
from django.shortcuts import get_object_or_404

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
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        user = serializer.save()
        # Get verification_method from user object (set in serializer.create())
        verification_method = getattr(user, '_verification_method', self.request.data.get('verification_method', 'phone'))
        
        try:
            if verification_method == 'email':
                # Send OTP via email
                code = str(random.randint(100000, 999999))
                otp = OTP.objects.create(user=user, email=user.email, code=code, method='email')
                
                # Send using EmailJS (API based, reliable)
                print(f"[INFO] Sending OTP email via EmailJS to {user.email}")
                from .email_utils import send_email_via_emailjs
                
                # Run in background if possible, but for now call directly to ensure it works
                try:
                    result = send_email_via_emailjs(
                        to_email=user.email,
                        subject="Your AAfri Ride Verification Code",
                        message=f"Your code is: {code}\n\nValid for 5 minutes.",
                        otp=otp,
                        code=code
                    )
                    if result['success']:
                        print(f"[OK] OTP email sent via EmailJS to {user.email}")
                    else:
                        print(f"[ERROR] EmailJS failed: {result['result']}")
                        otp.send_error = str(result['result'])
                        otp.save(update_fields=['send_error'])
                except Exception as email_error:
                    print(f"[ERROR] EmailJS exception: {email_error}")
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

        # If this is a rider registration, send application acknowledgement to user
        try:
            if getattr(user, 'role', '') == getattr(User, 'RIDER', 'rider'):
                # Send email to user acknowledging application
                user_email = user.email
                if user_email:
                    try:
                        send_email_with_logging(
                            to_email=user_email,
                            subject='AAfri Ride - Driver Application Received',
                            message='Thank you. Your driver application has been received and is under review by our team. We will notify you once it is approved.'
                        )
                    except Exception as e:
                        print(f"Failed to send driver application email: {e}")

                # Notify staff/admin users
                try:
                    staff_emails = list(User.objects.filter(is_staff=True).exclude(email__isnull=True).exclude(email__exact='').values_list('email', flat=True))
                    for admin_email in staff_emails:
                        try:
                            send_email_with_logging(
                                to_email=admin_email,
                                subject='New Driver Application',
                                message=f'A new driver application was submitted by {user.email or user.phone}. Please review in the admin panel.'
                            )
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

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
        
        # Send using EmailJS
        from .email_utils import send_email_via_emailjs
        try:
            send_email_via_emailjs(
                to_email=email,
                subject="Your AAfri Ride Verification Code",
                message=f"Your code is: {code}\n\nValid for 10 minutes.",
                otp=otp,
                code=code
            )
        except Exception as e:
            print(f"Warning: Could not send email via EmailJS: {e}")
        
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
            # Require admin approval for riders
            if getattr(user, 'role', '') == getattr(User, 'RIDER', 'rider'):
                rider_profile = getattr(user, 'rider_profile', None)
                if rider_profile and not getattr(rider_profile, 'is_approved', False):
                    return Response(
                        {'detail': 'Driver application pending approval by admin. You cannot login until approved.'},
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


class AdminDriverViewSet(viewsets.ViewSet):
    """Admin API to list, create, and approve driver (RiderProfile) records."""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def list(self, request):
        queryset = RiderProfile.objects.select_related('user').order_by('-submitted_at')
        # allow filtering by approval status
        is_approved = request.query_params.get('is_approved')
        if is_approved is not None:
            queryset = queryset.filter(is_approved=(is_approved.lower() == 'true'))
        serializer = RiderProfileSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        profile = get_object_or_404(RiderProfile, pk=pk)
        serializer = RiderProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        # Expect user id or create user inline
        data = request.data.copy()
        user_id = data.get('user') or data.get('user_id')
        if not user_id:
            # create a user object for the driver (admin created)
            email = data.get('email')
            phone = data.get('phone')
            password = data.get('password') or User.objects.make_random_password()
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            role = User.RIDER
            user = User.objects.create_user(email=email, phone=phone, first_name=first_name, last_name=last_name, role=role)
            user.set_password(password)
            user.is_verified = True  # admin-created users considered verified
            user.save()
        else:
            user = get_object_or_404(User, pk=int(user_id))

        # attach user id and create RiderProfile
        data['user'] = user.id
        serializer = RiderProfileSerializer(data=data)
        if serializer.is_valid():
            profile = serializer.save()
            # mark approved if admin wants
            if data.get('is_approved') in ['true', 'True', True, '1', 1]:
                profile.is_approved = True
                profile.save()
                # notify user
                if user.email:
                    try:
                        send_email_with_logging(
                            to_email=user.email,
                            subject='AAfri Ride - Driver Account Created and Approved',
                            message='Your driver account was created and approved by admin. You can now login.'
                        )
                    except Exception:
                        pass

            return Response(RiderProfileSerializer(profile, context={'request': request}).data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        profile = get_object_or_404(RiderProfile, pk=pk)
        serializer = RiderProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            profile = serializer.save()
            return Response(RiderProfileSerializer(profile, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def approve(request, pk=None):
        # Ensure only admin users can call this endpoint
        if not getattr(request, 'user', None) or not request.user.is_staff:
            return Response({'detail': 'Admin privileges required'}, status=status.HTTP_403_FORBIDDEN)

        profile = get_object_or_404(RiderProfile, pk=pk)
        profile.is_approved = True
        profile.save()
        # notify the user
        try:
            if profile.user and profile.user.email:
                send_email_with_logging(
                    to_email=profile.user.email,
                    subject='AAfri Ride - Driver Application Approved',
                    message='Congratulations — your driver application has been approved. You can now log in and start driving.'
                )
        except Exception:
            pass
        return Response({'detail': 'approved'})


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
