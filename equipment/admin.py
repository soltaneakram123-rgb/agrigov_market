from django.contrib import admin
from .models import Equipment, EquipmentRequest


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category', 'quantity_available', 'available_count', 'wilaya', 'is_active')
    list_filter   = ('category', 'is_active', 'wilaya')
    search_fields = ('name', 'description')


@admin.register(EquipmentRequest)
class EquipmentRequestAdmin(admin.ModelAdmin):
    list_display  = ('farmer', 'equipment', 'start_date', 'end_date', 'status', 'created_at')
    list_filter   = ('status', 'equipment__category')
    search_fields = ('farmer__username', 'equipment__name')
