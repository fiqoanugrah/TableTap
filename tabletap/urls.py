"""
Main URL Configuration for the TableTap project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import landing_view, home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_view, name='landing'),
    path('home/', home_view, name='home'),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('restaurant/', include('restaurants.urls')),
    path('orders/', include('orders.urls')),
    path('menu/', include('customer.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)