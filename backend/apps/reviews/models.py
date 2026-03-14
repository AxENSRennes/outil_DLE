from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class ReviewEventType(models.TextChoices):
    PRE_QA_CONFIRMED = "pre_qa_confirmed", "Pre-QA Confirmed"
    CHANGE_MARKED_REVIEWED = "change_marked_reviewed", "Change Marked Reviewed"


class ReviewEvent(models.Model):
    batch = models.ForeignKey(
        "batches.Batch",
        on_delete=models.PROTECT,
        related_name="review_events",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="review_events",
    )
    event_type = models.CharField(max_length=64, choices=ReviewEventType.choices)
    step = models.ForeignKey(
        "batches.BatchStep",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="review_events",
    )
    note = models.TextField(blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-occurred_at", "-id")
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["event_type", "occurred_at"],
                name="review_event_type_occurred_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.occurred_at.isoformat()}"
