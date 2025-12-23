from django.contrib import admin
from django.urls import path, include
from asr.views import pages as views_pages
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views_pages.landing, name="landing"),
    path("test/", views_pages.test_page, name="test"),
    path("login/", views_pages.login_page, name="login"),
    path("register/", views_pages.register_page, name="register"),
    path("pricing/", views_pages.pricing, name="pricing"),
    path("dashboard/", views_pages.dashboard, name="dashboard"),
    path("applications/", views_pages.applications, name="applications"),
    path("applications/<str:app_id>/", views_pages.application_detail, name="application-detail"),
    path("usage/", views_pages.usage, name="usage"),
    path("docs/", views_pages.docs, name="docs"),
    path("recorder/", views_pages.recorder, name="recorder"),
    path("history/", views_pages.history, name="history"),
    path("account/", views_pages.account, name="account"),
    path("asr/", views_pages.asr_ui, name="asr-ui"),

    path("api/", include("asr.urls.api")),
    path("api/", include("asr.urls.user_api")),
    path("api/auth/", include("asr.urls.auth")),
    path("api/apps/", include("asr.urls.apps")),
    path("api/v1/", include("asr.asr_api.v1_urls")),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
