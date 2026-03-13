from __future__ import annotations

from django.urls import path

from apps.reviews.api.views import ReviewSummaryView

app_name = "reviews"

urlpatterns = [
    path(
        "batches/<int:batch_id>/review-summary/",
        ReviewSummaryView.as_view(),
        name="batch-review-summary",
    ),
]
