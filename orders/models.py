from django.db import models
from restaurants.models import Restaurant, Table, MenuItem
from django.utils import timezone

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready to Serve'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    completion_time = models.DateTimeField(null=True, blank=True)
    special_instructions = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    
    def __str__(self):
        return f"Order #{self.id} - {self.table}"
    
    def save(self, *args, **kwargs):
        # Update timestamps based on status changes
        if self.status == 'preparing' and not self.accepted_at:
            self.accepted_at = timezone.now()
        elif self.status == 'ready' and not self.ready_at:
            self.ready_at = timezone.now()
        elif self.status == 'completed' and not self.completion_time:
            self.completion_time = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        return sum(item.price * item.quantity for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)  # Price at time of order
    notes = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"
    
    @property
    def get_total(self):
        return self.price * self.quantity