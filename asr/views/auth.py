from datetime import timedelta

from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from asr import schemas
from asr.auth.jwt import CustomTokenObtainPairSerializer
from asr.utils.errors import error_response
from asr.utils.auth import HumanJWTAuthentication, HumanTokenRequired


@extend_schema(
    tags=["Auth"],
    summary="Obtain access and refresh tokens",
    responses=CustomTokenObtainPairSerializer,
)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["Auth"],
    summary="Refresh access token",
)
class CustomTokenRefreshView(TokenRefreshView):
    pass

class AnonTokenView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Obtain anonymous short-lived token",
        responses=schemas.TokenResponseSerializer,
    )
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

    @extend_schema(
        tags=["Auth"],
        summary="Register a new user",
        request=schemas.RegisterRequestSerializer,
        responses={
            201: schemas.RegisterResponseSerializer,
            400: schemas.ErrorResponseSerializer,
        },
    )
    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = (request.data.get("password") or "").strip()
        if not username or not password:
            return error_response("INVALID_CREDENTIALS", "Username and password are required.", status_code=400)
        if User.objects.filter(username=username).exists():
            return error_response("USERNAME_TAKEN", "Username already exists.", status_code=400)
        user = User.objects.create_user(username=username, password=password)
        return Response({"id": user.id, "username": user.username}, status=201)


class LogoutView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired, IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Log out user",
        responses={204: None},
    )
    def post(self, request):
        return Response(status=204)
