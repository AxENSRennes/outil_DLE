from __future__ import annotations

from typing import Any, ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditEventType(models.TextChoices):
    IDENTIFY = "identify", "Identify"
    SWITCH_USER = "switch_user", "Switch User"
    LOCK_WORKSTATION = "lock_workstation", "Lock Workstation"
    LOCK_FAILED = "lock_failed", "Lock Failed"
    IDENTIFY_FAILED = "identify_failed", "Identify Failed"
    SIGNATURE_REAUTH_SUCCEEDED = "signature_reauth_succeeded", "Signature Reauth Succeeded"
    SIGNATURE_REAUTH_FAILED = "signature_reauth_failed", "Signature Reauth Failed"
    LOCK_FAILED = "lock_failed", "Lock Failed"

    # Batch-domain event types
    BATCH_CREATED = "batch_created", "Batch Created"
    STEP_DRAFT_SAVED = "step_draft_saved", "Step Draft Saved"
    STEP_COMPLETED = "step_completed", "Step Completed"
    STEP_SIGNED = "step_signed", "Step Signed"
    BATCH_SUBMITTED_FOR_PRE_QA = (
        "batch_submitted_for_pre_qa",
        "Batch Submitted for Pre-QA",
    )
    PRE_QA_REVIEW_CONFIRMED = "pre_qa_review_confirmed", "Pre-QA Review Confirmed"
    QUALITY_REVIEW_STARTED = "quality_review_started", "Quality Review Started"
    BATCH_RELEASED = "batch_released", "Batch Released"
    BATCH_REJECTED = "batch_rejected", "Batch Rejected"
    BATCH_RETURNED_FOR_CORRECTION = (
        "batch_returned_for_correction",
        "Batch Returned for Correction",
    )
    CORRECTION_SUBMITTED = "correction_submitted", "Correction Submitted"
    CHANGE_REVIEWED = "change_reviewed", "Change Reviewed"


AUTH_OPTIONAL_ACTOR_EVENT_TYPES: tuple[str, ...] = (
    AuditEventType.IDENTIFY,
    AuditEventType.SWITCH_USER,
    AuditEventType.LOCK_WORKSTATION,
    AuditEventType.IDENTIFY_FAILED,
    AuditEventType.SIGNATURE_REAUTH_SUCCEEDED,
    AuditEventType.SIGNATURE_REAUTH_FAILED,
    AuditEventType.LOCK_FAILED,
)

BATCH_DOMAIN_EVENT_TYPES: tuple[str, ...] = tuple(
    event_type.value
    for event_type in AuditEventType
    if event_type.value not in AUTH_OPTIONAL_ACTOR_EVENT_TYPES
)


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    site = models.ForeignKey(
        "sites.Site",
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=64, choices=AuditEventType.choices)
    occurred_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    target_type = models.CharField(max_length=64, blank=True, default="")
    target_id = models.PositiveIntegerField(null=True, blank=True)

    def clean(self) -> None:
        super().clean()
        self.target_type = self.target_type.strip()

        if self.event_type in BATCH_DOMAIN_EVENT_TYPES and self.actor_id is None:
            raise ValidationError(
                {"actor": "This field is required for batch-domain audit events."}
            )
        if self.target_id is not None and not self.target_type:
            raise ValidationError(
                {"target_type": "This field is required when target_id is provided."}
            )
        if self.target_type and self.target_id is None:
            raise ValidationError(
                {"target_id": "This field is required when target_type is provided."}
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.target_type = self.target_type.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ("-occurred_at", "-id")
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["event_type", "occurred_at"],
                name="audit_event_type_occurred_idx",
            ),
            models.Index(
                fields=["target_type", "target_id"],
                name="audit_target_type_id_idx",
            ),
            models.Index(
                fields=["actor", "occurred_at"],
                name="audit_actor_occurred_idx",
            ),
        ]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.CheckConstraint(
                check=(
                    models.Q(target_type="", target_id__isnull=True)
                    | (~models.Q(target_type="") & models.Q(target_id__isnull=False))
                ),
                name="audit_target_type_id_consistent",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(event_type__in=AUTH_OPTIONAL_ACTOR_EVENT_TYPES)
                    | models.Q(actor__isnull=False)
                ),
                name="audit_batch_event_actor_required",
            ),
            models.CheckConstraint(
                check=(models.Q(target_id__isnull=True) | ~models.Q(target_type__regex=r"^\s*$")),
                name="audit_target_type_not_blank_when_linked",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.occurred_at.isoformat()}"
