from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.db import models


class BatchStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    IN_PROGRESS = "in_progress", "In Progress"
    AWAITING_PRE_QA = "awaiting_pre_qa", "Awaiting Pre-QA"
    IN_PRE_QA_REVIEW = "in_pre_qa_review", "In Pre-QA Review"
    AWAITING_QUALITY_REVIEW = "awaiting_quality_review", "Awaiting Quality Review"
    IN_QUALITY_REVIEW = "in_quality_review", "In Quality Review"
    RETURNED_FOR_CORRECTION = "returned_for_correction", "Returned for Correction"
    RELEASED = "released", "Released"
    REJECTED = "rejected", "Rejected"


class BatchStepStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not Started"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETE = "complete", "Complete"
    SIGNED = "signed", "Signed"


# Alias so the reviews app can import StepStatus without changes.
StepStatus = BatchStepStatus


class StepSignatureState(models.TextChoices):
    NOT_REQUIRED = "not_required", "Not Required"
    REQUIRED = "required", "Required"
    SIGNED = "signed", "Signed"


class Batch(models.Model):
    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.PROTECT,
        related_name="batches",
    )
    # mmr_version_id stored as integer until Epic 2 provides the MMRVersion model.
    mmr_version_id = models.PositiveIntegerField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=32,
        choices=BatchStatus.choices,
        default=BatchStatus.DRAFT,
    )
    snapshot_json = models.JSONField()
    lot_size_target = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    lot_size_actual = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    batch_context_json = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_batches",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "batches"

    def __str__(self) -> str:
        return self.batch_number


class BatchStep(models.Model):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    step_key = models.CharField(max_length=100)
    occurrence_key = models.CharField(max_length=100, default="default")
    occurrence_index = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    sequence_order = models.PositiveIntegerField()
    is_applicable = models.BooleanField(default=True)
    status = models.CharField(
        max_length=32,
        choices=BatchStepStatus.choices,
        default=BatchStepStatus.NOT_STARTED,
    )
    signature_state = models.CharField(
        max_length=32,
        choices=StepSignatureState.choices,
        default=StepSignatureState.NOT_REQUIRED,
    )
    blocks_execution_progress = models.BooleanField(default=False)
    blocks_step_completion = models.BooleanField(default=True)
    blocks_signature = models.BooleanField(default=False)
    blocks_pre_qa_handoff = models.BooleanField(default=True)
    # Review-tracking fields (used by review summary feature).
    required_data_complete = models.BooleanField(default=True)
    changed_since_review = models.BooleanField(default=False)
    changed_since_signature = models.BooleanField(default=False)
    review_required = models.BooleanField(default=False)
    has_open_exception = models.BooleanField(default=False)
    open_exception_is_blocking = models.BooleanField(default=False)
    data_json = models.JSONField(default=dict)
    meta_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="edited_batch_steps",
        null=True,
        blank=True,
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["sequence_order"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["batch", "step_key", "occurrence_key"],
                name="uniq_batch_step_occurrence",
            )
        ]

    def __str__(self) -> str:
        return f"{self.batch.batch_number} / {self.step_key} / {self.occurrence_key}"


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
        return f"{self.step.title} signed by {self.signer} ({self.meaning})"


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
