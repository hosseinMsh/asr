from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from asr.utils.plan import resolve_user_plan

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["plan"] = str(resolve_user_plan(user))
        try:
            token["tv"] = getattr(user.profile, "token_version", 1)
        except Exception:
            token["tv"] = 1
        token["uid"] = user.id
        return token
