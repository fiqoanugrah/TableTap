from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('<int:restaurant_id>/<int:table_id>/', views.menu, name='menu'),
    path('cart/<int:restaurant_id>/<int:table_id>/', views.cart, name='cart'),
    path('add-to-cart/<int:restaurant_id>/<int:table_id>/<int:menu_item_id>/', views.add_to_cart, name='add_to_cart'),
    path('place-order/<int:restaurant_id>/<int:table_id>/', views.place_order, name='place_order'),
    path('order-status/<int:order_id>/', views.order_status, name='order_status'),
]