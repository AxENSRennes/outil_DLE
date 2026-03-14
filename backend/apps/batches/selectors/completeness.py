from __future__ import annotations

from collections import OrderedDict
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
    doc_reqs = BatchDocumentRequirement.objects.filter(batch=batch).order_by("document_code")

    counts_by_step_key: dict[str, dict[str, int]] = {}
    step_counts = (
        BatchStep.objects.filter(batch=batch)
        .values("step_key")
        .annotate(
            occurrence_count=Count("id"),
            actual_count=Count(
                "id",
                filter=Q(is_applicable=True, status__in=_COMPLETED_STATUSES),
            ),
        )
    )
    for row in step_counts:
        counts_by_step_key[row["step_key"]] = {
            "occurrence_count": row["occurrence_count"],
            "actual_count": row["actual_count"],
        }

    for doc_req in doc_reqs:
        counts = counts_by_step_key.get(doc_req.source_step_key, {})
        actual_count = counts.get("actual_count", 0)
        is_complete = True if not doc_req.is_applicable else actual_count >= doc_req.expected_count
        results.append(
            {
                "document_code": doc_req.document_code,
                "title": doc_req.title,
                "source_step_key": doc_req.source_step_key,
                "is_required": doc_req.is_required,
                "repeat_mode": doc_req.repeat_mode,
                "is_applicable": doc_req.is_applicable,
                "expected_count": doc_req.expected_count,
                "actual_count": actual_count,
                "is_complete": is_complete,
                "is_blocking": (doc_req.is_required and doc_req.is_applicable and not is_complete),
                "applicability_basis_json": doc_req.applicability_basis_json,
            }
        )
    return results


def get_grouped_steps(batch: Batch) -> list[dict[str, Any]]:
    """Return steps grouped by step_key in execution order."""

    steps = BatchStep.objects.filter(batch=batch).order_by("sequence_order")
    doc_reqs_map = {
        doc_req.document_code: doc_req
        for doc_req in BatchDocumentRequirement.objects.filter(batch=batch)
    }

    groups: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for step in steps:
        if step.step_key not in groups:
            doc_req = doc_reqs_map.get(step.step_key)
            groups[step.step_key] = {
                "step_key": step.step_key,
                "title": step.title,
                "repeat_mode": doc_req.repeat_mode if doc_req else "single",
                "is_applicable": doc_req.is_applicable if doc_req else step.is_applicable,
                "occurrences": [],
            }
        groups[step.step_key]["occurrences"].append(step)

    return list(groups.values())


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
