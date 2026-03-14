from __future__ import annotations

from django.urls import path

from apps.mmr.api.views import (
    MMRDetailView,
    MMRListCreateView,
    MMRVersionDetailView,
    MMRVersionListCreateView,
    StepDetailView,
    StepListCreateView,
    StepReorderView,
)

app_name = "mmr-api"

urlpatterns = [
    path("", MMRListCreateView.as_view(), name="mmr-list-create"),
    path("<int:mmr_id>/", MMRDetailView.as_view(), name="mmr-detail"),
    path(
        "<int:mmr_id>/versions/",
        MMRVersionListCreateView.as_view(),
        name="mmr-version-list-create",
    ),
    path(
        "<int:mmr_id>/versions/<int:version_id>/",
        MMRVersionDetailView.as_view(),
        name="mmr-version-detail",
    ),
    # Step endpoints (nested under version)
    path(
        "<int:mmr_id>/versions/<int:version_id>/steps/",
        StepListCreateView.as_view(),
        name="step-list-create",
    ),
    path(
        "<int:mmr_id>/versions/<int:version_id>/steps/reorder/",
        StepReorderView.as_view(),
        name="step-reorder",
    ),
    path(
        "<int:mmr_id>/versions/<int:version_id>/steps/<str:step_key>/",
        StepDetailView.as_view(),
        name="step-detail",
    ),
]
