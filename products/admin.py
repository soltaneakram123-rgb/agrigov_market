from django.contrib import admin
from .models import Product, ProductCategory, ProductType


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'name_ar', 'category', 'image_url')
    list_filter   = ('category',)
    search_fields = ('name', 'name_ar')
    ordering      = ('category', 'name')


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('name', 'product_type', 'farm', 'price_per_kg', 'quantity_kg', 'is_available')
    list_filter   = ('is_available', 'quality', 'category')
    search_fields = ('name', 'farm__name')
