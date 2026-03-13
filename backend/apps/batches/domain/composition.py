from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.batches.models import (
    Batch,
    BatchDocumentRepeatMode,
    BatchDocumentRequirement,
    BatchStep,
    BatchStepStatus,
    StepSignatureState,
)


class CompositionError(Exception):
    pass


def _evaluate_applicability(
    step_def: dict[str, Any], batch_context: dict[str, Any]
) -> tuple[bool, dict[str, Any]]:
    """Evaluate whether a step is applicable given the batch context.

    Returns (is_applicable, basis_json) where basis_json records the evaluation.
    """
    applicability = step_def.get("applicability")
    if not applicability:
        return True, {}

    basis: dict[str, Any] = {"rule": applicability}
    is_applicable = True

    machine_codes = applicability.get("machineCodes")
    if machine_codes is not None:
        ctx_machine = batch_context.get("machine_code", "")
        if ctx_machine not in machine_codes:
            is_applicable = False
            basis["machine_code_match"] = False
            basis["context_machine_code"] = ctx_machine
            basis["required_machine_codes"] = machine_codes

    glitter_mode = applicability.get("glitterMode")
    if glitter_mode is not None:
        ctx_glitter = batch_context.get("glitter_mode", "")
        if ctx_glitter != glitter_mode:
            is_applicable = False
            basis["glitter_mode_match"] = False
            basis["context_glitter_mode"] = ctx_glitter
            basis["required_glitter_mode"] = glitter_mode

    line_codes = applicability.get("lineCodes")
    if line_codes is not None:
        ctx_line = batch_context.get("line_code", "")
        if ctx_line not in line_codes:
            is_applicable = False
            basis["line_code_match"] = False
            basis["context_line_code"] = ctx_line
            basis["required_line_codes"] = line_codes

    format_families = applicability.get("formatFamilies")
    if format_families is not None:
        ctx_format = batch_context.get("format_family", "")
        if ctx_format not in format_families:
            is_applicable = False
            basis["format_family_match"] = False
            basis["context_format_family"] = ctx_format
            basis["required_format_families"] = format_families

    site_codes = applicability.get("siteCodes")
    if site_codes is not None:
        ctx_site = batch_context.get("site_code", "")
        if ctx_site not in site_codes:
            is_applicable = False
            basis["site_code_match"] = False
            basis["context_site_code"] = ctx_site
            basis["required_site_codes"] = site_codes

    basis["is_applicable"] = is_applicable
    return is_applicable, basis


def _resolve_repeat_mode(mode_str: str) -> str:
    """Map template repeatPolicy.mode to BatchDocumentRepeatMode value."""
    mapping = {
        "single": BatchDocumentRepeatMode.SINGLE,
        "per_shift": BatchDocumentRepeatMode.PER_SHIFT,
        "per_team": BatchDocumentRepeatMode.PER_TEAM,
        "per_box": BatchDocumentRepeatMode.PER_BOX,
        "per_event": BatchDocumentRepeatMode.PER_EVENT,
    }
    return mapping.get(mode_str, BatchDocumentRepeatMode.SINGLE)


def _resolve_signature_state(signature_policy: dict[str, Any] | None) -> str:
    """Determine initial signature state from template signaturePolicy."""
    if signature_policy and signature_policy.get("required"):
        return StepSignatureState.REQUIRED
    return StepSignatureState.NOT_REQUIRED


@transaction.atomic
def generate_repeated_controls(batch: Batch) -> list[BatchStep]:
    """Generate BatchStep and BatchDocumentRequirement records from the frozen
    template snapshot stored in batch.snapshot_json.

    This function is idempotent: it only creates steps with NOT_STARTED status
    and skips step_keys that already have non-NOT_STARTED records.
    """
    snapshot = batch.snapshot_json
    if snapshot is None:
        raise CompositionError("Batch has no template snapshot.")

    step_order: list[str] = snapshot.get("stepOrder", [])
    steps_defs: dict[str, Any] = snapshot.get("steps", {})
    batch_context = batch.batch_context_json or {}

    created_steps: list[BatchStep] = []
    for position, step_key in enumerate(step_order):
        step_def = steps_defs.get(step_key)
        if step_def is None:
            continue

        # Applicability evaluation
        is_applicable, applicability_basis = _evaluate_applicability(
            step_def, batch_context
        )

        # If not applicable and whenNotApplicable == "hidden", skip entirely
        when_not_applicable = (
            step_def.get("applicability", {}).get("whenNotApplicable", "mark_na")
            if not is_applicable
            else None
        )
        if not is_applicable and when_not_applicable == "hidden":
            continue

        # Repeat policy
        repeat_policy = step_def.get("repeatPolicy", {})
        mode = repeat_policy.get("mode", "single")
        min_records = repeat_policy.get("minRecords", 1)

        # Blocking policy
        blocking = step_def.get("blockingPolicy", {})
        blocks_execution_progress = blocking.get("blocksExecutionProgress", False)
        blocks_step_completion = blocking.get("blocksStepCompletion", True)
        blocks_signature = blocking.get("blocksSignature", False)
        blocks_pre_qa_handoff = blocking.get("blocksPreQaHandoff", True)

        # Signature policy
        signature_state = _resolve_signature_state(step_def.get("signaturePolicy"))

        title = step_def.get("title", step_key)
        fields = step_def.get("fields", [])

        # Idempotency check: if non-NOT_STARTED steps exist for this step_key, skip
        existing_non_initial = BatchStep.objects.filter(
            batch=batch, step_key=step_key
        ).exclude(status=BatchStepStatus.NOT_STARTED)
        if existing_non_initial.exists():
            # Preserve existing steps, skip this step_key
            continue

        # Delete existing NOT_STARTED steps for this step_key (re-composition)
        BatchStep.objects.filter(
            batch=batch, step_key=step_key, status=BatchStepStatus.NOT_STARTED
        ).delete()

        # Delete existing document requirement for re-composition
        BatchDocumentRequirement.objects.filter(
            batch=batch, document_code=step_key
        ).delete()

        record_count = 1 if mode == "single" else min_records
        step_records: list[BatchStep] = []

        for idx in range(1, record_count + 1):
            occurrence_key = "default" if mode == "single" else f"{step_key}_{mode}_{idx}"

            sequence = position * 1000 + idx

            step_record = BatchStep(
                batch=batch,
                step_key=step_key,
                occurrence_key=occurrence_key,
                occurrence_index=idx,
                title=title,
                sequence_order=sequence,
                source_document_code=step_key,
                is_applicable=is_applicable,
                applicability_basis_json=applicability_basis,
                status=BatchStepStatus.NOT_STARTED,
                review_state="none",
                signature_state=signature_state,
                blocks_execution_progress=blocks_execution_progress,
                blocks_step_completion=blocks_step_completion,
                blocks_signature=blocks_signature,
                blocks_pre_qa_handoff=blocks_pre_qa_handoff,
                data_json={},
                meta_json={"fields": fields},
            )
            step_records.append(step_record)

        BatchStep.objects.bulk_create(step_records)
        created_steps.extend(step_records)

        # Create corresponding BatchDocumentRequirement
        repeat_mode_value = _resolve_repeat_mode(mode)
        BatchDocumentRequirement.objects.create(
            batch=batch,
            document_code=step_key,
            title=title,
            source_step_key=step_key,
            is_required=step_def.get("required", True),
            is_applicable=is_applicable,
            repeat_mode=repeat_mode_value,
            expected_count=len(step_records),
            actual_count=len(step_records),
            applicability_basis_json=applicability_basis,
        )

    return created_steps
