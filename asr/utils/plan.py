from django.conf import settings
from django.utils import timezone

from asr.models import Plan


def _plan_defaults(code: str) -> dict:
    defaults = settings.DEFAULT_PLANS.get(code, {})
    return {
        "name": defaults.get("name", code.title()),
        "monthly_seconds_limit": defaults.get("monthly_seconds_limit"),
        "max_file_size_mb": defaults.get("max_file_size_mb"),
        "history_retention_days": defaults.get("history_retention_days"),
    }


def get_or_create_plan(code: str) -> Plan:
    plan, _ = Plan.objects.get_or_create(code=code, defaults=_plan_defaults(code))
    return plan


def resolve_plan_from_code(code: str, fallback: str = "anon") -> Plan:
    if not code:
        return get_or_create_plan(fallback)
    plan = Plan.objects.filter(code=code).first()
    return plan if plan else get_or_create_plan(fallback)


def resolve_user_plan(user) -> Plan:
    sub = getattr(user, "subscription", None)
    if sub and sub.is_active and sub.plan:
        if sub.ends_at and sub.ends_at < timezone.now():
            return get_or_create_plan("free")
        return sub.plan
    prof = getattr(user, "profile", None)
    if prof and prof.plan:
        return prof.plan
    return get_or_create_plan("free")
