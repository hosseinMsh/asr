from django.urls import path
from asr.views.api import (
    DashboardOverviewView,
    HealthView,
    HistoryView,
    ResultView,
    StatusView,
    UploadView,
    UsageByAppView,
    UsageView,
)
from asr.views.apps import (
    ApplicationDetailView,
    ApplicationListCreateView,
    ApplicationTokenListCreateView,
    ApplicationTokenRevokeView,
)

urlpatterns = [
    path("health/", HealthView.as_view()),
    path("upload/", UploadView.as_view()),
    path("status/<uuid:job_id>/", StatusView.as_view()),
    path("result/<uuid:job_id>/", ResultView.as_view()),
    path("usage/", UsageView.as_view()),
    path("history/", HistoryView.as_view()),
    path("dashboard/overview/", DashboardOverviewView.as_view()),
    path("usage/by-app/", UsageByAppView.as_view()),
    path("jobs/", HistoryView.as_view()),
    path("asr/test-upload/", UploadView.as_view()),
    path("asr/jobs/", HistoryView.as_view()),
    path("asr/jobs/<uuid:job_id>/", ResultView.as_view()),
    path("apps/", ApplicationListCreateView.as_view()),
    path("apps/<uuid:app_id>/", ApplicationDetailView.as_view()),
    path("apps/<uuid:app_id>/tokens/", ApplicationTokenListCreateView.as_view()),
    path("apps/<uuid:app_id>/tokens/<uuid:token_id>/revoke/", ApplicationTokenRevokeView.as_view()),
]
