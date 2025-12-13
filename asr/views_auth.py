from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken
from datetime import timedelta
from .jwt import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class AnonTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        if not request.session.session_key:
            request.session.create()
        sk = request.session.session_key
        token = AccessToken()
        token.set_exp(lifetime=timedelta(minutes=10))
        token["plan"] = "anon"
        token["sid"] = sk
        token["uid"] = 0
        token["tv"] = 0
        return Response({"access": str(token), "plan": "anon", "expires_in_sec": int(token.lifetime.total_seconds())})

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = (request.data.get("password") or "").strip()
        if not username or not password:
            return Response({"detail":"username/password required"}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({"detail":"username already exists"}, status=400)
        user = User.objects.create_user(username=username, password=password)
        return Response({"id": user.id, "username": user.username})
