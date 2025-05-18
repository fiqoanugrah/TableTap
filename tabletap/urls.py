from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('restaurant/', include('restaurants.urls', namespace='restaurants')),
    path('staff/', include('orders.urls', namespace='orders')),
    path('menu/', include('customer.urls', namespace='customer')),
    path('', RedirectView.as_view(url='/accounts/login/'), name='home'),  # Redirect ke login page
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)