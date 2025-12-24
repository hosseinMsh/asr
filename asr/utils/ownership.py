import uuid

from rest_framework.exceptions import PermissionDenied
from asr.models import ASRJob
from asr.utils.auth import get_request_sid

def get_job_for_request(request, job_id: uuid.UUID) -> ASRJob:
    qs = ASRJob.objects.filter(id=job_id, application__isnull=True)
    if request.user and request.user.is_authenticated:
        qs = qs.filter(user=request.user)
    else:
        sid = get_request_sid(request)
        if not sid:
            raise PermissionDenied("No session")
        qs = qs.filter(session_key=sid)
    job = qs.first()
    if not job:
        raise PermissionDenied("You do not own this job")
    return job


def get_app_job_for_request(request, job_id: uuid.UUID) -> ASRJob:
    application = getattr(request, "application", None)
    if not application:
        raise PermissionDenied("No application")
    job = ASRJob.objects.filter(id=job_id, application=application).first()
    if not job:
        raise PermissionDenied("You do not own this job")
    return job
