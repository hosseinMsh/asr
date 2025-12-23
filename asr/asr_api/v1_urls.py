from django.urls import path

from asr.asr_api.views import HealthView, UploadView, StatusView, ResultView

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("asr/upload/", UploadView.as_view()),
    path("asr/jobs/<uuid:job_id>/", ResultView.as_view()),
    path("asr/jobs/<uuid:job_id>/status/", StatusView.as_view()),
]
