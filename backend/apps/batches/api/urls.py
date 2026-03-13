from __future__ import annotations

from django.urls import path

from apps.batches.api.views import SubmitCorrectionView

app_name = "batches"

urlpatterns = [
    path(
        "batches/<int:batch_id>/steps/<int:step_id>/corrections",
        SubmitCorrectionView.as_view(),
        name="submit-correction",
    ),
]
