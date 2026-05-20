from django.db import models
from accounts.models import CustomUser
from products.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Pending Farmer Approval'),
        ('confirmed',  'Confirmed by Farmer'),
        ('in_transit', 'In Transit'),
        ('delivered',  'Delivered'),
        ('cancelled',  'Cancelled'),
    ]
    buyer        = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                     limit_choices_to={'role': 'buyer'})
    farmer       = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                     related_name='sold_orders',
                                     limit_choices_to={'role': 'farmer'})
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                    default='pending')
    # ── Shipping address entered by buyer ──────────────────────────────
    shipping_address   = models.CharField(max_length=500, blank=True)
    shipping_wilaya    = models.CharField(max_length=100, blank=True)
    shipping_phone     = models.CharField(max_length=30,  blank=True)
    shipping_notes     = models.TextField(blank=True)
    # ── Shipping price set by transporter ──────────────────────────────
    shipping_price     = models.DecimalField(max_digits=10, decimal_places=2,
                                             null=True, blank=True)
    # ── Buyer approval of shipping price ─────────────────────────────
    APPROVAL_CHOICES = [
        ('pending',  'Awaiting Buyer Approval'),
        ('approved', 'Approved by Buyer'),
        ('rejected', 'Rejected by Buyer'),
    ]
    shipping_approval   = models.CharField(max_length=20, choices=APPROVAL_CHOICES,
                                            default='pending')
    created_at         = models.DateTimeField(auto_now_add=True)

    @property
    def grand_total(self):
        sp = self.shipping_price or 0
        return self.total_amount + sp

    def get_status_display_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class OrderItem(models.Model):
    order          = models.ForeignKey(Order, on_delete=models.CASCADE,
                                       related_name='items')
    product        = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_kg    = models.DecimalField(max_digits=10, decimal_places=2)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)


class Delivery(models.Model):
    STATUS_CHOICES = [
        ('waiting',   'Waiting for Farmer Approval'),
        ('pending',   'Open — Awaiting Transporter'),
        ('assigned',  'Assigned'),
        ('in_transit','In Transit'),
        ('delivered', 'Delivered'),
        ('declined',  'Declined'),
    ]
    order             = models.OneToOneField(Order, on_delete=models.CASCADE,
                                             related_name='delivery')
    transporter       = models.ForeignKey('accounts.CustomUser',
                                          on_delete=models.SET_NULL,
                                          null=True, blank=True,
                                          related_name='deliveries',
                                          limit_choices_to={'role': 'transporter'})
    pickup_location   = models.CharField(max_length=300)
    delivery_location = models.CharField(max_length=300)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                         default='waiting')
    shipping_price    = models.DecimalField(max_digits=10, decimal_places=2,
                                            null=True, blank=True,
                                            help_text="Price set by transporter before accepting")
    assigned_at       = models.DateTimeField(null=True, blank=True)
    delivered_at      = models.DateTimeField(null=True, blank=True)
    notes             = models.TextField(blank=True)

    def __str__(self):
        return f"Delivery #{self.id} for Order #{self.order.id} – {self.status}"

    def best_offer(self):
        """Return the lowest-price accepted offer, or None."""
        return self.offers.order_by('proposed_price').first()


class DeliveryOffer(models.Model):
    """
    An offer submitted by a transporter for a pending delivery.
    Multiple transporters can submit offers; the buyer sees only the cheapest one.
    """
    STATUS_CHOICES = [
        ('pending',  'Pending Buyer Approval'),
        ('accepted', 'Accepted by Buyer'),
        ('rejected', 'Rejected by Buyer'),
    ]
    delivery        = models.ForeignKey(Delivery, on_delete=models.CASCADE,
                                        related_name='offers')
    transporter     = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE,
                                        related_name='delivery_offers',
                                        limit_choices_to={'role': 'transporter'})
    proposed_price  = models.DecimalField(max_digits=10, decimal_places=2)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                       default='pending')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One offer per transporter per delivery
        unique_together = ('delivery', 'transporter')
        ordering = ['proposed_price']

    def __str__(self):
        return f"Offer by {self.transporter} for Delivery #{self.delivery.id} – {self.proposed_price} DA"
