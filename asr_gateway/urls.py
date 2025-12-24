from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("asr.urls.pages")),

    path("api/", include("asr.urls.api")),
    path("api/v1/", include("asr.urls.v1")),
    path("api/auth/", include("asr.urls.auth")),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
