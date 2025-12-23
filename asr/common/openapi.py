from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiTokenAuthScheme(OpenApiAuthenticationExtension):
    target_class = "asr.applications.authentication.APITokenAuthentication"
    name = "ApiTokenAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Token",
            "description": "API token in the Authorization header using the Bearer scheme.",
        }


class JWTAuthScheme(OpenApiAuthenticationExtension):
    target_class = "rest_framework_simplejwt.authentication.JWTAuthentication"
    name = "JWTAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token for dashboard/admin APIs.",
        }
