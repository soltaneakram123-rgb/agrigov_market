from django.db import models
from products.models import ProductCategory, ProductType
from django.utils import timezone


SEASON_CHOICES = [
    ('spring', 'Spring  (Mar-May)'),
    ('summer', 'Summer  (Jun-Aug)'),
    ('autumn', 'Autumn  (Sep-Nov)'),
    ('winter', 'Winter  (Dec-Feb)'),
]

SEASON_MONTHS = {
    'spring': [3, 4, 5],
    'summer': [6, 7, 8],
    'autumn': [9, 10, 11],
    'winter': [12, 1, 2],
}


def current_season():
    month = timezone.now().month
    for season, months in SEASON_MONTHS.items():
        if month in months:
            return season
    return 'summer'


class SeasonalPriceRange(models.Model):
    product_type = models.ForeignKey(
        ProductType, on_delete=models.CASCADE,
        related_name='price_ranges'
    )
    season = models.CharField(max_length=10, choices=SEASON_CHOICES)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product_type', 'season')
        ordering = ['product_type__name', 'season']

    def __str__(self):
        return f"{self.product_type.name} - {self.get_season_display()} [{self.min_price}-{self.max_price} DA]"


class OfficialPrice(models.Model):
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField()

    def __str__(self):
        return f"{self.category.name} - {self.price_per_kg} DA"


class Policy(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]
    title = models.CharField(max_length=300)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Policies"


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_review', 'In Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    from_user = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='complaints_filed'
    )
    subject = models.CharField(max_length=300)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolution_note = models.TextField(blank=True)

    def __str__(self):
        return f"#{self.id} - {self.subject}"