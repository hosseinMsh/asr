from django.urls import path
from asr.views.auth import (
    AnonTokenView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    LogoutView,
    RegisterView,
)

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view()),
    path("token/refresh/", CustomTokenRefreshView.as_view()),
    path("login/", CustomTokenObtainPairView.as_view()),
    path("refresh/", CustomTokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("anon/token/", AnonTokenView.as_view()),
    path("register/", RegisterView.as_view()),
]
