from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Admin Panel
    path('admin/', admin.site.urls),

    # 2. Aapka Main App (Campus)
    path('', include('campus.urls')), 
]

# 3. Media aur Static Files (Photos/QR Code ke liye)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)