from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('farmer', 'Farmer (Producer)'),
        ('buyer', 'Buyer'),
        ('transporter', 'Transporter'),
        ('ministry', 'Ministry of Agriculture'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='buyer')
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False, help_text="Must be approved by admin before login is allowed")
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True
    )
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class FarmerProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='farmer_profile')
    farm_name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    size_hectares = models.DecimalField(max_digits=8, decimal_places=2, default=1.0)

class TransporterProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='transporter_profile',
    )
    vehicle_type = models.CharField(max_length=100)
    capacity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    service_areas = models.TextField(
        help_text="Comma-separated list of wilayas / regions"
    )
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} – {self.vehicle_type}"
    
