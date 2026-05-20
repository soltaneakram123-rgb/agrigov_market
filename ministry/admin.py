from django.contrib import admin
from django.contrib import messages
from .models import OfficialPrice, Policy, Complaint, SeasonalPriceRange


@admin.register(OfficialPrice)
class OfficialPriceAdmin(admin.ModelAdmin):
    list_display = ['category', 'price_per_kg', 'valid_from', 'valid_to']
    list_filter = ['category']
    ordering = ['-valid_from']


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'created_at', 'updated_at']
    list_filter = ['status']
    search_fields = ['title']
    ordering = ['-created_at']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['id', 'from_user', 'subject', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['subject', 'from_user__username']
    ordering = ['-created_at']


@admin.register(SeasonalPriceRange)
class SeasonalPriceRangeAdmin(admin.ModelAdmin):
    list_display = ['product_type', 'season', 'min_price', 'max_price', 'updated_at']
    list_filter = ['season', 'product_type']
    ordering = ['product_type__name', 'season']