import time
import tempfile
import requests
from celery import shared_task
from django.conf import settings
from pydub import AudioSegment

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import ASRJob, UsageLedger
from .utils import map_exception, ASRTemporaryError


def push_job(job_id: int, data: dict):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"job_{job_id}",
        {"type": "job_event", "data": data},
    )


def _extract_audio_metadata(audio_bytes: bytes):
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tmp:
        tmp.write(audio_bytes);
        tmp.flush()
        audio = AudioSegment.from_file(tmp.name)
        return {"duration_sec": len(audio) / 1000.0, "sample_rate": audio.frame_rate, "channels": audio.channels}


def _calc_cost(duration_sec: float, words_count: int) -> float:
    return float(duration_sec or 0) + float(settings.WORD_COST) * int(words_count or 0)


@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2, "countdown": 5})
def run_asr_job(self, job_id: int, audio_bytes: bytes, content_type: str, language: str = "fa", plan: str = "anon"):
    job = ASRJob.objects.get(id=job_id)
    job.status = "processing"
    job.celery_task_id = self.request.id
    job.audio_mime = content_type
    job.save(update_fields=["status", "celery_task_id", "audio_mime"])
    push_job(job_id, {"status": "processing"})

    t0 = time.time()
    try:
        meta = _extract_audio_metadata(audio_bytes)
        job.audio_duration_sec = job.audio_duration_sec or meta["duration_sec"]
        job.audio_sample_rate = meta["sample_rate"]
        job.audio_channels = meta["channels"]
        job.save(update_fields=["audio_duration_sec", "audio_sample_rate", "audio_channels"])

        files = {"file": ("audio", audio_bytes, content_type)}
        data = {"language": language}
        resp = requests.post(settings.ASR_FASTAPI_URL, files=files, data=data, timeout=settings.ASR_FASTAPI_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()

        text = (payload.get("asr") or payload.get("text") or "").strip()
        job.text = text
        job.words_count = len(text.split()) if text else 0
        job.chars_count = len(text) if text else 0
        job.processing_time_sec = time.time() - t0
        job.status = "done"
        job.error_message = None
        job.save()

        cost_units = _calc_cost(job.audio_duration_sec, job.words_count)
        UsageLedger.objects.update_or_create(
            job=job,
            defaults={
                "user": job.user,
                "session_key": job.session_key,
                "plan_at_time": plan,
                "audio_duration_sec": float(job.audio_duration_sec or 0),
                "words_count": job.words_count,
                "chars_count": job.chars_count,
                "cost_units": float(cost_units),
            }
        )

        push_job(job_id, {
            "status": "done",
            "text": job.text,
            "words_count": job.words_count,
            "chars_count": job.chars_count,
            "audio_duration_sec": job.audio_duration_sec,
            "processing_seconds": job.processing_time_sec,
            "cost_units": cost_units,
            "plan": plan,
        })
        return {"text": text}


    except Exception as e:
        domain_error = map_exception(e)
        job.status = "error"
        job.processing_time_sec = time.time() - t0
        # full error only for backend/debug
        job.error_message = f"{type(e).__name__}: {str(e)}"
        job.save(update_fields=["status", "processing_time_sec", "error_message"])
        # SAFE payload for UI
        push_job(job_id, {
            "status": "error",
            "error_code": domain_error.error_code,
            "message": domain_error.public_message,
        })
        # retry only if temporary
        if isinstance(domain_error, ASRTemporaryError):
            raise self.retry(exc=e)
        return
