# restaurants/models.py
from django.db import models
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import base64

class Restaurant(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_restaurants')
    staff = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='staffed_restaurants', blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    logo = models.TextField(blank=True, null=True)  # Base64 encoded image
    operating_hours = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, 
                             choices=[('active', 'Active'), ('inactive', 'Inactive')],
                             default='active')
    
    def __str__(self):
        return self.name
    
    def save_logo_base64(self, image_file):
        """Convert uploaded image to base64 and save to model"""
        if image_file:
            with image_file.open() as f:
                image_data = f.read()
                self.logo = base64.b64encode(image_data).decode('utf-8')
                self.save()

class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    table_number = models.IntegerField()
    seats = models.IntegerField(default=2)
    qr_code_url = models.CharField(max_length=255, blank=True)
    qr_code = models.TextField(blank=True, null=True)  # Base64 encoded QR code
    status = models.CharField(max_length=20, 
                             choices=[('available', 'Available'), ('occupied', 'Occupied')],
                             default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('restaurant', 'table_number')
    
    def __str__(self):
        return f"{self.restaurant.name} - Table {self.table_number}"
    
    def generate_qr_code(self, request=None):
        """Generate QR code and save as base64 string"""
        if request:
            base_url = f"{request.scheme}://{request.get_host()}"
        else:
            base_url = "https://tabletap.vercel.app"  # Fallback URL
            
        url = f"{base_url}/menu/{self.restaurant.id}/{self.id}/"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        self.qr_code = qr_code_base64
        self.qr_code_url = url
        self.save()
        return self.qr_code

class MenuCategory(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Menu Categories'
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.TextField(blank=True, null=True)  # Base64 encoded image
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def save_image_base64(self, image_file):
        """Convert uploaded image to base64 and save to model"""
        if image_file:
            with image_file.open() as f:
                image_data = f.read()
                self.image = base64.b64encode(image_data).decode('utf-8')
                self.save()