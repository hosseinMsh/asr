def get_bearer_token(request) -> str | None:
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header:
        return None
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return None
