from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'rider', 'origin_address', 'dest_address', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('origin_address', 'dest_address', 'customer__email', 'rider__email')


from .models import DriverLocation


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'lat', 'lng', 'updated_at')
    search_fields = ('driver__email',)
    readonly_fields = ('updated_at',)

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference', 'trip', 'amount', 'status', 'created_at', 'paid_at')
    search_fields = ('reference', 'trip__id')
    readonly_fields = ('created_at', 'paid_at', 'raw_response')
