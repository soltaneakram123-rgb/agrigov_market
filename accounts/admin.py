from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from .models import CustomUser, FarmerProfile


class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_approved', 'is_active', 'is_verified', 'date_joined']
    list_filter = ['role', 'is_approved', 'is_active', 'is_verified']
    list_editable = ['is_approved', 'is_active']
    actions = ['approve_users', 'reject_users']

    fieldsets = UserAdmin.fieldsets + (
        ('AgriGov Fields', {
            'fields': ('role', 'phone', 'is_verified', 'is_approved')
        }),
    )

    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True, is_active=True)
        self.message_user(request, f'{updated} user(s) approved and activated ✅', messages.SUCCESS)
    approve_users.short_description = '✅ Approve selected users (allow login)'

    def reject_users(self, request, queryset):
        updated = queryset.update(is_approved=False, is_active=False)
        self.message_user(request, f'{updated} user(s) rejected ❌', messages.WARNING)
    reject_users.short_description = '❌ Reject selected users (block login)'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(FarmerProfile)
