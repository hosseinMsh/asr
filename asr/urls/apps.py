from django.urls import path

from asr.views.apps import (
    ApplicationDeactivateView,
    ApplicationListCreateView,
    ApplicationUsageView,
    APITokenListCreateView,
    APITokenRevokeView,
)

urlpatterns = [
    path("", ApplicationListCreateView.as_view()),
    path("<uuid:app_id>/deactivate/", ApplicationDeactivateView.as_view()),
    path("<uuid:app_id>/usage/", ApplicationUsageView.as_view()),
    path("<uuid:app_id>/tokens/", APITokenListCreateView.as_view()),
    path("<uuid:app_id>/tokens/<uuid:token_id>/revoke/", APITokenRevokeView.as_view()),
]
