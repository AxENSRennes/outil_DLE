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


class BatchStepStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not started"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    SIGNED = "signed", "Signed"
    FLAGGED = "flagged", "Flagged"
    UNDER_REVIEW = "under_review", "Under review"
    APPROVED = "approved", "Approved"


class StepReviewState(models.TextChoices):
    NONE = "none", "None"
    REQUIRED = "required", "Required"
    IN_REVIEW = "in_review", "In review"
    APPROVED = "approved", "Approved"
    CHANGED = "changed", "Changed"


class StepSignatureState(models.TextChoices):
    NOT_REQUIRED = "not_required", "Not required"
    REQUIRED = "required", "Required"
    SIGNED = "signed", "Signed"
    CHANGED = "changed", "Changed"


class ReviewState(models.TextChoices):
    NONE = "none", "None"
    REQUIRED = "required", "Required"
    IN_REVIEW = "in_review", "In review"
    REVIEWED = "reviewed", "Reviewed"
    CHANGED_SINCE_REVIEW = "changed_since_review", "Changed since review"


class SignatureState(models.TextChoices):
    NONE = "none", "None"
    REQUIRED = "required", "Required"
    PARTIALLY_SIGNED = "partially_signed", "Partially signed"
    SIGNED = "signed", "Signed"
    CHANGED_SINCE_SIGNATURE = "changed_since_signature", "Changed since signature"


class BatchDocumentStatus(models.TextChoices):
    EXPECTED = "expected", "Expected"
    PRESENT = "present", "Present"
    MISSING = "missing", "Missing"


class BatchDocumentRepeatMode(models.TextChoices):
    SINGLE = "single", "Single"
    PER_SHIFT = "per_shift", "Per shift"
    PER_TEAM = "per_team", "Per team"
    PER_BOX = "per_box", "Per box"
    PER_EVENT = "per_event", "Per event"


class Batch(models.Model):
    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.PROTECT,
        related_name="batches",
    )
    batch_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=32,
        choices=BatchStatus.choices,
        default=BatchStatus.DRAFT,
    )
    review_state = models.CharField(
        max_length=32,
        choices=ReviewState.choices,
        default=ReviewState.NONE,
    )
    signature_state = models.CharField(
        max_length=32,
        choices=SignatureState.choices,
        default=SignatureState.NONE,
    )
    lot_size_target = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True
    )
    lot_size_actual = models.DecimalField(
        max_digits=12, decimal_places=3, null=True, blank=True
    )
    snapshot_json = models.JSONField()
    batch_context_json = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    review_started_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_batches",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_batches",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    occurrence_key = models.CharField(max_length=200, default="default")
    occurrence_index = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    sequence_order = models.PositiveIntegerField()
    source_document_code = models.CharField(max_length=100, blank=True)
    is_applicable = models.BooleanField(default=True)
    applicability_basis_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=32,
        choices=BatchStepStatus.choices,
        default=BatchStepStatus.NOT_STARTED,
    )
    review_state = models.CharField(
        max_length=32,
        choices=StepReviewState.choices,
        default=StepReviewState.NONE,
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
    data_json = models.JSONField(default=dict, blank=True)
    meta_json = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="edited_batch_steps",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sequence_order",)
        constraints: ClassVar[tuple[models.BaseConstraint, ...]] = (
            models.UniqueConstraint(
                fields=("batch", "step_key", "occurrence_key"),
                name="uniq_batch_step_occurrence",
            ),
        )

    def __str__(self) -> str:
        return f"{self.batch.batch_number} / {self.step_key} / {self.occurrence_key}"


class BatchDocumentRequirement(models.Model):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="document_requirements",
    )
    document_code = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    source_step_key = models.CharField(max_length=100, blank=True)
    is_required = models.BooleanField(default=True)
    is_applicable = models.BooleanField(default=True)
    repeat_mode = models.CharField(
        max_length=32,
        choices=BatchDocumentRepeatMode.choices,
        default=BatchDocumentRepeatMode.SINGLE,
    )
    expected_count = models.PositiveIntegerField(default=1)
    actual_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=32,
        choices=BatchDocumentStatus.choices,
        default=BatchDocumentStatus.EXPECTED,
    )
    applicability_basis_json = models.JSONField(default=dict, blank=True)
    meta_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints: ClassVar[tuple[models.BaseConstraint, ...]] = (
            models.UniqueConstraint(
                fields=("batch", "document_code"),
                name="uniq_batch_document_requirement",
            ),
        )

    def __str__(self) -> str:
        return f"{self.batch.batch_number} / {self.document_code}"
