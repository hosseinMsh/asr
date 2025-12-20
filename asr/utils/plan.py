from django.utils import timezone
from asr.models import Plan

def resolve_user_plan(user):
    sub = getattr(user, "subscription", None)
    if sub and sub.is_active:
        if sub.ends_at and sub.ends_at < timezone.now():
            return Plan.FREE
        return sub.plan
    prof = getattr(user, "profile", None)
    return prof.plan if prof else Plan.FREE
