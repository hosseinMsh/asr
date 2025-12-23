from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound

from asr.accounts.authentication import StrictJWTAuthentication
from asr.models import ASRJob, UsageLedger, Application, APIToken


class UserUsageView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = UsageLedger.objects.filter(user=request.user)
        agg = qs.aggregate(
            total_cost=Sum("cost_units"),
            total_sec=Sum("audio_duration_sec"),
            total_words=Sum("words_count"),
        )
        return Response(
            {
                "total_cost_units": float(agg["total_cost"] or 0),
                "total_audio_sec": float(agg["total_sec"] or 0),
                "total_words": int(agg["total_words"] or 0),
                "count": qs.count(),
            }
        )


class UserUsageByAppView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        apps = Application.objects.filter(user=request.user)
        payload = []
        for app in apps:
            qs = UsageLedger.objects.filter(application=app)
            agg = qs.aggregate(
                total_cost=Sum("cost_units"),
                total_sec=Sum("audio_duration_sec"),
                total_words=Sum("words_count"),
            )
            payload.append(
                {
                    "application_id": str(app.id),
                    "application_name": app.name,
                    "total_cost_units": float(agg["total_cost"] or 0),
                    "total_audio_sec": float(agg["total_sec"] or 0),
                    "total_words": int(agg["total_words"] or 0),
                    "count": qs.count(),
                }
            )
        return Response({"results": payload})


class DashboardOverviewView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        apps = Application.objects.filter(user=request.user)
        usage = UsageLedger.objects.filter(user=request.user)
        usage_agg = usage.aggregate(
            total_cost=Sum("cost_units"),
            total_sec=Sum("audio_duration_sec"),
            total_words=Sum("words_count"),
        )
        token_count = APIToken.objects.filter(application__in=apps).count()
        return Response(
            {
                "applications_count": apps.count(),
                "applications_active": apps.filter(is_active=True).count(),
                "api_tokens_count": token_count,
                "usage_total_audio_sec": float(usage_agg["total_sec"] or 0),
                "usage_total_words": int(usage_agg["total_words"] or 0),
                "usage_total_cost_units": float(usage_agg["total_cost"] or 0),
            }
        )


class UserJobsView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 10)), 1), 50)
        qs = ASRJob.objects.filter(user=request.user).order_by("-created_at")
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
        return Response(
            {
                "page": page,
                "page_size": page_size,
                "total": total,
                "results": items,
            }
        )


class UserJobDetailView(APIView):
    authentication_classes = [StrictJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = ASRJob.objects.filter(id=job_id, user=request.user).first()
        if not job:
            raise NotFound("Job not found.")
        payload = {
            "id": str(job.id),
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "audio_duration_sec": job.audio_duration_sec,
            "words_count": job.words_count,
            "chars_count": job.chars_count,
            "text": job.text,
            "error_code": job.error_code,
            "error_message_public": job.error_message_public,
        }
        return Response(payload)
