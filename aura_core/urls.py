"""
AURA STAGE // LUMINA STUDIO — Root URL Configuration
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "AURA STAGE // Lumina Studio Admin"
admin.site.site_title = "AURA STAGE Console"
admin.site.index_title = "Spatial Event Operations"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("studio.urls")),
]

# Serve uploaded room photographs straight from MEDIA_ROOT during dev.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
