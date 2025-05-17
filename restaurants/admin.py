from django.contrib import admin
from .models import Restaurant, Table, MenuCategory, MenuItem

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'owner__username')

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'table_number', 'seats', 'status')
    list_filter = ('status', 'restaurant')
    search_fields = ('restaurant__name', 'table_number')

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'display_order', 'active')
    list_filter = ('active', 'restaurant')
    search_fields = ('name', 'restaurant__name')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('is_available', 'category__restaurant')
    search_fields = ('name', 'category__name', 'category__restaurant__name')