from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class StrictJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        if raw_token.count(".") < 2:
            raise AuthenticationFailed("API tokens are not allowed for this endpoint.")
        return super().authenticate(request)
