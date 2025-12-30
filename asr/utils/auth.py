import hashlib

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication

from asr.models import ApiToken


# -----------------------------
# Helpers
# -----------------------------

def _get_bearer_token(request) -> str | None:
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header:
        return None
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return None


def _looks_like_jwt(token: str) -> bool:
    # basic heuristic, real validation happens in JWTAuthentication
    return token.count(".") == 2


def hash_api_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def enforce_bearer_token_only(request) -> None:
    """
    Prevent passing tokens via body or query params.
    """
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if "api_token" in request.data or "API_TOKEN" in request.data:
            raise AuthenticationFailed(
                "API tokens must be provided via Authorization header."
            )
    if "api_token" in request.query_params or "API_TOKEN" in request.query_params:
        raise AuthenticationFailed(
            "API tokens must be provided via Authorization header."
        )


def get_request_sid(request) -> str | None:
    if request.auth_type != "jwt":
        return None
    auth = getattr(request, "auth", None)
    return auth.get("sid") if isinstance(auth, dict) else None


# -----------------------------
# Authentication
# -----------------------------

class HumanJWTAuthentication(JWTAuthentication):
    """
    JWT authentication for human users.
    If token is not JWT-like -> return None (fallback to next auth).
    """

    def authenticate(self, request):
        enforce_bearer_token_only(request)

        raw_token = _get_bearer_token(request)
        if not raw_token:
            return None

        # Not a JWT → let ApiTokenAuthentication try
        if not _looks_like_jwt(raw_token):
            return None

        # JWT-like → must be valid JWT
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        # Token version invalidation
        if getattr(user, "is_authenticated", False):
            current_tv = getattr(getattr(user, "profile", None), "token_version", None)
            token_tv = validated_token.get("tv")
            if current_tv is not None and token_tv is not None and token_tv != current_tv:
                raise AuthenticationFailed("Token has been revoked. Please login again.")

        if isinstance(user, AnonymousUser) and not validated_token.get("sid"):
            raise AuthenticationFailed("Anonymous JWT missing session id.")

        request.auth_type = "jwt"
        request.is_human_auth = True

        return (user, validated_token)

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id") or validated_token.get("uid")
        if not user_id or user_id == 0:
            return AnonymousUser()

        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist as exc:
            raise AuthenticationFailed("User not found.") from exc


class ApiTokenAuthentication(BaseAuthentication):
    """
    API token authentication.
    If token looks like JWT -> return None (JWT auth will handle it).
    """

    def authenticate(self, request):
        enforce_bearer_token_only(request)

        raw_token = _get_bearer_token(request)
        if not raw_token:
            return None

        # JWT-like → not our responsibility
        if _looks_like_jwt(raw_token):
            return None

        token_hash = hash_api_token(raw_token)

        token_obj = (
            ApiToken.objects
            .select_related("application", "application__owner")
            .filter(
                token_hash=token_hash,
                revoked_at__isnull=True,
            )
            .first()
        )

        if not token_obj:
            raise AuthenticationFailed("Invalid API token.")

        token_obj.last_used_at = timezone.now()
        token_obj.save(update_fields=["last_used_at"])

        request.auth_type = "api"
        request.is_api_auth = True
        request.api_token = token_obj
        request.application = token_obj.application

        return (token_obj.application.owner, token_obj)


# -----------------------------
# Permission
# -----------------------------

class HumanOrApiTokenRequired(BasePermission):
    """
    Allow access if either:
    - valid human JWT
    - valid API token
    """

    def has_permission(self, request, view):
        return (
            getattr(request, "auth_type", None) in {"jwt", "api"}
            and getattr(request, "user", None) is not None
        )
