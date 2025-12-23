from datetime import timedelta

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from asr.accounts.serializers import (
    CustomTokenObtainPairSerializer,
    AnonTokenResponseSerializer,
    RegisterResponseSerializer,
)
from asr.accounts.authentication import StrictJWTAuthentication
from asr.common.errors import error_response


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        tags=["auth"],
        auth=[],
        responses={200: OpenApiResponse(description="JWT access and refresh tokens")},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=["auth"],
        auth=[],
        responses={200: OpenApiResponse(description="JWT refresh response")},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AnonTokenView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        auth=[],
        responses={200: AnonTokenResponseSerializer},
        examples=[
            OpenApiExample(
                "Anon token response",
                value={"access": "jwt-token", "plan": "anon", "expires_in_sec": 600},
            )
        ],
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
        return Response(
            {"access": str(token), "plan": "anon", "expires_in_sec": int(token.lifetime.total_seconds())}
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        auth=[],
        request=RegisterSerializer,
        responses={200: RegisterResponseSerializer},
        examples=[
            OpenApiExample(
                "Register response",
                value={"id": 1, "username": "demo"},
            )
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"].strip()
        password = serializer.validated_data["password"].strip()
        if not username or not password:
            return error_response("INVALID_CREDENTIALS", "Username and password are required.", status_code=400)
        if User.objects.filter(username=username).exists():
            return error_response("USERNAME_TAKEN", "Username already exists.", status_code=400)
        user = User.objects.create_user(username=username, password=password)
        return Response({"id": user.id, "username": user.username})


class LogoutView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        auth=[{"JWTAuth": []}],
        responses={204: OpenApiResponse(description="Logged out")},
    )
    def post(self, request):
        return Response(status=204)
