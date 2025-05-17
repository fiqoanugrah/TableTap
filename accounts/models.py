from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin/Owner'),
        ('staff', 'Staff'),
        ('customer', 'Customer'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    def is_restaurant_owner(self):
        return self.role == 'admin'
    
    def is_staff_member(self):
        return self.role == 'staff'