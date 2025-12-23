from django.urls import path

from asr.usage.views import (
    UserUsageView,
    UserUsageByAppView,
    UserJobsView,
    UserJobDetailView,
    DashboardOverviewView,
)

urlpatterns = [
    path("dashboard/overview/", DashboardOverviewView.as_view()),
    path("usage/", UserUsageView.as_view()),
    path("usage/by-app/", UserUsageByAppView.as_view()),
    path("jobs/", UserJobsView.as_view()),
    path("jobs/<uuid:job_id>/", UserJobDetailView.as_view()),
    path("history/", UserJobsView.as_view()),
]
