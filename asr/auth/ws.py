from asr.utils.auth import HumanJWTAuthentication
from channels.db import database_sync_to_async

from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _get_user_from_token(raw_token: str):
    auth = HumanJWTAuthentication()
    validated = auth.get_validated_token(raw_token)
    user = auth.get_user(validated)
    return user, validated


class JWTQueryStringAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()
        scope["jwt"] = None
        scope["token"] = None

        # Decode query string safely
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)

        token_list = params.get("token", [])
        if not token_list:
            return await super().__call__(scope, receive, send)

        token = token_list[0]
        scope["jwt"] = token

        try:
            user, payload = await _get_user_from_token(token)
            if user:
                scope["user"] = user
            scope["token"] = dict(payload)
        except Exception:
            scope["token"] = None

        return await super().__call__(scope, receive, send)
