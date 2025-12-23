import uuid

from rest_framework.exceptions import PermissionDenied

from asr.asr_api.services import get_job_for_application


def get_job_for_request(request, job_id: uuid.UUID):
    job = get_job_for_application(request.application, job_id)
    if not job:
        raise PermissionDenied("You do not own this job")
    return job
