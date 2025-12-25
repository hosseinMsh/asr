from rest_framework import serializers


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Service health indicator.")


class ErrorResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class UploadRequestSerializer(serializers.Serializer):
    audio = serializers.FileField(help_text="Audio file to transcribe. Use the `audio` field name.")
    language = serializers.CharField(
        required=False,
        default="fa",
        help_text="Language code for transcription. Defaults to Persian (`fa`).",
    )


class UploadResponseSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()


class AudioInfoSerializer(serializers.Serializer):
    duration_sec = serializers.FloatField(allow_null=True)
    sample_rate = serializers.IntegerField(allow_null=True)
    channels = serializers.IntegerField(allow_null=True)
    mime = serializers.CharField(allow_null=True)


class JobStatusErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class JobStatusSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    processing_seconds = serializers.FloatField(allow_null=True)
    audio = AudioInfoSerializer()
    error = JobStatusErrorSerializer(required=False)


class JobResultSerializer(serializers.Serializer):
    text = serializers.CharField()
    json_result = serializers.JSONField()
    words_count = serializers.IntegerField()
    chars_count = serializers.IntegerField()
    audio = AudioInfoSerializer()
    processing_seconds = serializers.FloatField(allow_null=True)
    cost_units = serializers.FloatField(allow_null=True)
    plan_at_time = serializers.CharField(allow_null=True)


class UsageSummarySerializer(serializers.Serializer):
    total_cost_units = serializers.FloatField()
    total_audio_sec = serializers.FloatField()
    total_words = serializers.IntegerField()
    count = serializers.IntegerField()


class ApplicationUsageSerializer(serializers.Serializer):
    app_id = serializers.UUIDField()
    app_name = serializers.CharField()
    total_cost_units = serializers.FloatField()
    total_audio_sec = serializers.FloatField()
    total_words = serializers.IntegerField()


class HistoryItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    audio_duration_sec = serializers.FloatField(allow_null=True)
    words_count = serializers.IntegerField()
    chars_count = serializers.IntegerField()


class PaginatedHistorySerializer(serializers.Serializer):
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total = serializers.IntegerField()
    results = HistoryItemSerializer(many=True)


class DashboardOverviewSerializer(serializers.Serializer):
    total_cost_units = serializers.FloatField()
    total_audio_sec = serializers.FloatField()
    total_words = serializers.IntegerField()
    jobs_count = serializers.IntegerField()


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="JWT access token.")
    plan = serializers.CharField()
    expires_in_sec = serializers.IntegerField()


class RegisterRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()


class ApplicationCreateSerializer(serializers.Serializer):
    name = serializers.CharField()


class ApplicationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    created_at = serializers.DateTimeField()


class ApplicationTokenSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    prefix = serializers.CharField()
    created_at = serializers.DateTimeField()
    revoked_at = serializers.DateTimeField(allow_null=True)
    last_used_at = serializers.DateTimeField(allow_null=True)


class ApplicationTokenCreateResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    token = serializers.CharField(help_text="Full token value. Store securely; it is only returned once.")
    prefix = serializers.CharField()
    created_at = serializers.DateTimeField()


class RevokeTokenResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
