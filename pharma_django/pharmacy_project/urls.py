from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pharmacy_app.urls')),
    path('api/', include('pharmacy_app.api_urls')),
    path('api/ml/', include('ml_engine.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)