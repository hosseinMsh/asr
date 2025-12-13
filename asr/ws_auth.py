from rest_framework_simplejwt.authentication import JWTAuthentication
from channels.db import database_sync_to_async

from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
import jwt


@database_sync_to_async
def _get_user_from_token(raw_token: str):
    auth = JWTAuthentication()
    validated = auth.get_validated_token(raw_token)
    user = auth.get_user(validated)
    return user, validated


class JWTQueryStringAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()
        scope["jwt"] = None

        # Decode query string safely
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)

        token_list = params.get("token", [])
        if not token_list:
            return await super().__call__(scope, receive, send)

        token = token_list[0]
        scope["jwt"] = token

        user = await self.get_user(token)
        if user:
            scope["user"] = user

        return await super().__call__(scope, receive, send)

    @sync_to_async
    def get_user(self, token):
        from django.conf import settings
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"],
            )
            return User.objects.get(id=payload["user_id"])
        except Exception:
            return None
