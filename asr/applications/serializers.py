from rest_framework import serializers


class ApplicationSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ApplicationListResponseSerializer(serializers.Serializer):
    results = ApplicationSerializer(many=True)


class ApplicationCreateSerializer(serializers.Serializer):
    name = serializers.CharField()


class ApplicationDeactivateSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class APITokenSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    token_last_four = serializers.CharField(read_only=True)
    revoked_at = serializers.DateTimeField(allow_null=True, read_only=True)
    last_used_at = serializers.DateTimeField(allow_null=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class APITokenListResponseSerializer(serializers.Serializer):
    results = APITokenSerializer(many=True)


class APITokenCreateSerializer(serializers.Serializer):
    name = serializers.CharField()


class APITokenCreateResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    token = serializers.CharField(read_only=True)
    token_last_four = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class APITokenRevokeSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    revoked_at = serializers.DateTimeField(allow_null=True, read_only=True)


class ApplicationUsageResponseSerializer(serializers.Serializer):
    application_id = serializers.UUIDField()
    total_cost_units = serializers.FloatField()
    total_audio_sec = serializers.FloatField()
    total_words = serializers.IntegerField()
    count = serializers.IntegerField()
