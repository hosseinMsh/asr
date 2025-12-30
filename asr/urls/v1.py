from django.urls import path

from asr.views.app_api import AppHealthView, AppUploadView, AppStatusView, AppResultView
from asr.views.profile import ChangePasswordView, CurrentUserProfileView, UpdateUserProfileView

urlpatterns = [
    path("health/", AppHealthView.as_view()),
    path("asr/upload/", AppUploadView.as_view()),
    path("asr/jobs/<uuid:job_id>/", AppResultView.as_view()),
    path("asr/jobs/<uuid:job_id>/status/", AppStatusView.as_view()),

    # user profile settings
    path("users/me/", CurrentUserProfileView.as_view()),
    path("users/me/update/", UpdateUserProfileView.as_view()),
    path("users/me/change-password/", ChangePasswordView.as_view()),
]
