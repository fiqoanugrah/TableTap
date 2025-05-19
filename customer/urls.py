"""
URLs for the customer app with proper names to match templates
"""
from django.urls import path
from . import views

# Register the 'customer' namespace
app_name = 'customer'

urlpatterns = [
    # Change this to match template references
    path('<int:restaurant_id>/<int:table_id>/', views.menu_view, name='menu_view'),
    
    # Cart views
    path('cart/<int:restaurant_id>/<int:table_id>/', views.cart_view, name='cart'),
    
    # Add to cart
    path('add-to-cart/<int:restaurant_id>/<int:table_id>/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    
    # Rename this to match template reference - change from 'update_cart' to 'update_cart_item'
    path('update-cart/<int:restaurant_id>/<int:table_id>/<int:item_id>/', views.update_cart, name='update_cart_item'),
    
    # Order submission
    path('place-order/<int:restaurant_id>/<int:table_id>/', views.place_order, name='place_order'),
    
    # Order status & confirmation
    path('order-status/<int:order_id>/', views.order_status, name='order_status'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    # QR code table entry
    path('table/<str:table_code>/', views.table_entry, name='table_entry'),
    path('remove-from-cart/<int:restaurant_id>/<int:table_id>/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
]