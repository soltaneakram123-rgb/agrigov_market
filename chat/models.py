from django.db import models
from accounts.models import CustomUser
from orders.models import Order


class Message(models.Model):
    order     = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='messages')
    sender    = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    body      = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[Order #{self.order_id}] {self.sender.username}: {self.body[:40]}"
