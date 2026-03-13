"""Foundation models for batch records.

These are stub models combining the minimal schema needed by both the
dossier-composition feature (Epic 6, Story 6.1) and the review-summary
feature (Epic 5, Story 5.1).  They will be replaced with full
implementations when Epics 2-4 are developed.
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class BatchStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    READY = "ready", "Ready"
    IN_EXECUTION = "in_execution", "In execution"
    IN_PROGRESS = "in_progress", "In Progress"
    AWAITING_PRE_QA = "awaiting_pre_qa", "Awaiting Pre-QA"
    IN_PRE_QA_REVIEW = "in_pre_qa_review", "In Pre-QA Review"
    AWAITING_QUALITY_REVIEW = "awaiting_quality_review", "Awaiting Quality Review"
    IN_QUALITY_REVIEW = "in_quality_review", "In Quality Review"
    RETURNED_FOR_CORRECTION = "returned_for_correction", "Returned for Correction"
    REVIEW_REQUIRED = "review_required", "Review required"
    UNDER_REVIEW = "under_review", "Under review"
    RELEASED = "released", "Released"
    REJECTED = "rejected", "Rejected"
    ARCHIVED = "archived", "Archived"


class StepStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not Started"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETE = "complete", "Complete"
    SIGNED = "signed", "Signed"


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
        ordering = ("-created_at",)
        verbose_name_plural = "batches"
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["site", "status"],
                name="batch_site_status_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.batch_number


class BatchStep(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveIntegerField()
    reference = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=StepStatus.choices,
        default=StepStatus.NOT_STARTED,
    )
    requires_signature = models.BooleanField(default=False)
    required_data_complete = models.BooleanField(default=True)
    changed_since_review = models.BooleanField(default=False)
    changed_since_signature = models.BooleanField(default=False)
    review_required = models.BooleanField(default=False)
    has_open_exception = models.BooleanField(default=False)
    open_exception_is_blocking = models.BooleanField(default=False)

    class Meta:
        ordering = ("batch", "order")
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("batch", "order"),
                name="batches_unique_step_order",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.reference} ({self.status})"


class StepSignature(models.Model):
    step = models.ForeignKey(BatchStep, on_delete=models.PROTECT, related_name="signatures")
    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="step_signatures",
    )
    meaning = models.CharField(max_length=50)
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-signed_at",)

    def __str__(self) -> str:
        return f"{self.step.reference} signed by {self.signer} ({self.meaning})"


class DossierChecklistItem(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="checklist_items")
    document_name = models.CharField(max_length=200)
    is_present = models.BooleanField(default=False)

    class Meta:
        ordering = ("document_name",)
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=("batch", "document_name"),
                name="batches_unique_checklist_document",
            ),
        ]

    def __str__(self) -> str:
        status = "present" if self.is_present else "missing"
        return f"{self.document_name} ({status})"
