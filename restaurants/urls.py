from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('menu/categories/', views.menu_categories, name='menu_categories'),
    path('menu/items/', views.menu_items, name='menu_items'),
    path('tables/', views.tables, name='tables'),
    path('generate-qr/<int:table_id>/', views.generate_qr, name='generate_qr'),
    path('create/', views.create_restaurant, name='create_restaurant'),
    path('menu/categories/add/', views.add_category, name='add_category'),
    path('menu/categories/edit/', views.edit_category, name='edit_category'),
    path('menu/categories/delete/', views.delete_category, name='delete_category'),
    path('menu/items/add/', views.add_menu_item, name='add_menu_item'),
    path('menu/items/edit/', views.edit_menu_item, name='edit_menu_item'),
    path('menu/items/delete/', views.delete_menu_item, name='delete_menu_item'),
]