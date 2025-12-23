import secrets

from django.conf import settings
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from asr.common.auth import get_bearer_token
from asr.models import APIToken


def _hash_token(raw_token: str) -> str:
    digest = salted_hmac("api-token", raw_token, secret=settings.SECRET_KEY).hexdigest()
    return digest


def generate_api_token() -> tuple[str, str, str]:
    raw = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw)
    last_four = raw[-4:]
    return raw, token_hash, last_four


class APITokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        raw_token = get_bearer_token(request)
        if not raw_token:
            return None
        if raw_token.count(".") >= 2:
            raise AuthenticationFailed("JWTs are not allowed for this endpoint.")
        token_hash = _hash_token(raw_token)
        api_token = (
            APIToken.objects.select_related("application", "application__user")
            .filter(token_hash=token_hash)
            .first()
        )
        if not api_token:
            raise AuthenticationFailed("Invalid API token.")
        if api_token.is_revoked:
            raise AuthenticationFailed("API token has been revoked.")
        if not api_token.application.is_active:
            raise AuthenticationFailed("Application is disabled.")
        api_token.last_used_at = timezone.now()
        api_token.save(update_fields=["last_used_at"])
        request.application = api_token.application
        return api_token.application.user, api_token
