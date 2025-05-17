from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('menu/categories/', views.menu_categories, name='menu_categories'),
    path('menu/items/', views.menu_items, name='menu_items'),
    path('tables/', views.tables, name='tables'),
    path('generate-qr/<int:table_id>/', views.generate_qr, name='generate_qr'),
]