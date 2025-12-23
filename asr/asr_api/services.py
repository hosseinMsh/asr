import tempfile
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from pydub import AudioSegment

from asr.models import ASRJob, Application, UsageLedger
from asr.utils.plan import resolve_user_plan
from asr.tasks import run_asr_job


def get_plan_for_user(user):
    if user and user.is_authenticated:
        return resolve_user_plan(user)
    return None


def extract_duration(audio_bytes: bytes) -> float:
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        audio = AudioSegment.from_file(tmp.name)
        return len(audio) / 1000.0


def month_start() -> timezone.datetime:
    now = timezone.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def monthly_usage_seconds(application: Application) -> float:
    qs = UsageLedger.objects.filter(application=application, created_at__gte=month_start())
    agg = qs.aggregate(total_sec=Sum("audio_duration_sec"))
    return float(agg["total_sec"] or 0)


def history_queryset(application: Application, plan):
    qs = ASRJob.objects.filter(application=application)
    if plan and plan.history_retention_days:
        cutoff = timezone.now() - timedelta(days=plan.history_retention_days)
        qs = qs.filter(created_at__gte=cutoff)
    return qs


def create_job(application: Application, user, audio_file, language: str, plan):
    audio_bytes = audio_file.read()
    duration_sec = None
    try:
        duration_sec = extract_duration(audio_bytes)
        if plan and plan.monthly_seconds_limit:
            used = monthly_usage_seconds(application)
            if duration_sec and used + duration_sec > float(plan.monthly_seconds_limit):
                return None, {
                    "code": "MONTHLY_LIMIT_EXCEEDED",
                    "message": "Monthly seconds limit reached for your plan.",
                    "status_code": 403,
                }
    except Exception:
        duration_sec = None
    if plan and plan.max_file_size_mb:
        max_bytes = int(plan.max_file_size_mb) * 1024 * 1024
        if audio_file.size and audio_file.size > max_bytes:
            return None, {
                "code": "FILE_TOO_LARGE",
                "message": "File exceeds the maximum size for your plan.",
                "status_code": 403,
            }

    job = ASRJob.objects.create(
        application=application,
        user=user,
        status="queued",
        audio_mime=audio_file.content_type,
        audio_duration_sec=duration_sec,
    )

    async_result = run_asr_job.delay(
        job.id,
        audio_bytes,
        audio_file.content_type,
        language,
        plan.code,
    )
    job.celery_task_id = async_result.id
    job.save(update_fields=["celery_task_id"])
    return job, None


def get_job_for_application(application: Application, job_id):
    return ASRJob.objects.filter(id=job_id, application=application).first()


def build_status_payload(job: ASRJob) -> dict:
    payload = {
        "id": str(job.id),
        "status": job.status,
        "processing_seconds": job.processing_time_sec,
        "audio": {
            "duration_sec": job.audio_duration_sec,
            "sample_rate": job.audio_sample_rate,
            "channels": job.audio_channels,
            "mime": job.audio_mime,
        },
    }
    if job.status == "error":
        payload["error"] = {
            "code": job.error_code or "PROCESSING_FAILED",
            "message": job.error_message_public or "Processing failed.",
        }
    return payload


def build_result_payload(job: ASRJob) -> dict:
    usage = getattr(job, "usage", None)
    return {
        "text": job.text or "",
        "json_result": {"text": job.text or ""},
        "words_count": job.words_count,
        "chars_count": job.chars_count,
        "audio": {
            "duration_sec": job.audio_duration_sec,
            "sample_rate": job.audio_sample_rate,
            "channels": job.audio_channels,
            "mime": job.audio_mime,
        },
        "processing_seconds": job.processing_time_sec,
        "cost_units": getattr(usage, "cost_units", None),
        "plan_at_time": getattr(usage.plan_at_time, "code", None) if usage else None,
    }


def history_page(application: Application, plan, page: int, page_size: int) -> dict:
    qs = history_queryset(application, plan).order_by("-created_at")
    total = qs.count()
    offset = (page - 1) * page_size
    items = [
        {
            "id": str(job.id),
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "audio_duration_sec": job.audio_duration_sec,
            "words_count": job.words_count,
            "chars_count": job.chars_count,
        }
        for job in qs[offset : offset + page_size]
    ]
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "results": items,
    }
