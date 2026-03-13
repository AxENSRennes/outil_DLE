from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import Max

from apps.batches.models import (
    Batch,
    BatchDocumentRequirement,
    BatchStep,
    BatchStepStatus,
    StepSignatureState,
)


class OccurrenceError(Exception):
    pass


@transaction.atomic
def add_occurrence(batch: Batch, step_key: str) -> BatchStep:
    """Add a new occurrence of a repeated step.

    Validates that the step's repeat policy allows additional occurrences
    and creates the next BatchStep record with incremented occurrence_index.
    """
    snapshot = batch.snapshot_json
    if not snapshot:
        raise OccurrenceError("Batch has no template snapshot.")

    steps_defs: dict[str, Any] = snapshot.get("steps", {})
    step_def = steps_defs.get(step_key)
    if step_def is None:
        raise OccurrenceError(f"Step key '{step_key}' not found in template snapshot.")

    repeat_policy = step_def.get("repeatPolicy", {})
    mode = repeat_policy.get("mode", "single")

    if mode == "single":
        raise OccurrenceError(
            f"Step '{step_key}' has repeat mode 'single' and does not support "
            f"additional occurrences."
        )

    max_records = repeat_policy.get("maxRecords")
    existing_steps = BatchStep.objects.filter(batch=batch, step_key=step_key)
    current_count = existing_steps.count()

    if max_records is not None and current_count >= max_records:
        raise OccurrenceError(
            f"Step '{step_key}' has reached the maximum of {max_records} occurrences."
        )

    max_index = existing_steps.aggregate(max_idx=Max("occurrence_index"))["max_idx"] or 0
    next_index = max_index + 1

    occurrence_key = f"{step_key}_{mode}_{next_index}"

    # Derive sequence_order from the last existing step for this key
    last_step = existing_steps.order_by("-sequence_order").first()
    sequence_order = (last_step.sequence_order + 1) if last_step else next_index

    # Blocking and signature from template
    blocking = step_def.get("blockingPolicy", {})
    signature_policy = step_def.get("signaturePolicy")
    signature_state = (
        StepSignatureState.REQUIRED
        if signature_policy and signature_policy.get("required")
        else StepSignatureState.NOT_REQUIRED
    )

    # Applicability from existing steps (same step_key, same context)
    reference_step = existing_steps.first()
    is_applicable = reference_step.is_applicable if reference_step else True
    applicability_basis = (
        reference_step.applicability_basis_json if reference_step else {}
    )

    new_step = BatchStep.objects.create(
        batch=batch,
        step_key=step_key,
        occurrence_key=occurrence_key,
        occurrence_index=next_index,
        title=step_def.get("title", step_key),
        sequence_order=sequence_order,
        source_document_code=step_key,
        is_applicable=is_applicable,
        applicability_basis_json=applicability_basis,
        status=BatchStepStatus.NOT_STARTED,
        signature_state=signature_state,
        blocks_execution_progress=blocking.get("blocksExecutionProgress", False),
        blocks_step_completion=blocking.get("blocksStepCompletion", True),
        blocks_signature=blocking.get("blocksSignature", False),
        blocks_pre_qa_handoff=blocking.get("blocksPreQaHandoff", True),
        meta_json={"fields": step_def.get("fields", [])},
    )

    # Update document requirement counts
    doc_req = BatchDocumentRequirement.objects.filter(
        batch=batch, document_code=step_key
    ).first()
    if doc_req:
        doc_req.expected_count = current_count + 1
        doc_req.actual_count = current_count + 1
        doc_req.save(update_fields=["expected_count", "actual_count", "updated_at"])

    return new_step
