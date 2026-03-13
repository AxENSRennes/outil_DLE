"""Domain services for pre-QA review workflow.

Handles confirming pre-QA review (handoff to quality) and marking
individual step review items as reviewed.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audit.models import AuditEvent, AuditEventType
from apps.authz.models import User
from apps.batches.models import Batch, BatchStatus, BatchStep
from apps.reviews.models import ReviewEvent, ReviewEventType
from apps.reviews.selectors.review_summary import get_batch_review_summary

_VALID_PRE_QA_STATUSES = (BatchStatus.AWAITING_PRE_QA, BatchStatus.IN_PRE_QA_REVIEW)


@dataclass(frozen=True)
class ConfirmPreQaResult:
    batch: Batch
    review_event: ReviewEvent


@dataclass(frozen=True)
class MarkStepReviewedResult:
    step: BatchStep
    batch_status: str
    flags_cleared: tuple[str, ...]
    review_event: ReviewEvent


def _validate_pre_qa_batch_status(batch: Batch) -> None:
    if batch.status not in _VALID_PRE_QA_STATUSES:
        raise ValidationError(
            "Batch must be in awaiting_pre_qa or in_pre_qa_review status.",
            code="invalid_batch_state",
        )


def _validate_reviewable_step(*, batch: Batch, step: BatchStep) -> None:
    if step.batch_id != batch.pk:
        raise ValidationError(
            "Step does not belong to the specified batch.",
            code="step_not_in_batch",
        )

    # changed_since_signature is a persistent integrity marker cleared only by
    # re-signing, not by review. Only clearable flags make a step actionable.
    if not (step.changed_since_review or step.review_required):
        raise ValidationError(
            "Step has no reviewable flags to clear.",
            code="no_reviewable_flags",
        )


def confirm_pre_qa_review(
    *,
    batch: Batch,
    reviewer: User,
    note: str = "",
) -> ConfirmPreQaResult:
    """Confirm that the batch is ready for quality handoff.

    Validates batch status and severity, creates a ReviewEvent, transitions
    the batch to ``awaiting_quality_review``, and records an audit event.

    Raises ``ValidationError`` when the batch is not in a valid state or
    when red-severity blocking conditions remain.
    """
    _validate_pre_qa_batch_status(batch)

    review_event: ReviewEvent | None = None
    committed = False
    try:
        with transaction.atomic():
            # Lock the batch row to prevent concurrent confirms (TOCTOU).
            batch = Batch.objects.select_for_update().get(pk=batch.pk)
            _validate_pre_qa_batch_status(batch)

            summary = get_batch_review_summary(batch)
            if summary.severity == "red":
                raise ValidationError(
                    "Cannot confirm pre-QA review: blocking issues remain "
                    "(missing required data, missing required signatures, "
                    "or blocking open exceptions).",
                    code="pre_qa_review_blocked",
                )

            review_event = ReviewEvent.objects.create(
                batch=batch,
                reviewer=reviewer,
                event_type=ReviewEventType.PRE_QA_CONFIRMED,
                note=note,
            )

            batch.status = BatchStatus.AWAITING_QUALITY_REVIEW
            batch.save(update_fields=["status", "updated_at"])
            committed = True
    finally:
        AuditEvent.objects.create(
            actor=reviewer,
            site=batch.site,
            event_type=AuditEventType.PRE_QA_REVIEW_CONFIRMED,
            metadata={
                "batch_id": batch.pk,
                "batch_reference": batch.reference,
                "reviewer_id": reviewer.pk,
                "note": note,
                "review_event_id": (
                    review_event.pk if review_event and committed else None
                ),
            },
        )

    return ConfirmPreQaResult(batch=batch, review_event=review_event)


def mark_step_reviewed(
    *,
    batch: Batch,
    step: BatchStep,
    reviewer: User,
    note: str = "",
) -> MarkStepReviewedResult:
    """Mark a flagged step as reviewed during pre-QA.

    Clears ``changed_since_review`` and ``review_required`` flags,
    transitions the batch to ``in_pre_qa_review`` if needed, creates
    a ReviewEvent, and records an audit event.

    Note: ``changed_since_signature`` is a persistent integrity marker
    that is only cleared by re-signing, not by review.  It does not
    make a step actionable for mark-reviewed on its own.

    Raises ``ValidationError`` when the batch status or step state is
    not appropriate.
    """
    _validate_pre_qa_batch_status(batch)
    _validate_reviewable_step(batch=batch, step=step)

    flags_cleared: list[str] = []
    review_event: ReviewEvent | None = None
    committed = False
    try:
        with transaction.atomic():
            # Lock rows to prevent concurrent reviews of the same step.
            batch = Batch.objects.select_for_update().get(pk=batch.pk)
            step = BatchStep.objects.select_for_update().get(pk=step.pk)
            _validate_pre_qa_batch_status(batch)
            _validate_reviewable_step(batch=batch, step=step)

            # Clear flags after lock acquisition (step was re-fetched).
            if step.changed_since_review:
                step.changed_since_review = False
                flags_cleared.append("changed_since_review")
            if step.review_required:
                step.review_required = False
                flags_cleared.append("review_required")

            step.save(update_fields=["changed_since_review", "review_required"])

            if batch.status == BatchStatus.AWAITING_PRE_QA:
                batch.status = BatchStatus.IN_PRE_QA_REVIEW
                batch.save(update_fields=["status", "updated_at"])

            review_event = ReviewEvent.objects.create(
                batch=batch,
                reviewer=reviewer,
                event_type=ReviewEventType.CHANGE_MARKED_REVIEWED,
                step=step,
                note=note,
            )
            committed = True
    finally:
        AuditEvent.objects.create(
            actor=reviewer,
            site=batch.site,
            event_type=AuditEventType.REVIEW_ITEM_MARKED_REVIEWED,
            metadata={
                "batch_id": batch.pk,
                "step_id": step.pk,
                "step_reference": step.reference,
                "reviewer_id": reviewer.pk,
                "flags_cleared": flags_cleared,
                "review_event_id": (
                    review_event.pk if review_event and committed else None
                ),
            },
        )

    return MarkStepReviewedResult(
        step=step,
        batch_status=batch.status,
        flags_cleared=tuple(flags_cleared),
        review_event=review_event,
    )
