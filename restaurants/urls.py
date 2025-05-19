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
    path('tables/', views.tables, name='tables'),
    path('tables/add/', views.add_table, name='add_table'),
    path('tables/edit/', views.edit_table, name='edit_table'),
    path('tables/delete/', views.delete_table, name='delete_table'),
    path('tables/generate-qr/<int:table_id>/', views.generate_qr, name='generate_qr'),
    
    path('users/', views.user_management, name='user_management'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:user_id>/update/', views.update_user, name='update_user'),
    path('users/<int:user_id>/deactivate/', views.deactivate_user, name='deactivate_user'),
]