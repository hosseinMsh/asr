import tempfile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from pydub import AudioSegment
from django.db.models import Sum

from asr.models import UsageLedger, ASRJob
from asr.utils.ownership import get_job_for_request
from asr.utils.plan import resolve_user_plan
from asr.tasks import run_asr_job

def _ensure_session(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def _get_plan(request):
    auth = getattr(request, "auth", None)
    if auth:
        try:
            p = auth.get("plan")
            if p:
                return p
        except Exception:
            pass
    if request.user and request.user.is_authenticated:
        return str(resolve_user_plan(request.user))
    return "anon"

def _extract_duration(audio_bytes: bytes) -> float:
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tmp:
        tmp.write(audio_bytes); tmp.flush()
        audio = AudioSegment.from_file(tmp.name)
        return len(audio) / 1000.0

class HealthView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"status":"ok"})

class UploadView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        audio = request.FILES.get("audio") or request.FILES.get("file")
        if not audio:
            return Response({"detail":"Audio missing"}, status=400)

        plan = _get_plan(request)
        if plan not in {"anon","free","plus","pro"}:
            plan = "anon"

        audio_bytes = audio.read()

        duration_sec = None
        try:
            duration_sec = _extract_duration(audio_bytes)
            max_sec = settings.LIMITS.get(plan, {}).get("max_audio_sec")
            if max_sec and duration_sec > float(max_sec):
                return Response({"detail": f"Audio too long for plan={plan}. max={max_sec}s"}, status=403)
        except Exception:
            duration_sec = None

        if request.user and request.user.is_authenticated:
            user = request.user
            session_key = None
        else:
            user = None
            session_key = _ensure_session(request)
            try:
                if request.auth and request.auth.get("plan") == "anon":
                    sid = request.auth.get("sid")
                    if sid and sid != session_key:
                        return Response({"detail":"Anon token not bound to this session"}, status=403)
            except Exception:
                pass

        job = ASRJob.objects.create(
            user=user, session_key=session_key, status="queued",
            audio_mime=audio.content_type, audio_duration_sec=duration_sec
        )

        async_result = run_asr_job.delay(job.id, audio_bytes, audio.content_type, request.data.get("language","fa"), plan)
        job.celery_task_id = async_result.id
        print('job', async_result.id)
        job.save(update_fields=["celery_task_id"])

        return Response({"job_id": str(job.id), "status": job.status})

class StatusView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, job_id: int):
        job = get_job_for_request(request, job_id)
        return Response({
            "id": str(job.id),
            "status": job.status,
            "error": job.error_message,
            "processing_seconds": job.processing_time_sec,
            "audio": {
                "duration_sec": job.audio_duration_sec,
                "sample_rate": job.audio_sample_rate,
                "channels": job.audio_channels,
                "mime": job.audio_mime,
            }
        })

class ResultView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, job_id: int):
        job = get_job_for_request(request, job_id)
        if job.status != "done":
            return Response({"status": job.status, "error": job.error_message}, status=202 if job.status in ("queued","processing") else 400)
        usage = getattr(job, "usage", None)
        return Response({
            "text": job.text or "",
            "json_result": {"text": job.text or ""},
            "words_count": job.words_count,
            "chars_count": job.chars_count,
            "audio": {"duration_sec": job.audio_duration_sec, "sample_rate": job.audio_sample_rate, "channels": job.audio_channels, "mime": job.audio_mime},
            "processing_seconds": job.processing_time_sec,
            "cost_units": getattr(usage, "cost_units", None),
            "plan_at_time": getattr(usage, "plan_at_time", None),
        })

class UsageView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        if request.user and request.user.is_authenticated:
            qs = UsageLedger.objects.filter(user=request.user)
        else:
            if not request.session.session_key:
                request.session.create()
            qs = UsageLedger.objects.filter(session_key=request.session.session_key)

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
