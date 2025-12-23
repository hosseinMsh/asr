from django.urls import path
from asr.views.api import HealthView, UploadView, StatusView, ResultView, UsageView, HistoryView

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("upload/", UploadView.as_view()),
    path("status/<uuid:job_id>/", StatusView.as_view()),
    path("result/<uuid:job_id>/", ResultView.as_view()),
    path("usage/", UsageView.as_view()),
    path("history/", HistoryView.as_view()),
]
