from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import Max

from apps.batches.domain.template_rules import resolve_step_definition
from apps.batches.models import (
    Batch,
    BatchDocumentRequirement,
    BatchStep,
    BatchStepStatus,
)


class OccurrenceError(Exception):
    def __init__(
        self,
        detail: str,
        *,
        code: str = "occurrence_error",
        status_code: int = 400,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code
        self.status_code = status_code


@transaction.atomic
def add_occurrence(batch: Batch, step_key: str) -> BatchStep:
    """Add a new occurrence of a repeated step.

    Validates that the step's repeat policy allows additional occurrences
    and creates the next BatchStep record with incremented occurrence_index.
    """
    snapshot = batch.snapshot_json
    if not snapshot:
        raise OccurrenceError("Batch has no template snapshot.")

    try:
        resolved_step = resolve_step_definition(
            snapshot,
            batch.batch_context_json or {},
            step_key,
        )
    except ValueError as exc:
        raise OccurrenceError(str(exc)) from exc
    except KeyError as exc:
        raise OccurrenceError(str(exc)) from exc

    if resolved_step.repeat_mode == "single":
        raise OccurrenceError(
            f"Step '{step_key}' has repeat mode 'single' and does not support "
            f"additional occurrences."
        )

    if resolved_step.is_hidden:
        raise OccurrenceError(
            f"Step '{step_key}' is hidden for the current batch context.",
            code="occurrence_not_applicable",
        )

    if not resolved_step.is_applicable:
        raise OccurrenceError(
            f"Step '{step_key}' is not applicable for the current batch context.",
            code="occurrence_not_applicable",
        )

    existing_steps = BatchStep.objects.select_for_update().filter(
        batch=batch,
        step_key=step_key,
    )
    current_count = existing_steps.count()

    if resolved_step.max_records is not None and current_count >= resolved_step.max_records:
        raise OccurrenceError(
            f"Step '{step_key}' has reached the maximum of {resolved_step.max_records} occurrences."
        )

    max_index = existing_steps.aggregate(max_idx=Max("occurrence_index"))["max_idx"] or 0
    next_index = max_index + 1

    occurrence_key = f"{step_key}_{resolved_step.repeat_mode}_{next_index}"

    # Derive sequence_order from the last existing step for this key
    last_step = existing_steps.order_by("-sequence_order").first()
    sequence_order = (last_step.sequence_order + 1) if last_step else next_index

    try:
        new_step = BatchStep.objects.create(
            batch=batch,
            step_key=step_key,
            occurrence_key=occurrence_key,
            occurrence_index=next_index,
            title=resolved_step.title,
            sequence_order=sequence_order,
            source_document_code=step_key,
            is_applicable=resolved_step.is_applicable,
            applicability_basis_json=resolved_step.applicability_basis,
            status=BatchStepStatus.NOT_STARTED,
            signature_state=resolved_step.signature_state,
            blocks_execution_progress=resolved_step.blocks_execution_progress,
            blocks_step_completion=resolved_step.blocks_step_completion,
            blocks_signature=resolved_step.blocks_signature,
            blocks_pre_qa_handoff=resolved_step.blocks_pre_qa_handoff,
            meta_json={"fields": resolved_step.fields},
        )
    except IntegrityError as exc:
        raise OccurrenceError(
            (
                f"Another occurrence for step '{step_key}' was created concurrently. "
                "Retry the request."
            ),
            code="occurrence_conflict",
            status_code=409,
        ) from exc

    # Update document requirement counts
    doc_req = (
        BatchDocumentRequirement.objects.select_for_update()
        .filter(batch=batch, document_code=step_key)
        .first()
    )
    if doc_req:
        doc_req.expected_count = current_count + 1
        doc_req.actual_count = current_count + 1
        doc_req.save(update_fields=["expected_count", "actual_count", "updated_at"])

    return new_step
