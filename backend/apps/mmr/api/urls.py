from __future__ import annotations

from django.urls import path

from apps.mmr.api.views import (
    MMRDetailView,
    MMRListCreateView,
    MMRVersionDetailView,
    MMRVersionListCreateView,
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
]
