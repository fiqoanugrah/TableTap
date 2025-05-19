from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('list/', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/update-status/', views.update_status, name='update_status'),
]