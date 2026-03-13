from __future__ import annotations

from django.urls import path

from apps.reviews.api.views import ReviewSummaryView
from apps.reviews.api.views_pre_qa import ConfirmPreQaReviewView, MarkStepReviewedView

app_name = "reviews"

urlpatterns = [
    path(
        "batches/<int:batch_id>/review-summary",
        ReviewSummaryView.as_view(),
        name="batch-review-summary",
    ),
    path(
        "batches/<int:batch_id>/pre-qa-review/confirm",
        ConfirmPreQaReviewView.as_view(),
        name="confirm-pre-qa-review",
    ),
    path(
        "batches/<int:batch_id>/review-items/<int:step_id>/mark-reviewed",
        MarkStepReviewedView.as_view(),
        name="mark-step-reviewed",
    ),
]
