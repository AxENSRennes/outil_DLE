from __future__ import annotations

from django.urls import path

from apps.authz.api.views import AuthContextView

app_name = "authz-api"

urlpatterns = [
    path("context/", AuthContextView.as_view(), name="context"),
]
