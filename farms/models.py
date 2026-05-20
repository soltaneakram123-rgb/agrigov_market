from django.db import models
from accounts.models import CustomUser

class Farm(models.Model):
    farmer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    size_hectares = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name