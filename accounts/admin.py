from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PasswordResetToken

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'hourly_rate', 'is_active')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'address', 'profile_picture', 'hourly_rate')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'address', 'hourly_rate')
        }),
    )
    readonly_fields = []

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'token')
    readonly_fields = ('created_at',)
