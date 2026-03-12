from __future__ import annotations

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from shared.api.views import HealthCheckView

app_name = "shared-api"


urlpatterns = [
    path("auth/", include("apps.authz.api.urls")),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "schema/docs/",
        SpectacularSwaggerView.as_view(url_name="shared-api:schema"),
        name="schema-docs",
    ),
]
