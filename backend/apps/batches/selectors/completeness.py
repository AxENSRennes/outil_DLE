from __future__ import annotations

from typing import Any

from django.db.models import Count, Q

from apps.batches.models import (
    Batch,
    BatchDocumentRequirement,
    BatchStep,
    BatchStepStatus,
)

# Statuses considered "completed" for completeness calculations
_COMPLETED_STATUSES = (
    BatchStepStatus.COMPLETED,
    BatchStepStatus.SIGNED,
    BatchStepStatus.FLAGGED,
    BatchStepStatus.UNDER_REVIEW,
    BatchStepStatus.APPROVED,
)


def get_step_completeness_by_group(batch: Batch) -> list[dict[str, Any]]:
    """Return per-step_key completeness counts, including only applicable steps."""
    return list(
        BatchStep.objects.filter(batch=batch, is_applicable=True)
        .values("step_key")
        .annotate(
            total=Count("id"),
            completed=Count("id", filter=Q(status__in=_COMPLETED_STATUSES)),
            incomplete=Count("id", filter=~Q(status__in=_COMPLETED_STATUSES)),
        )
        .order_by("step_key")
    )


def get_document_requirement_completeness(batch: Batch) -> list[dict[str, Any]]:
    """Return per-document-requirement completeness data."""
    results = []
    doc_reqs = BatchDocumentRequirement.objects.filter(batch=batch).order_by(
        "document_code"
    )

    # Pre-compute completed counts per step_key in one query
    completed_map: dict[str, int] = {}
    step_counts = (
        BatchStep.objects.filter(batch=batch, is_applicable=True)
        .values("step_key")
        .annotate(completed=Count("id", filter=Q(status__in=_COMPLETED_STATUSES)))
    )
    for row in step_counts:
        completed_map[row["step_key"]] = row["completed"]

    for doc_req in doc_reqs:
        completed_count = completed_map.get(doc_req.source_step_key, 0)
        results.append(
            {
                "document_code": doc_req.document_code,
                "title": doc_req.title,
                "repeat_mode": doc_req.repeat_mode,
                "is_applicable": doc_req.is_applicable,
                "expected_count": doc_req.expected_count,
                "actual_completed": completed_count,
                "is_complete": completed_count >= doc_req.expected_count
                and doc_req.is_applicable,
            }
        )
    return results


def get_occurrence_details(batch: Batch, step_key: str) -> list[dict[str, Any]]:
    """Return individual occurrence status for a given step_key."""
    qs = (
        BatchStep.objects.filter(batch=batch, step_key=step_key)
        .values(
            "id",
            "occurrence_key",
            "occurrence_index",
            "is_applicable",
            "status",
            "review_state",
            "signature_state",
        )
        .order_by("occurrence_index")
    )
    return [dict(row) for row in qs]
