from __future__ import annotations

from django.urls import path

from apps.authz.api.views import (
    AuthContextView,
    OperatorSiteAccessProbeView,
    SignatureReauthView,
    WorkstationIdentifyView,
    WorkstationLockView,
)

app_name = "authz-api"

urlpatterns = [
    path("context/", AuthContextView.as_view(), name="context"),
    path(
        "workstation-identify/",
        WorkstationIdentifyView.as_view(),
        name="workstation-identify",
    ),
    path(
        "workstation-lock/",
        WorkstationLockView.as_view(),
        name="workstation-lock",
    ),
    path(
        "signature-reauth/",
        SignatureReauthView.as_view(),
        name="signature-reauth",
    ),
    path(
        "sites/<slug:site_code>/operator-access/",
        OperatorSiteAccessProbeView.as_view(),
        name="operator-access-probe",
    ),
]
