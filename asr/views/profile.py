from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from asr.models import Profile
from asr.serializers import ProfileSerializer, PasswordChangeSerializer
from asr.utils.auth import HumanJWTAuthentication


def _get_or_create_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


class CurrentUserProfileView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = _get_or_create_profile(request.user)
        serializer = ProfileSerializer(profile, context={"request": request})
        return Response(serializer.data)


class UpdateUserProfileView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def put(self, request):
        profile = _get_or_create_profile(request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated. Please login again."}, status=status.HTTP_200_OK)
