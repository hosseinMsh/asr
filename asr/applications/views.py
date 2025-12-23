from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema, OpenApiExample

from asr.applications import services
from asr.accounts.authentication import StrictJWTAuthentication
from asr.applications.serializers import (
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationDeactivateSerializer,
    ApplicationListResponseSerializer,
    APITokenSerializer,
    APITokenCreateSerializer,
    APITokenCreateResponseSerializer,
    APITokenRevokeSerializer,
    APITokenListResponseSerializer,
    ApplicationUsageResponseSerializer,
)
from asr.usage.services import usage_summary_for_application
from asr.models import Application


def _get_application_for_user(user, app_id: str) -> Application:
    app = Application.objects.filter(id=app_id, user=user).first()
    if not app:
        raise NotFound("Application not found.")
    return app


class ApplicationListCreateView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["applications"],
        auth=[{"JWTAuth": []}],
        responses={200: ApplicationListResponseSerializer},
    )
    def get(self, request):
        apps = services.list_applications(request.user)
        serializer = ApplicationSerializer(apps, many=True)
        return Response(ApplicationListResponseSerializer({"results": serializer.data}).data)

    @extend_schema(
        tags=["applications"],
        auth=[{"JWTAuth": []}],
        request=ApplicationCreateSerializer,
        responses={201: ApplicationSerializer},
        examples=[
            OpenApiExample(
                "Create application",
                value={"name": "My App"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data["name"].strip()
        if not name:
            raise ValidationError("Application name is required.")
        app = services.create_application(request.user, name)
        return Response(ApplicationSerializer(app).data, status=201)


class ApplicationDeactivateView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["applications"],
        auth=[{"JWTAuth": []}],
        responses={200: ApplicationDeactivateSerializer},
    )
    def post(self, request, app_id: str):
        app = _get_application_for_user(request.user, app_id)
        app = services.deactivate_application(app)
        return Response(ApplicationDeactivateSerializer(app).data)


class APITokenListCreateView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["applications"],
        auth=[{"JWTAuth": []}],
        responses={200: APITokenListResponseSerializer},
    )
    def get(self, request, app_id: str):
        app = _get_application_for_user(request.user, app_id)
        tokens = services.list_tokens(app)
        serializer = APITokenSerializer(tokens, many=True)
        return Response(APITokenListResponseSerializer({"results": serializer.data}).data)

    @extend_schema(
        tags=["applications"],
        auth=[{"JWTAuth": []}],
        request=APITokenCreateSerializer,
        responses={201: APITokenCreateResponseSerializer},
        examples=[
            OpenApiExample(
                "Create API token",
                value={"name": "CI token"},
                request_only=True,
            ),
            OpenApiExample(
                "Token response",
                value={
                    "id": "uuid",
                    "name": "CI token",
                    "token": "api_token_value",
                    "token_last_four": "abcd",
                    "created_at": "2025-01-01T00:00:00Z",
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request, app_id: str):
        app = _get_application_for_user(request.user, app_id)
        serializer = APITokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data["name"].strip()
        if not name:
            raise ValidationError("Token name is required.")
        api_token, raw_token = services.create_token(app, name)
        response_payload = APITokenCreateResponseSerializer(
            {
                "id": api_token.id,
                "name": api_token.name,
                "token": raw_token,
                "token_last_four": api_token.token_last_four,
                "created_at": api_token.created_at,
            }
        )
        return Response(response_payload.data, status=201)


class APITokenRevokeView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["applications"],
        auth=[{"JWTAuth": []}],
        responses={200: APITokenRevokeSerializer},
    )
    def post(self, request, app_id: str, token_id: str):
        app = _get_application_for_user(request.user, app_id)
        token = app.tokens.filter(id=token_id).first()
        if not token:
            raise NotFound("Token not found.")
        token = services.revoke_token(token)
        return Response(APITokenRevokeSerializer(token).data)


class ApplicationUsageView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["usage"],
        auth=[{"JWTAuth": []}],
        responses={200: ApplicationUsageResponseSerializer},
    )
    def get(self, request, app_id: str):
        app = _get_application_for_user(request.user, app_id)
        summary = usage_summary_for_application(app)
        payload = {"application_id": app.id, **summary}
        serializer = ApplicationUsageResponseSerializer(payload)
        return Response(serializer.data)
