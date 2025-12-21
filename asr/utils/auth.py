from rest_framework.exceptions import PermissionDenied, ValidationError


def _get_bearer_token(request) -> str | None:
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header:
        return None
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return None


def enforce_body_token(request) -> None:
    bearer = _get_bearer_token(request)
    if not bearer:
        return
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    body_token = request.data.get("auth_token")
    if not body_token:
        raise ValidationError("auth_token required")
    if body_token != bearer:
        raise PermissionDenied("auth_token mismatch")
