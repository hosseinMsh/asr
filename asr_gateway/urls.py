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
    path("history/", views_pages.history, name="history"),
    path("account/", views_pages.account, name="account"),
    path("asr/", views_pages.asr_ui, name="asr-ui"),

    path("api/", include("asr.urls.api")),
    path("api/auth/", include("asr.urls.auth")),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]
