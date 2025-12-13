import uuid

from django.db import models
from django.contrib.auth.models import User

class Plan(models.TextChoices):
    ANON = "anon", "Anonymous"
    FREE = "free", "Free"
    PLUS = "plus", "Plus"
    PRO  = "pro", "Pro"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    plan = models.CharField(max_length=16, choices=Plan.choices, default=Plan.FREE)
    token_version = models.PositiveIntegerField(default=1)

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.CharField(max_length=16, choices=Plan.choices)
    is_active = models.BooleanField(default=False)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

class ASRJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STATUS_CHOICES = [("queued","Queued"),("processing","Processing"),("done","Done"),("error","Error")]
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="asr_jobs")
    session_key = models.CharField(max_length=40, null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="queued")
    error_message = models.TextField(null=True, blank=True)
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
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name="usage_ledger")
    session_key = models.CharField(max_length=40, null=True, blank=True)
    job = models.OneToOneField(ASRJob, on_delete=models.CASCADE, related_name="usage")
    plan_at_time = models.CharField(max_length=16, choices=Plan.choices)
    audio_duration_sec = models.FloatField()
    words_count = models.IntegerField(default=0)
    chars_count = models.IntegerField(default=0)
    cost_units = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
