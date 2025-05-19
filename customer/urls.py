"""
URLs for the customer app with proper names to match templates
"""
from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    # Menu view
    path('<int:restaurant_id>/<int:table_id>/', views.menu_view, name='menu_view'),

    # Cart views
    path('cart/<int:restaurant_id>/<int:table_id>/', views.cart_view, name='cart'),

    # Add to cart (support both /add-to-cart/... and /menu/add-to-cart/...)
    path('add-to-cart/<int:restaurant_id>/<int:table_id>/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('menu/add-to-cart/<int:restaurant_id>/<int:table_id>/<int:item_id>/', views.add_to_cart),

    # Update cart item
    path('update-cart/<int:restaurant_id>/<int:table_id>/<int:item_id>/', views.update_cart, name='update_cart_item'),

    # Remove from cart
    path('remove-from-cart/<int:restaurant_id>/<int:table_id>/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Order submission
    path('place-order/<int:restaurant_id>/<int:table_id>/', views.place_order, name='place_order'),

    # Order status & confirmation
    path('order-status/<int:order_id>/', views.order_status, name='order_status'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

    # QR code table entry
    path('table/<str:table_code>/', views.table_entry, name='table_entry'),
]