from django.contrib import admin
from .models import ASRJob, UsageLedger, UserProfile, Subscription

@admin.register(ASRJob)
class ASRJobAdmin(admin.ModelAdmin):
    list_display = ("id","user","session_key","status","audio_duration_sec","words_count","chars_count","processing_time_sec","created_at")
    list_filter = ("status","created_at")

@admin.register(UsageLedger)
class UsageLedgerAdmin(admin.ModelAdmin):
    list_display = ("id","user","session_key","plan_at_time","audio_duration_sec","words_count","cost_units","created_at")
    list_filter = ("plan_at_time","created_at")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user","plan","token_version")
    list_filter = ("plan",)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user","plan","is_active","starts_at","ends_at")
    list_filter = ("plan","is_active")
