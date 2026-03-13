"""Foundation models for batch records.

These are minimal models introduced as FK targets for Epic 6 (dossier composition).
Epic 2 (Story 2.5) will expand the Batch model with full lifecycle, review, and
signature state fields.
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class BatchStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    READY = "ready", "Ready"
    IN_EXECUTION = "in_execution", "In execution"
    REVIEW_REQUIRED = "review_required", "Review required"
    UNDER_REVIEW = "under_review", "Under review"
    RELEASED = "released", "Released"
    REJECTED = "rejected", "Rejected"
    ARCHIVED = "archived", "Archived"


class Batch(models.Model):
    """An instantiated batch record created from an MMRVersion snapshot.

    Stores operational context (line, machine, format_family, paillette_present)
    in ``batch_context_json`` for dossier composition decisions.
    """

    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.PROTECT,
        related_name="batches",
    )
    mmr_version = models.ForeignKey(
        "mmr.MMRVersion",
        on_delete=models.PROTECT,
        related_name="batches",
    )
    batch_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=32,
        choices=BatchStatus.choices,
        default=BatchStatus.DRAFT,
    )
    batch_context_json = models.JSONField(default=dict, blank=True)
    snapshot_json = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_batches",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "batches"
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["site", "status"],
                name="batch_site_status_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.batch_number
