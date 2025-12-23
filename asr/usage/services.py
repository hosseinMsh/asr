from django.db.models import Sum

from asr.models import Application, UsageLedger


def usage_summary_for_application(application: Application) -> dict:
    qs = UsageLedger.objects.filter(application=application)
    agg = qs.aggregate(
        total_cost=Sum("cost_units"),
        total_sec=Sum("audio_duration_sec"),
        total_words=Sum("words_count"),
    )
    return {
        "total_cost_units": float(agg["total_cost"] or 0),
        "total_audio_sec": float(agg["total_sec"] or 0),
        "total_words": int(agg["total_words"] or 0),
        "count": qs.count(),
    }
