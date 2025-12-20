from rest_framework.exceptions import PermissionDenied
from asr.models import ASRJob

def get_job_for_request(request, job_id: int) -> ASRJob:
    qs = ASRJob.objects.filter(id=job_id)
    if request.user and request.user.is_authenticated:
        qs = qs.filter(user=request.user)
    else:
        if not request.session.session_key:
            raise PermissionDenied("No session")
        qs = qs.filter(session_key=request.session.session_key)
    job = qs.first()
    if not job:
        raise PermissionDenied("You do not own this job")
    return job
