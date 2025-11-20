from django.contrib import admin
from .models import ErrorLog


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'severity',
        'error_type',
        'endpoint',
        'status_code',
        'user_email',
        'resolved',
        'created_at',
    ]
    list_filter = [
        'severity',
        'error_type',
        'resolved',
        'created_at',
    ]
    search_fields = [
        'title',
        'message',
        'endpoint',
        'user_email',
    ]
    readonly_fields = [
        'id',
        'traceback',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Error Information', {
            'fields': ('id', 'title', 'message', 'error_type', 'severity')
        }),
        ('Request Details', {
            'fields': ('endpoint', 'method', 'status_code', 'user_email')
        }),
        ('Data', {
            'fields': ('request_data', 'response_data'),
            'classes': ('collapse',)
        }),
        ('Traceback', {
            'fields': ('traceback',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('resolved', 'created_at', 'updated_at')
        }),
    )
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
