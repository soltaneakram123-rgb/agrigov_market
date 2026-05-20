from django.db import models
from farms.models import Farm


class ProductType(models.Model):
    """Predefined catalogue — farmer picks from this list, cannot invent names."""
    name = models.CharField(max_length=100, unique=True)
    name_ar = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=50, choices=[
        ('vegetables', 'Vegetables'),
        ('fruits',     'Fruits'),
        ('grains',     'Grains & Cereals'),
        ('herbs',      'Herbs & Spices'),
        ('legumes',    'Legumes'),
        ('dairy',      'Dairy'),
        ('other',      'Other'),
    ], default='vegetables')
    image_url = models.URLField(blank=True)

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT)
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT,
                                     null=True, blank=True,
                                     related_name='products')
    name = models.CharField(max_length=200)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    quality = models.CharField(max_length=20, choices=[
        ('A', 'Premium'), ('B', 'Standard'), ('C', 'Basic')
    ])
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.farm.name}"

    @property
    def image(self):
        """Return the product image — from ProductType catalogue if available."""
        if self.product_type and self.product_type.image_url:
            return self.product_type.image_url
        return "https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=400&auto=format"
