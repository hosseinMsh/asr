from rest_framework import serializers


class UploadRequestSerializer(serializers.Serializer):
    audio = serializers.FileField(required=False)
    file = serializers.FileField(required=False)
    language = serializers.CharField(required=False, default="fa")

    def validate(self, attrs):
        audio = attrs.get("audio") or attrs.get("file")
        if not audio:
            raise serializers.ValidationError("Audio file is required.")
        attrs["audio_file"] = audio
        return attrs


class UploadResponseSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()


class AudioMetadataSerializer(serializers.Serializer):
    duration_sec = serializers.FloatField(allow_null=True)
    sample_rate = serializers.IntegerField(allow_null=True)
    channels = serializers.IntegerField(allow_null=True)
    mime = serializers.CharField(allow_null=True)


class StatusResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    processing_seconds = serializers.FloatField(allow_null=True)
    audio = AudioMetadataSerializer()
    error = serializers.DictField(required=False)


class ResultResponseSerializer(serializers.Serializer):
    text = serializers.CharField()
    json_result = serializers.DictField()
    words_count = serializers.IntegerField()
    chars_count = serializers.IntegerField()
    audio = AudioMetadataSerializer()
    processing_seconds = serializers.FloatField(allow_null=True)
    cost_units = serializers.FloatField(allow_null=True)
    plan_at_time = serializers.CharField(allow_null=True)


class UsageResponseSerializer(serializers.Serializer):
    total_cost_units = serializers.FloatField()
    total_audio_sec = serializers.FloatField()
    total_words = serializers.IntegerField()
    count = serializers.IntegerField()


class HistoryItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    audio_duration_sec = serializers.FloatField(allow_null=True)
    words_count = serializers.IntegerField()
    chars_count = serializers.IntegerField()


class HistoryResponseSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total = serializers.IntegerField()
    results = HistoryItemSerializer(many=True)
