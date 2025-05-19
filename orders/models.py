# orders/models.py
from django.db import models
from django.utils import timezone
from restaurants.models import Restaurant, Table
from django.conf import settings

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_instructions = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)  # New field to track when order is completed
    
    def __str__(self):
        return f"Order #{self.id} - {self.table.table_number} - {self.get_status_display()}"
    
    def get_total_items(self):
        return self.items.aggregate(models.Sum('quantity'))['quantity__sum'] or 0
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Harga pada saat pemesanan
    notes = models.TextField(blank=True, null=True)  # Instruksi khusus untuk item
    
    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"
    
    def get_total(self):
        return self.price * self.quantity