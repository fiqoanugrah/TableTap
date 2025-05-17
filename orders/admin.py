from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'restaurant', 'table', 'status', 'created_at', 'total_amount')
    list_filter = ('status', 'restaurant')
    search_fields = ('id', 'restaurant__name', 'table__table_number')
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'price')
    list_filter = ('order__restaurant',)
    search_fields = ('order__id', 'menu_item__name')