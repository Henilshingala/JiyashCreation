from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import RedirectView

def favicon_view(request):
    return HttpResponse(status=204)  # No content

urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', favicon_view),
    path('', include('app.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)