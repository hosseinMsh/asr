import tempfile
import uuid
from datetime import timedelta

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from pydub import AudioSegment
from django.db.models import Sum
from django.utils import timezone

from asr import schemas
from asr.models import UsageLedger, ASRJob, Application
from asr.utils.ownership import get_job_for_request
from asr.utils.plan import resolve_user_plan, resolve_plan_from_code
from asr.utils.errors import error_response
from asr.utils.auth import enforce_bearer_token_only, get_request_sid, HumanJWTAuthentication, HumanTokenRequired, \
    ApiTokenRequired, ApiTokenAuthentication, HumanOrApiTokenRequired
from asr.tasks import run_asr_job

def _get_plan(request):
    auth = getattr(request, "auth", None)
    if auth:
        try:
            p = auth.get("plan")
            if p:
                return resolve_plan_from_code(p)
        except Exception:
            pass
    if request.user and request.user.is_authenticated:
        return resolve_user_plan(request.user)
    return resolve_plan_from_code("anon")


def _get_history_queryset(request, plan):
    if request.user and request.user.is_authenticated:
        qs = ASRJob.objects.filter(user=request.user, application__isnull=True)
    else:
        sid = get_request_sid(request)
        if not sid:
            return ASRJob.objects.none()
        qs = ASRJob.objects.filter(session_key=sid, application__isnull=True)
    if plan and plan.history_retention_days:
        cutoff = timezone.now() - timedelta(days=plan.history_retention_days)
        qs = qs.filter(created_at__gte=cutoff)
    return qs


def _get_month_start():
    now = timezone.now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _monthly_usage_seconds(request):
    if request.user and request.user.is_authenticated:
        qs = UsageLedger.objects.filter(user=request.user, application__isnull=True)
    else:
        sid = get_request_sid(request)
        if not sid:
            return 0.0
        qs = UsageLedger.objects.filter(session_key=sid, application__isnull=True)
    qs = qs.filter(created_at__gte=_get_month_start())
    agg = qs.aggregate(total_sec=Sum("audio_duration_sec"))
    return float(agg["total_sec"] or 0)

def _extract_duration(audio_bytes: bytes) -> float:
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tmp:
        tmp.write(audio_bytes); tmp.flush()
        audio = AudioSegment.from_file(tmp.name)
        return len(audio) / 1000.0

class HealthView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired]

    @extend_schema(
        tags=["User ASR"],
        summary="Health check",
        description="Simple health endpoint that validates JWT authentication.",
        responses=schemas.HealthResponseSerializer,
    )
    def get(self, request):
        return Response({"status":"ok"})


class DashboardOverviewView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired, IsAuthenticated]

    @extend_schema(
        tags=["User ASR"],
        summary="Usage overview",
        responses=schemas.DashboardOverviewSerializer,
    )
    def get(self, request):
        usage = UsageLedger.objects.filter(user=request.user, application__isnull=True).aggregate(
            total_cost=Sum("cost_units"),
            total_sec=Sum("audio_duration_sec"),
            total_words=Sum("words_count"),
        )
        jobs_count = ASRJob.objects.filter(user=request.user, application__isnull=True).count()
        return Response({
            "total_cost_units": float(usage["total_cost"] or 0),
            "total_audio_sec": float(usage["total_sec"] or 0),
            "total_words": int(usage["total_words"] or 0),
            "jobs_count": jobs_count,
        })

class UploadView(APIView):
    authentication_classes = [HumanJWTAuthentication, ApiTokenAuthentication]
    permission_classes = [HumanOrApiTokenRequired]

    @extend_schema(
        tags=["User ASR"],
        summary="Upload audio for transcription",
        description="Uploads an audio file for transcription. Requires a bearer JWT. The file field should be sent as `audio`.",
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

        plan = _get_plan(request)

        audio_bytes = audio.read()

        duration_sec = None
        try:
            duration_sec = _extract_duration(audio_bytes)
            if plan and plan.monthly_seconds_limit:
                used = _monthly_usage_seconds(request)
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

        if request.user and request.user.is_authenticated:
            user = request.user
            session_key = None
        else:
            user = None
            session_key = get_request_sid(request)
            if not session_key:
                return error_response(
                    "SESSION_MISSING",
                    "Anonymous token missing session.",
                    status_code=403,
                )

        job = ASRJob.objects.create(
            user=user, session_key=session_key, status="queued",
            audio_mime=audio.content_type, audio_duration_sec=duration_sec
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

class StatusView(APIView):
    authentication_classes = [HumanJWTAuthentication,ApiTokenAuthentication]
    permission_classes = [HumanOrApiTokenRequired]

    @extend_schema(
        tags=["User ASR"],
        summary="Get job status",
        parameters=[
            OpenApiParameter("job_id", type=str, location=OpenApiParameter.PATH, description="ASR job id"),
        ],
        responses={
            200: schemas.JobStatusSerializer,
            404: schemas.ErrorResponseSerializer,
        },
    )
    def get(self, request, job_id: uuid.UUID):
        job = get_job_for_request(request, job_id)
        payload = {
            "id": str(job.id),
            "status": job.status,
            "processing_seconds": job.processing_time_sec,
            "audio": {
                "duration_sec": job.audio_duration_sec,
                "sample_rate": job.audio_sample_rate,
                "channels": job.audio_channels,
                "mime": job.audio_mime,
            }
        }
        if job.status == "error":
            payload["error"] = {
                "code": job.error_code or "PROCESSING_FAILED",
                "message": job.error_message_public or "Processing failed.",
            }
        return Response(payload)

class ResultView(APIView):
    authentication_classes = [HumanJWTAuthentication,ApiTokenAuthentication]
    permission_classes = [HumanOrApiTokenRequired]

    @extend_schema(
        tags=["User ASR"],
        summary="Get transcription result",
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
        job = get_job_for_request(request, job_id)
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
            "audio": {"duration_sec": job.audio_duration_sec, "sample_rate": job.audio_sample_rate, "channels": job.audio_channels, "mime": job.audio_mime},
            "processing_seconds": job.processing_time_sec,
            "cost_units": getattr(usage, "cost_units", None),
            "plan_at_time": getattr(usage.plan_at_time, "code", None) if usage else None,
        })

class UsageView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired]

    @extend_schema(
        tags=["User ASR"],
        summary="Usage summary (GET)",
        responses=schemas.UsageSummarySerializer,
    )
    def get(self, request):
        return self._handle(request)

    @extend_schema(
        tags=["User ASR"],
        summary="Usage summary (POST)",
        responses=schemas.UsageSummarySerializer,
    )
    def post(self, request):
        enforce_bearer_token_only(request)
        return self._handle(request)

    def _handle(self, request):
        if request.user and request.user.is_authenticated:
            qs = UsageLedger.objects.filter(user=request.user, application__isnull=True)
        else:
            sid = get_request_sid(request)
            if not sid:
                return Response({
                    "total_cost_units": 0.0,
                    "total_audio_sec": 0.0,
                    "total_words": 0,
                    "count": 0,
                })
            qs = UsageLedger.objects.filter(session_key=sid, application__isnull=True)

        agg = qs.aggregate(
            total_cost=Sum("cost_units"),
            total_sec=Sum("audio_duration_sec"),
            total_words=Sum("words_count"),
        )
        return Response({
            "total_cost_units": float(agg["total_cost"] or 0),
            "total_audio_sec": float(agg["total_sec"] or 0),
            "total_words": int(agg["total_words"] or 0),
            "count": qs.count(),
        })


class UsageByAppView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired, IsAuthenticated]

    @extend_schema(
        tags=["User ASR"],
        summary="Usage by application",
        responses=schemas.ApplicationUsageSerializer(many=True),
    )
    def get(self, request):
        apps = Application.objects.filter(owner=request.user).order_by("name")
        results = []
        for app in apps:
            agg = UsageLedger.objects.filter(application=app).aggregate(
                total_cost=Sum("cost_units"),
                total_sec=Sum("audio_duration_sec"),
                total_words=Sum("words_count"),
            )
            results.append({
                "app_id": str(app.id),
                "app_name": app.name,
                "total_cost_units": float(agg["total_cost"] or 0),
                "total_audio_sec": float(agg["total_sec"] or 0),
                "total_words": int(agg["total_words"] or 0),
            })
        return Response(results)


class HistoryView(APIView):
    authentication_classes = [HumanJWTAuthentication]
    permission_classes = [HumanTokenRequired]

    @extend_schema(
        tags=["User ASR"],
        summary="List transcription jobs",
        parameters=[
            OpenApiParameter("page", type=int, location=OpenApiParameter.QUERY, required=False, description="Page number (default 1)"),
            OpenApiParameter("page_size", type=int, location=OpenApiParameter.QUERY, required=False, description="Items per page (default 10, max 50)"),
        ],
        responses=schemas.PaginatedHistorySerializer,
    )
    def get(self, request):
        plan = _get_plan(request)
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 10)), 1), 50)
        qs = _get_history_queryset(request, plan).order_by("-created_at")
        total = qs.count()
        offset = (page - 1) * page_size
        items = []
        for job in qs[offset: offset + page_size]:
            items.append({
                "id": str(job.id),
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "audio_duration_sec": job.audio_duration_sec,
                "words_count": job.words_count,
                "chars_count": job.chars_count,
            })
        return Response({
            "page": page,
            "page_size": page_size,
            "total": total,
            "results": items,
        })

    @extend_schema(
        tags=["User ASR"],
        summary="List transcription jobs (POST)",
        responses=schemas.PaginatedHistorySerializer,
    )
    def post(self, request):
        enforce_bearer_token_only(request)
        return self.get(request)
