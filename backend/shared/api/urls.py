from __future__ import annotations

from django.urls import include, path

from shared.api.views import (
    AuthenticatedSchemaDocsView,
    AuthenticatedSchemaView,
    HealthCheckView,
)

app_name = "shared-api"


urlpatterns = [
    path("auth/", include("apps.authz.api.urls")),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("schema/", AuthenticatedSchemaView.as_view(), name="schema"),
    path(
        "schema/docs/",
        AuthenticatedSchemaDocsView.as_view(url_name="shared-api:schema"),
        name="schema-docs",
    ),
    path("batches/", include("apps.batches.api.urls")),
]
