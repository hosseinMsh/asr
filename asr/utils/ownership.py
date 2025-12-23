import uuid

from rest_framework.exceptions import PermissionDenied
from asr.models import ASRJob

def get_job_for_request(request, job_id: uuid.UUID) -> ASRJob:
    qs = ASRJob.objects.filter(id=job_id, application=request.application)
    job = qs.first()
    if not job:
        raise PermissionDenied("You do not own this job")
    return job
