from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
]