import uuid

from django.db import models
from django.contrib.auth.models import User


class Plan(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    monthly_seconds_limit = models.PositiveIntegerField(null=True, blank=True)
    max_file_size_mb = models.PositiveIntegerField(null=True, blank=True)
    history_retention_days = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="profiles", null=True, blank=True)
    token_version = models.PositiveIntegerField(default=1)

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions", null=True, blank=True)
    is_active = models.BooleanField(default=False)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.user_id})"


class APIToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="tokens")
    name = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=64, unique=True)
    token_last_four = models.CharField(max_length=4)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

class ASRJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STATUS_CHOICES = [("queued","Queued"),("processing","Processing"),("done","Done"),("error","Error")]
    application = models.ForeignKey("Application", null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="asr_jobs")
    session_key = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="queued")
    error_message = models.TextField(null=True, blank=True)
    error_code = models.CharField(max_length=64, null=True, blank=True)
    error_message_public = models.TextField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    audio_duration_sec = models.FloatField(null=True, blank=True)
    audio_sample_rate = models.IntegerField(null=True, blank=True)
    audio_channels = models.IntegerField(null=True, blank=True)
    audio_format = models.CharField(max_length=32, null=True, blank=True)
    audio_mime = models.CharField(max_length=64, null=True, blank=True)

    words_count = models.IntegerField(default=0)
    chars_count = models.IntegerField(default=0)
    processing_time_sec = models.FloatField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UsageLedger(models.Model):
    application = models.ForeignKey("Application", null=True, blank=True, on_delete=models.SET_NULL, related_name="usage_ledger")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="usage_ledger")
    session_key = models.CharField(max_length=40, null=True, blank=True)
    job = models.OneToOneField(ASRJob, on_delete=models.CASCADE, related_name="usage")
    plan_at_time = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="usage_entries")
    audio_duration_sec = models.FloatField()
    words_count = models.IntegerField(default=0)
    chars_count = models.IntegerField(default=0)
    cost_units = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
