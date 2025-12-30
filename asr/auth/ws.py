from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from asr.models import ApiToken
from asr.utils.auth import HumanJWTAuthentication, hash_api_token


@database_sync_to_async
def _get_user_from_jwt(raw_token: str):
    auth = HumanJWTAuthentication()
    validated = auth.get_validated_token(raw_token)
    user = auth.get_user(validated)
    return user, validated


@database_sync_to_async
def _get_api_token(raw_token: str):
    token_hash = hash_api_token(raw_token)
    token_obj = ApiToken.objects.select_related("application", "application__owner").filter(
        token_hash=token_hash,
        revoked_at__isnull=True,
    ).first()
    if not token_obj:
        return None
    token_obj.last_used_at = timezone.now()
    token_obj.save(update_fields=["last_used_at"])
    return token_obj


class JWTQueryStringAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()
        scope["jwt"] = None
        scope["token"] = None
        scope["api_token"] = None
        scope["application"] = None

        # Decode query string safely
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)

        auth_header = None
        headers = dict(scope.get("headers", []) or [])
        if b"authorization" in headers:
            auth_header = headers[b"authorization"].decode("utf-8")
        raw_token = None

        if auth_header and auth_header.lower().startswith("bearer "):
            raw_token = auth_header.split(" ", 1)[1].strip()
        elif params.get("token"):
            raw_token = params["token"][0]

        if not raw_token:
            return await super().__call__(scope, receive, send)

        scope["jwt"] = raw_token

        # Try JWT first; if that fails, fall back to API token
        try:
            user, payload = await _get_user_from_jwt(raw_token)
            if user:
                scope["user"] = user
            scope["token"] = dict(payload)
        except Exception:
            api_token = await _get_api_token(raw_token)
            if not api_token:
                scope["token"] = None
                return await super().__call__(scope, receive, send)
            scope["api_token"] = api_token
            scope["application"] = api_token.application
            scope["user"] = api_token.application.owner

        return await super().__call__(scope, receive, send)
