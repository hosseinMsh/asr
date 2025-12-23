from django.utils import timezone

from asr.models import Application, APIToken
from asr.applications.authentication import generate_api_token


def list_applications(user):
    return Application.objects.filter(user=user).order_by("created_at")


def create_application(user, name: str) -> Application:
    return Application.objects.create(user=user, name=name)


def deactivate_application(application: Application) -> Application:
    application.is_active = False
    application.save(update_fields=["is_active", "updated_at"])
    return application


def list_tokens(application: Application):
    return application.tokens.order_by("-created_at")


def create_token(application: Application, name: str) -> tuple[APIToken, str]:
    raw_token, token_hash, last_four = generate_api_token()
    api_token = APIToken.objects.create(
        application=application,
        name=name,
        token_hash=token_hash,
        token_last_four=last_four,
    )
    return api_token, raw_token


def revoke_token(token: APIToken) -> APIToken:
    if not token.revoked_at:
        token.revoked_at = timezone.now()
        token.save(update_fields=["revoked_at"])
    return token
