from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import CustomerProfile, RiderProfile, OTP, Device

User = get_user_model()
class RiderProfileInline(admin.StackedInline):
    model = RiderProfile
    can_delete = False
    verbose_name = 'Rider Profile'
    fk_name = 'user'
    extra = 0


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'phone', 'role', 'is_staff')
    inlines = [RiderProfileInline]

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_payment')

@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_make', 'vehicle_model', 'vehicle_plate', 'is_available', 'is_approved', 'submitted_at')
    list_filter = ('is_approved', 'is_available', 'vehicle_make')
    search_fields = ('user__email', 'user__phone', 'vehicle_plate', 'license_number')

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('phone', 'code', 'verified', 'created_at')

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'created_at')
