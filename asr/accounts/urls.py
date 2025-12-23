from django.urls import path
from asr.accounts.views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    AnonTokenView,
    RegisterView,
)

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view()),
    path("token/refresh/", CustomTokenRefreshView.as_view()),
    path("anon/token/", AnonTokenView.as_view()),
    path("register/", RegisterView.as_view()),
]
