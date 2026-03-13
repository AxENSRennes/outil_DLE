from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.batches.models import BatchDocumentRepeatMode, StepSignatureState


@dataclass(frozen=True)
class ResolvedStepDefinition:
    step_key: str
    title: str
    fields: list[dict[str, Any]]
    repeat_mode: str
    min_records: int
    max_records: int | None
    is_required: bool
    is_applicable: bool
    when_not_applicable: str | None
    applicability_basis: dict[str, Any]
    signature_state: str
    blocks_execution_progress: bool
    blocks_step_completion: bool
    blocks_signature: bool
    blocks_pre_qa_handoff: bool

    @property
    def is_hidden(self) -> bool:
        return not self.is_applicable and self.when_not_applicable == "hidden"

    @property
    def initial_record_count(self) -> int:
        return 1 if self.repeat_mode == "single" else self.min_records


def evaluate_applicability(
    step_def: dict[str, Any], batch_context: dict[str, Any]
) -> tuple[bool, dict[str, Any], str | None]:
    """Evaluate whether a step applies to the current batch context."""

    applicability = step_def.get("applicability")
    if not applicability:
        return True, {}, None

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
    if glitter_mode is not None and glitter_mode != "any":
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
    when_not_applicable = applicability.get("whenNotApplicable")
    return is_applicable, basis, when_not_applicable


def resolve_document_repeat_mode(mode_str: str) -> str:
    mapping = {
        "single": BatchDocumentRepeatMode.SINGLE,
        "per_shift": BatchDocumentRepeatMode.PER_SHIFT,
        "per_team": BatchDocumentRepeatMode.PER_TEAM,
        "per_box": BatchDocumentRepeatMode.PER_BOX,
        "per_event": BatchDocumentRepeatMode.PER_EVENT,
    }
    return mapping.get(mode_str, BatchDocumentRepeatMode.SINGLE)


def resolve_signature_state(signature_policy: dict[str, Any] | None) -> str:
    if signature_policy and signature_policy.get("required"):
        return StepSignatureState.REQUIRED
    return StepSignatureState.NOT_REQUIRED


def resolve_step_definition(
    snapshot: dict[str, Any] | None,
    batch_context: dict[str, Any],
    step_key: str,
) -> ResolvedStepDefinition:
    if snapshot is None:
        raise ValueError("Batch has no template snapshot.")

    steps_defs: dict[str, Any] = snapshot.get("steps", {})
    step_def = steps_defs.get(step_key)
    if step_def is None:
        raise KeyError(f"Step key '{step_key}' not found in template snapshot.")

    repeat_policy = step_def.get("repeatPolicy", {})
    mode = repeat_policy.get("mode", "single")
    min_records = repeat_policy.get("minRecords", 1)
    max_records = repeat_policy.get("maxRecords")

    is_applicable, applicability_basis, when_not_applicable = evaluate_applicability(
        step_def, batch_context
    )

    blocking = step_def.get("blockingPolicy", {})

    return ResolvedStepDefinition(
        step_key=step_key,
        title=step_def.get("title", step_key),
        fields=step_def.get("fields", []),
        repeat_mode=mode,
        min_records=min_records,
        max_records=max_records,
        is_required=step_def.get("required", True),
        is_applicable=is_applicable,
        when_not_applicable=when_not_applicable,
        applicability_basis=applicability_basis,
        signature_state=resolve_signature_state(step_def.get("signaturePolicy")),
        blocks_execution_progress=blocking.get("blocksExecutionProgress", False),
        blocks_step_completion=blocking.get("blocksStepCompletion", True),
        blocks_signature=blocking.get("blocksSignature", False),
        blocks_pre_qa_handoff=blocking.get("blocksPreQaHandoff", True),
    )
