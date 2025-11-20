from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError('User must have an email or phone')
        email = self.normalize_email(email) if email else None
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.create_user(email=email, password=password, **extra_fields)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    CUSTOMER = 'customer'
    RIDER = 'rider'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (RIDER, 'Rider'),
        (ADMIN, 'Admin'),
    ]

    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CUSTOMER)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # Email/Phone verification status

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email or self.phone or f'User-{self.pk}'


class CustomerProfile(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='customer_profile')
    default_payment = models.ForeignKey('payments.PaymentMethod', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'CustomerProfile({self.user})'


class RiderProfile(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='rider_profile')
    vehicle_make = models.CharField(max_length=100, blank=True)
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_plate = models.CharField(max_length=20, blank=True)
    license_document = models.FileField(upload_to='licenses/', null=True, blank=True)
    id_document = models.FileField(upload_to='ids/', null=True, blank=True)
    is_available = models.BooleanField(default=False)

    def __str__(self):
        return f'RiderProfile({self.user})'


class OTP(models.Model):
    METHOD_EMAIL = 'email'
    METHOD_PHONE = 'phone'
    METHOD_CHOICES = [
        (METHOD_EMAIL, 'Email'),
        (METHOD_PHONE, 'Phone'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='otps', null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    code = models.CharField(max_length=8)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default=METHOD_PHONE)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    # Tracks whether this OTP has been sent (email/SMS) and any error details
    sent_at = models.DateTimeField(null=True, blank=True)
    send_result = models.IntegerField(null=True, blank=True)
    send_error = models.TextField(null=True, blank=True)

    @property
    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 300

    def __str__(self):
        contact = self.email if self.method == self.METHOD_EMAIL else self.phone
        return f'OTP({contact or self.user}, method={self.method})'


class Device(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='devices')
    token = models.CharField(max_length=512)
    platform = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Device({self.user}, {self.platform})'
