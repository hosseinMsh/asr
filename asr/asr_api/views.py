import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from asr.applications.authentication import APITokenAuthentication
from asr.asr_api import services
from asr.asr_api.serializers import (
    UploadRequestSerializer,
    UploadResponseSerializer,
    StatusResponseSerializer,
    ResultResponseSerializer,
    UsageResponseSerializer,
    HistoryResponseSerializer,
)
from asr.common.errors import error_response
from asr.usage.services import usage_summary_for_application


class HealthView(APIView):
    authentication_classes = [APITokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["asr"], auth=[{"ApiTokenAuth": []}], responses={200: OpenApiResponse(response=None)})
    def get(self, request):
        return Response({"status": "ok"})


class UploadView(APIView):
    authentication_classes = [APITokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["asr"],
        auth=[{"ApiTokenAuth": []}],
        request=UploadRequestSerializer,
        responses={200: UploadResponseSerializer},
        examples=[
            OpenApiExample(
                "Upload response",
                value={"job_id": "uuid", "status": "queued"},
                response_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = UploadRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        audio_file = serializer.validated_data["audio_file"]
        language = serializer.validated_data.get("language", "fa")
        plan = services.get_plan_for_user(request.user)
        job, error = services.create_job(request.application, request.user, audio_file, language, plan)
        if error:
            return error_response(error["code"], error["message"], status_code=error["status_code"])
        return Response(UploadResponseSerializer({"job_id": job.id, "status": job.status}).data)


class StatusView(APIView):
    authentication_classes = [APITokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["asr"],
        auth=[{"ApiTokenAuth": []}],
        responses={200: StatusResponseSerializer},
    )
    def get(self, request, job_id: uuid.UUID):
        job = services.get_job_for_application(request.application, job_id)
        if not job:
            return error_response("FORBIDDEN", "You do not own this job.", status_code=403)
        payload = services.build_status_payload(job)
        return Response(StatusResponseSerializer(payload).data)


class ResultView(APIView):
    authentication_classes = [APITokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["asr"],
        auth=[{"ApiTokenAuth": []}],
        responses={
            200: ResultResponseSerializer,
            202: OpenApiResponse(description="Job pending"),
            400: OpenApiResponse(description="Processing failed"),
        },
    )
    def get(self, request, job_id: uuid.UUID):
        job = services.get_job_for_application(request.application, job_id)
        if not job:
            return error_response("FORBIDDEN", "You do not own this job.", status_code=403)
        if job.status != "done":
            if job.status in ("queued", "processing"):
                return error_response("JOB_PENDING", "Job is still processing.", status_code=202)
            return error_response(
                job.error_code or "PROCESSING_FAILED",
                job.error_message_public or "Processing failed.",
                status_code=400,
            )
        payload = services.build_result_payload(job)
        return Response(ResultResponseSerializer(payload).data)


class UsageView(APIView):
    authentication_classes = [APITokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["usage"],
        auth=[{"ApiTokenAuth": []}],
        responses={200: UsageResponseSerializer},
    )
    def get(self, request):
        summary = usage_summary_for_application(request.application)
        return Response(UsageResponseSerializer(summary).data)


class HistoryView(APIView):
    authentication_classes = [APITokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["asr"],
        auth=[{"ApiTokenAuth": []}],
        responses={200: HistoryResponseSerializer},
    )
    def get(self, request):
        plan = services.get_plan_for_user(request.user)
        page = max(int(request.query_params.get("page", 1)), 1)
        page_size = min(max(int(request.query_params.get("page_size", 10)), 1), 50)
        payload = services.history_page(request.application, plan, page, page_size)
        return Response(HistoryResponseSerializer(payload).data)
