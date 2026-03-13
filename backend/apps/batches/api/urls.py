from __future__ import annotations

from django.urls import path

from apps.batches.api.views import (
    BatchAddOccurrenceView,
    BatchComposeView,
    BatchDocumentRequirementsListView,
    BatchStepsListView,
)

app_name = "batches-api"

urlpatterns = [
    path(
        "<int:batch_id>/compose",
        BatchComposeView.as_view(),
        name="compose",
    ),
    path(
        "<int:batch_id>/steps",
        BatchStepsListView.as_view(),
        name="steps-list",
    ),
    path(
        "<int:batch_id>/steps/<str:step_key>/occurrences",
        BatchAddOccurrenceView.as_view(),
        name="add-occurrence",
    ),
    path(
        "<int:batch_id>/document-requirements",
        BatchDocumentRequirementsListView.as_view(),
        name="document-requirements-list",
    ),
]
