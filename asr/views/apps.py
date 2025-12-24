import secrets

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from asr.models import ApiToken, Application
from asr.utils.auth import HumanJWTAuthentication, HumanTokenRequired, hash_api_token
from asr.utils.errors import error_response


def _get_application_for_user(user, app_id):
    app = Application.objects.filter(id=app_id, owner=user).first()
    if not app:
        raise PermissionDenied("Application not found.")
    return app


class ApplicationListCreateView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired, IsAuthenticated]

    def get(self, request):
        apps = Application.objects.filter(owner=request.user).order_by("-created_at")
        return Response([
            {"id": str(app.id), "name": app.name, "created_at": app.created_at.isoformat()}
            for app in apps
        ])

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            return error_response("INVALID_NAME", "Application name is required.", status_code=400)
        app = Application.objects.create(owner=request.user, name=name)
        return Response({"id": str(app.id), "name": app.name, "created_at": app.created_at.isoformat()}, status=201)


class ApplicationDetailView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired, IsAuthenticated]

    def get(self, request, app_id):
        app = _get_application_for_user(request.user, app_id)
        return Response({"id": str(app.id), "name": app.name, "created_at": app.created_at.isoformat()})

    def patch(self, request, app_id):
        app = _get_application_for_user(request.user, app_id)
        name = (request.data.get("name") or "").strip()
        if not name:
            return error_response("INVALID_NAME", "Application name is required.", status_code=400)
        app.name = name
        app.save(update_fields=["name"])
        return Response({"id": str(app.id), "name": app.name, "created_at": app.created_at.isoformat()})


class ApplicationTokenListCreateView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired, IsAuthenticated]

    def get(self, request, app_id):
        app = _get_application_for_user(request.user, app_id)
        tokens = ApiToken.objects.filter(application=app).order_by("-created_at")
        return Response([
            {
                "id": str(token.id),
                "prefix": token.token_prefix,
                "created_at": token.created_at.isoformat(),
                "revoked_at": token.revoked_at.isoformat() if token.revoked_at else None,
                "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
            }
            for token in tokens
        ])

    def post(self, request, app_id):
        app = _get_application_for_user(request.user, app_id)
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_api_token(raw_token)
        token = ApiToken.objects.create(
            application=app,
            token_hash=token_hash,
            token_prefix=raw_token[:10],
        )
        return Response({
            "id": str(token.id),
            "token": raw_token,
            "prefix": token.token_prefix,
            "created_at": token.created_at.isoformat(),
        }, status=201)


class ApplicationTokenRevokeView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired, IsAuthenticated]

    def post(self, request, app_id, token_id):
        app = _get_application_for_user(request.user, app_id)
        token = ApiToken.objects.filter(application=app, id=token_id, revoked_at__isnull=True).first()
        if not token:
            return error_response("TOKEN_NOT_FOUND", "Token not found.", status_code=404)
        token.revoked_at = timezone.now()
        token.save(update_fields=["revoked_at"])
        return Response({"status": "revoked"})
