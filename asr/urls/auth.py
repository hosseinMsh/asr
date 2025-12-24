from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from asr.views.auth import CustomTokenObtainPairView, AnonTokenView, RegisterView, LogoutView

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("login/", CustomTokenObtainPairView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("anon/token/", AnonTokenView.as_view()),
    path("register/", RegisterView.as_view()),
]
