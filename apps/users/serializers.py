from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CustomerProfile, RiderProfile, Device

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['email', 'phone', 'password', 'password2', 'first_name', 'last_name', 'role']

    def validate(self, data):
        password = data.get('password')
        password2 = data.get('password2', password)  # Use password as fallback if password2 not provided
        if password != password2:
            raise serializers.ValidationError('Passwords do not match')
        return data

    def create(self, validated_data):
        validated_data.pop('password2', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        # create profiles
        if user.role == User.CUSTOMER:
            CustomerProfile.objects.get_or_create(user=user)
        elif user.role == User.RIDER:
            RiderProfile.objects.get_or_create(user=user)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'token', 'platform', 'created_at']
