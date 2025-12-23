from django.utils import timezone
from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError

from asr.auth.api_token import generate_api_token
from asr.models import Application, APIToken, UsageLedger


def _get_application_for_user(user, app_id: str) -> Application:
    app = Application.objects.filter(id=app_id, user=user).first()
    if not app:
        raise NotFound("Application not found.")
    return app


class ApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        apps = Application.objects.filter(user=request.user).order_by("created_at")
        payload = [
            {
                "id": str(app.id),
                "name": app.name,
                "is_active": app.is_active,
                "created_at": app.created_at.isoformat(),
                "updated_at": app.updated_at.isoformat(),
            }
            for app in apps
        ]
        return Response({"results": payload})

    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            raise ValidationError("Application name is required.")
        app = Application.objects.create(user=request.user, name=name)
        return Response(
            {
                "id": str(app.id),
                "name": app.name,
                "is_active": app.is_active,
                "created_at": app.created_at.isoformat(),
                "updated_at": app.updated_at.isoformat(),
            },
            status=201,
        )


class ApplicationDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, app_id: str):
        app = _get_application_for_user(request.user, app_id)
        app.is_active = False
        app.save(update_fields=["is_active", "updated_at"])
        return Response(
            {
                "id": str(app.id),
                "name": app.name,
                "is_active": app.is_active,
                "updated_at": app.updated_at.isoformat(),
            }
        )


class APITokenListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, app_id: str):
        app = _get_application_for_user(request.user, app_id)
        tokens = app.tokens.order_by("-created_at")
        payload = [
            {
                "id": str(token.id),
                "name": token.name,
                "token_last_four": token.token_last_four,
                "revoked_at": token.revoked_at.isoformat() if token.revoked_at else None,
                "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
                "created_at": token.created_at.isoformat(),
            }
            for token in tokens
        ]
        return Response({"results": payload})

    def post(self, request, app_id: str):
        app = _get_application_for_user(request.user, app_id)
        name = (request.data.get("name") or "").strip()
        if not name:
            raise ValidationError("Token name is required.")
        raw_token, token_hash, last_four = generate_api_token()
        api_token = APIToken.objects.create(
            application=app,
            name=name,
            token_hash=token_hash,
            token_last_four=last_four,
        )
        return Response(
            {
                "id": str(api_token.id),
                "name": api_token.name,
                "token": raw_token,
                "token_last_four": api_token.token_last_four,
                "created_at": api_token.created_at.isoformat(),
            },
            status=201,
        )


class APITokenRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, app_id: str, token_id: str):
        app = _get_application_for_user(request.user, app_id)
        token = app.tokens.filter(id=token_id).first()
        if not token:
            raise NotFound("Token not found.")
        if not token.revoked_at:
            token.revoked_at = timezone.now()
            token.save(update_fields=["revoked_at"])
        return Response(
            {
                "id": str(token.id),
                "revoked_at": token.revoked_at.isoformat() if token.revoked_at else None,
            }
        )


class ApplicationUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, app_id: str):
        app = _get_application_for_user(request.user, app_id)
        qs = UsageLedger.objects.filter(application=app)
        agg = qs.aggregate(
            total_cost=Sum("cost_units"),
            total_sec=Sum("audio_duration_sec"),
            total_words=Sum("words_count"),
        )
        return Response(
            {
                "application_id": str(app.id),
                "total_cost_units": float(agg["total_cost"] or 0),
                "total_audio_sec": float(agg["total_sec"] or 0),
                "total_words": int(agg["total_words"] or 0),
                "count": qs.count(),
            }
        )
