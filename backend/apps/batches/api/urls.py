from __future__ import annotations

from django.urls import path

from apps.batches.api.views import BatchExecutionView, BatchStepDetailView

app_name = "batches-api"

urlpatterns = [
    path(
        "<int:batch_id>/execution/",
        BatchExecutionView.as_view(),
        name="batch-execution",
    ),
    path(
        "steps/<int:step_id>/",
        BatchStepDetailView.as_view(),
        name="batch-step-detail",
    ),
]
