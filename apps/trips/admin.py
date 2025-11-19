from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'rider', 'origin_address', 'dest_address', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('origin_address', 'dest_address', 'customer__email', 'rider__email')
