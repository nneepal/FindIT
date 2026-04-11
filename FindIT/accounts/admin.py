from django.contrib import admin
from .models import PasswordResetRequest, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address', 'date_of_birth')
    search_fields = ('user__username', 'user__email', 'phone_number')


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'sent_successfully', 'ip_address', 'requested_at')
    search_fields = ('email', 'user__username', 'user__email', 'ip_address')
    list_filter = ('sent_successfully', 'requested_at')
    readonly_fields = ('email', 'user', 'sent_successfully', 'ip_address', 'user_agent', 'requested_at')
