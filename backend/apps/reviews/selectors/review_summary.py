"""Selector that composes the batch review summary from database queries.

Queries batch, step, signature, and checklist data, then delegates to
the domain layer for evaluation and severity derivation.
"""

from __future__ import annotations

from typing import Any

from django.db.models import Exists, OuterRef

from apps.batches.models import Batch, BatchStep, DossierChecklistItem, StepSignature
from apps.reviews.domain.review_summary import (
    ReviewSummary,
    build_flagged_steps,
    derive_traffic_light_severity,
    evaluate_checklist,
    evaluate_flag_counts,
    evaluate_step_completeness,
)


def _load_steps(batch: Batch) -> list[dict[str, Any]]:
    """Load step data with signature presence annotation."""
    steps_qs = (
        BatchStep.objects.filter(batch=batch)
        .annotate(
            has_signature=Exists(
                StepSignature.objects.filter(step=OuterRef("pk")),
            ),
        )
        .order_by("order")
        .values(
            "id",
            "reference",
            "status",
            "requires_signature",
            "required_data_complete",
            "changed_since_review",
            "changed_since_signature",
            "review_required",
            "has_open_exception",
            "open_exception_is_blocking",
            "has_signature",
        )
    )
    return list(steps_qs)


def _load_checklist(batch: Batch) -> list[dict[str, Any]]:
    """Load dossier checklist items for the batch."""
    qs = (
        DossierChecklistItem.objects.filter(batch=batch)
        .order_by("document_name")
        .values("document_name", "is_present")
    )
    return [dict(row) for row in qs]


def _resolve_batch(batch_or_id: Batch | int) -> Batch:
    if isinstance(batch_or_id, Batch):
        return batch_or_id
    return Batch.objects.select_related("site").get(pk=batch_or_id)


def get_batch_review_summary(batch_or_id: Batch | int) -> ReviewSummary:
    """Compute the complete review summary for a batch.

    Composes database queries with domain evaluation functions to produce
    a structured read model suitable for API serialisation.
    """
    batch = _resolve_batch(batch_or_id)
    steps = _load_steps(batch)
    checklist_items = _load_checklist(batch)

    step_summary = evaluate_step_completeness(steps)
    flags = evaluate_flag_counts(steps)
    checklist = evaluate_checklist(checklist_items)
    flagged_steps = build_flagged_steps(steps)
    severity = derive_traffic_light_severity(flags, step_summary)

    return ReviewSummary(
        batch_id=batch.pk,
        batch_reference=batch.reference,
        batch_status=batch.status,
        severity=severity,
        step_summary=step_summary,
        flags=flags,
        checklist=checklist,
        flagged_steps=flagged_steps,
    )
