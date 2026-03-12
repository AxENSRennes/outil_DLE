from __future__ import annotations

from django.urls import path

from apps.authz.api.views import AuthContextView, OperatorSiteAccessProbeView

app_name = "authz-api"

urlpatterns = [
    path("context/", AuthContextView.as_view(), name="context"),
    path(
        "sites/<slug:site_code>/operator-access/",
        OperatorSiteAccessProbeView.as_view(),
        name="operator-access-probe",
    ),
]
