# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from django.views.generic import RedirectView

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     # path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
#     # path('', include('pharmacy_app.urls')),
#     # path('api/', include('pharmacy_app.api_urls')),
#     # path('api/ml/', include('ml_engine.urls')),
#     path('', include('pharmacy_app.urls')),
#     path('api/', include('pharmacy_app.api_urls')),
#     path('api/ml/', include('ml_engine.urls')),

# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('pharma_django.pharmacy_app.urls')),
    path('api/', include('pharma_django.pharmacy_app.api_urls')),
    path('api/ml/', include('pharma_django.ml_engine.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)