from django.contrib import admin
from .models import Order, OrderItem, Delivery, DeliveryOffer


@admin.register(DeliveryOffer)
class DeliveryOfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'delivery', 'transporter', 'proposed_price', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'transporter', 'status', 'shipping_price')


admin.site.register(Order)
admin.site.register(OrderItem)

