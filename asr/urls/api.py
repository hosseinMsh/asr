from django.urls import path

from asr.asr_api.views import HealthView, UploadView, StatusView, ResultView

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("upload/", UploadView.as_view()),
    path("status/<uuid:job_id>/", StatusView.as_view()),
    path("result/<uuid:job_id>/", ResultView.as_view()),
]
