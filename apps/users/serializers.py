from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CustomerProfile, RiderProfile, Device, OTP

User = get_user_model()


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from django.conf import settings


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend TokenObtainPairSerializer to allow role-based access token lifetime.

    If a user is staff/superuser or has role 'admin', we will issue an access token
    with a longer TTL defined by `ADMIN_ACCESS_TOKEN_LIFETIME_SECONDS` in settings.
    """
    def validate(self, attrs):
        # Perform the standard validation to authenticate the user
        data = super().validate(attrs)

        # Build fresh tokens so we can customise claims
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        # If user is admin/staff, extend access token expiry if configured
        is_admin = getattr(self.user, 'is_staff', False) or getattr(self.user, 'is_superuser', False) or getattr(self.user, 'role', '') == 'admin'
        if is_admin:
            admin_secs = getattr(settings, 'ADMIN_ACCESS_TOKEN_LIFETIME_SECONDS', None)
            if admin_secs:
                exp = datetime.utcnow() + timedelta(seconds=int(admin_secs))
                access['exp'] = int(exp.replace(tzinfo=None).timestamp())

        data['refresh'] = str(refresh)
        data['access'] = str(access)
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=False)
    # Make verification_method optional: default to 'phone' or infer from provided fields
    verification_method = serializers.ChoiceField(choices=['email', 'phone'], required=False, default='phone', write_only=True)

    class Meta:
        model = User
        fields = ['email', 'phone', 'password', 'password2', 'first_name', 'last_name', 'role', 'verification_method']

    def validate(self, data):
        password = data.get('password')
        password2 = data.get('password2', password)  # Use password as fallback if password2 not provided
        if password != password2:
            raise serializers.ValidationError('Passwords do not match')
        
        verification_method = data.get('verification_method')
        # If verification_method was not provided, infer it from fields: prefer email if present
        if not verification_method:
            if data.get('email'):
                verification_method = 'email'
                data['verification_method'] = 'email'
            elif data.get('phone'):
                verification_method = 'phone'
                data['verification_method'] = 'phone'
        if verification_method == 'email' and not data.get('email'):
            raise serializers.ValidationError('Email is required when choosing email verification')
        if verification_method == 'phone' and not data.get('phone'):
            raise serializers.ValidationError('Phone is required when choosing phone verification')
        
        return data

    def create(self, validated_data):
        validated_data.pop('password2', None)
        verification_method = validated_data.pop('verification_method', 'phone')  # Extract but keep for OTP
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        # create profiles
        if user.role == User.CUSTOMER:
            CustomerProfile.objects.get_or_create(user=user)
        elif user.role == User.RIDER:
            RiderProfile.objects.get_or_create(user=user)
        
        # Store verification_method in user object for view to access via serializer
        user._verification_method = verification_method
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']


class DeviceSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    
    class Meta:
        model = Device
        fields = ['id', 'user', 'user_email', 'token', 'platform', 'created_at']
        read_only_fields = ['id', 'user', 'user_email', 'created_at']


class OTPSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    is_verified = serializers.BooleanField(source='verified', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = OTP
        fields = [
            'id', 'user', 'user_email', 'email', 'phone', 'code', 
            'method', 'is_verified', 'is_expired', 'created_at',
            'sent_at', 'send_result', 'send_error'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'created_at', 'is_verified', 'is_expired']
