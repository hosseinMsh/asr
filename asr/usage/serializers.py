from rest_framework import serializers


class UsageSummarySerializer(serializers.Serializer):
    total_cost_units = serializers.FloatField()
    total_audio_sec = serializers.FloatField()
    total_words = serializers.IntegerField()
    count = serializers.IntegerField()
