from django.db import models
from accounts.models import CustomUser


class Equipment(models.Model):
    CATEGORY_CHOICES = [
        ('tractor',    'Tractor'),
        ('harvester',  'Harvester'),
        ('plow',       'Plow'),
        ('seeder',     'Seeder'),
        ('sprayer',    'Sprayer'),
        ('irrigation', 'Irrigation System'),
        ('baler',      'Baler'),
        ('other',      'Other'),
    ]

    name                = models.CharField(max_length=200)
    name_ar             = models.CharField(max_length=200, blank=True, help_text="Arabic name (optional)")
    category            = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    description         = models.TextField(blank=True)
    image_url           = models.URLField(blank=True)
    quantity_available  = models.PositiveIntegerField(default=1)
    price_per_day       = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                              help_text="Rental price per day (DA)")
    wilaya              = models.CharField(max_length=100, blank=True, help_text="Wilaya where the equipment is available")
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.get_category_display()} — {self.name}"

    @property
    def available_count(self):
        approved = self.requests.filter(status='approved').count()
        return max(self.quantity_available - approved, 0)


class EquipmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
    ]

    farmer      = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                    related_name='equipment_requests',
                                    limit_choices_to={'role': 'farmer'})
    equipment   = models.ForeignKey(Equipment, on_delete=models.CASCADE,
                                    related_name='requests')
    start_date  = models.DateField()
    end_date    = models.DateField()
    reason      = models.TextField(help_text="Reason for requesting the equipment")
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note  = models.TextField(blank=True, help_text="Admin note on approval or rejection")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request by {self.farmer.username} — {self.equipment.name} ({self.get_status_display()})"
