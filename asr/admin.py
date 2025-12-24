from django.contrib import admin
from .models import ASRJob, UsageLedger, UserProfile, Subscription, Plan, Application, ApiToken


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "monthly_seconds_limit", "max_file_size_mb", "history_retention_days", "is_active")
    list_filter = ("is_active",)

@admin.register(ASRJob)
class ASRJobAdmin(admin.ModelAdmin):
    list_display = ("id","user","application","session_key","status","audio_duration_sec","words_count","chars_count","processing_time_sec","created_at")
    list_filter = ("status","created_at")

@admin.register(UsageLedger)
class UsageLedgerAdmin(admin.ModelAdmin):
    list_display = ("id","user","application","session_key","plan_at_time","audio_duration_sec","words_count","cost_units","created_at")
    list_filter = ("plan_at_time","created_at")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user","plan","token_version")
    list_filter = ("plan",)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user","plan","is_active","starts_at","ends_at")
    list_filter = ("plan","is_active")

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id","name","owner","created_at")
    list_filter = ("created_at",)

@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ("id","application","token_prefix","created_at","revoked_at","last_used_at")
    list_filter = ("created_at","revoked_at")
