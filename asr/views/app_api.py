import tempfile
import uuid

from drf_spectacular.utils import OpenApiParameter, extend_schema
from django.db.models import Sum
from django.utils import timezone
from pydub import AudioSegment
from rest_framework.response import Response
from rest_framework.views import APIView

from asr import schemas
from asr.models import ASRJob, UsageLedger
from asr.tasks import run_asr_job
from asr.utils.auth import ApiTokenAuthentication, ApiTokenRequired, enforce_bearer_token_only
from asr.utils.errors import error_response
from asr.utils.ownership import get_app_job_for_request
from asr.utils.plan import resolve_user_plan


def _get_month_start():
    now = timezone.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _extract_duration(audio_bytes: bytes) -> float:
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        audio = AudioSegment.from_file(tmp.name)
        return len(audio) / 1000.0


def _monthly_usage_seconds(application):
    qs = UsageLedger.objects.filter(application=application, created_at__gte=_get_month_start())
    agg = qs.aggregate(total_sec=Sum("audio_duration_sec"))
    return float(agg["total_sec"] or 0)


class AppHealthView(APIView):
    authentication_classes = [ApiTokenAuthentication]
    permission_classes = [ApiTokenRequired]

    @extend_schema(
        tags=["Application API"],
        summary="App API health check",
        responses=schemas.HealthResponseSerializer,
    )
    def get(self, request):
        return Response({"status": "ok"})


class AppUploadView(APIView):
    authentication_classes = [ApiTokenAuthentication]
    permission_classes = [ApiTokenRequired]

    @extend_schema(
        tags=["Application API"],
        summary="Upload audio (application token)",
        request=schemas.UploadRequestSerializer,
        responses={
            200: schemas.UploadResponseSerializer,
            400: schemas.ErrorResponseSerializer,
            403: schemas.ErrorResponseSerializer,
        },
    )
    def post(self, request):
        enforce_bearer_token_only(request)
        audio = request.FILES.get("audio") or request.FILES.get("file")
        if not audio:
            return error_response("MISSING_AUDIO", "Audio file is required.", status_code=400)

        application = request.application
        owner = application.owner
        plan = resolve_user_plan(owner)

        audio_bytes = audio.read()

        duration_sec = None
        try:
            duration_sec = _extract_duration(audio_bytes)
            if plan and plan.monthly_seconds_limit:
                used = _monthly_usage_seconds(application)
                if duration_sec and used + duration_sec > float(plan.monthly_seconds_limit):
                    return error_response(
                        "MONTHLY_LIMIT_EXCEEDED",
                        "Monthly seconds limit reached for your plan.",
                        status_code=403,
                    )
        except Exception:
            duration_sec = None
        if plan and plan.max_file_size_mb:
            max_bytes = int(plan.max_file_size_mb) * 1024 * 1024
            if audio.size and audio.size > max_bytes:
                return error_response(
                    "FILE_TOO_LARGE",
                    "File exceeds the maximum size for your plan.",
                    status_code=403,
                )

        job = ASRJob.objects.create(
            user=owner,
            application=application,
            status="queued",
            audio_mime=audio.content_type,
            audio_duration_sec=duration_sec,
        )

        async_result = run_asr_job.delay(
            job.id,
            audio_bytes,
            audio.content_type,
            request.data.get("language", "fa"),
            plan.code,
        )
        job.celery_task_id = async_result.id
        job.save(update_fields=["celery_task_id"])

        return Response({"job_id": str(job.id), "status": job.status})


class AppStatusView(APIView):
    authentication_classes = [ApiTokenAuthentication]
    permission_classes = [ApiTokenRequired]

    @extend_schema(
        tags=["Application API"],
        summary="Get application job status",
        parameters=[
            OpenApiParameter("job_id", type=str, location=OpenApiParameter.PATH, description="ASR job id"),
        ],
        responses={
            200: schemas.JobStatusSerializer,
            404: schemas.ErrorResponseSerializer,
        },
    )
    def get(self, request, job_id: uuid.UUID):
        job = get_app_job_for_request(request, job_id)
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
        return Response(payload)


class AppResultView(APIView):
    authentication_classes = [ApiTokenAuthentication]
    permission_classes = [ApiTokenRequired]

    @extend_schema(
        tags=["Application API"],
        summary="Get application transcription result",
        parameters=[
            OpenApiParameter("job_id", type=str, location=OpenApiParameter.PATH, description="ASR job id"),
        ],
        responses={
            200: schemas.JobResultSerializer,
            202: schemas.ErrorResponseSerializer,
            400: schemas.ErrorResponseSerializer,
            404: schemas.ErrorResponseSerializer,
        },
    )
    def get(self, request, job_id: uuid.UUID):
        job = get_app_job_for_request(request, job_id)
        if job.status != "done":
            if job.status in ("queued", "processing"):
                return error_response("JOB_PENDING", "Job is still processing.", status_code=202)
            return error_response(
                job.error_code or "PROCESSING_FAILED",
                job.error_message_public or "Processing failed.",
                status_code=400,
            )
        usage = getattr(job, "usage", None)
        return Response({
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
        })
