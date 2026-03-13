"""Domain logic for computing batch review summaries.

Evaluates step completeness, signature completeness, integrity flags,
and derives a traffic-light severity (green / amber / red).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from apps.batches.models import StepStatus

Severity = Literal["green", "amber", "red"]


@dataclass(frozen=True)
class StepSummary:
    total: int
    not_started: int
    in_progress: int
    complete: int
    signed: int


@dataclass(frozen=True)
class FlagCounts:
    missing_required_data: int
    missing_required_signatures: int
    changed_since_review: int
    changed_since_signature: int
    open_exceptions: int
    review_required: int = 0
    blocking_open_exceptions: int = 0


@dataclass(frozen=True)
class ChecklistSummary:
    expected_documents: int
    present_documents: int
    missing_documents: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FlaggedStep:
    step_id: int
    step_reference: str
    step_status: str
    flags: list[str]
    severity: Severity


@dataclass(frozen=True)
class ReviewSummary:
    batch_id: int
    batch_reference: str
    batch_status: str
    severity: Severity
    step_summary: StepSummary
    flags: FlagCounts
    checklist: ChecklistSummary
    flagged_steps: list[FlaggedStep]


def evaluate_step_completeness(steps: list[dict[str, Any]]) -> StepSummary:
    """Compute per-status counts from a list of step dicts."""
    total = len(steps)
    not_started = 0
    in_progress = 0
    complete = 0
    signed = 0

    for step in steps:
        status = step["status"]
        if status == StepStatus.NOT_STARTED:
            not_started += 1
        elif status == StepStatus.IN_PROGRESS:
            in_progress += 1
        elif status == StepStatus.COMPLETE:
            complete += 1
        elif status == StepStatus.SIGNED:
            signed += 1

    return StepSummary(
        total=total,
        not_started=not_started,
        in_progress=in_progress,
        complete=complete,
        signed=signed,
    )


def evaluate_signature_completeness(steps: list[dict[str, Any]]) -> int:
    """Count steps that still need a required signature."""
    return sum(
        1
        for step in steps
        if step.get("requires_signature") and not step.get("has_signature")
    )


def evaluate_integrity_flags(steps: list[dict[str, Any]]) -> dict[str, int]:
    """Count review-integrity signals that affect reviewer attention."""
    changed_since_review = 0
    changed_since_signature = 0
    review_required = 0
    open_exceptions = 0
    blocking_open_exceptions = 0

    for step in steps:
        if step.get("changed_since_review"):
            changed_since_review += 1
        if step.get("changed_since_signature"):
            changed_since_signature += 1
        if step.get("review_required"):
            review_required += 1
        if step.get("has_open_exception"):
            open_exceptions += 1
            if step.get("open_exception_is_blocking"):
                blocking_open_exceptions += 1

    return {
        "changed_since_review": changed_since_review,
        "changed_since_signature": changed_since_signature,
        "review_required": review_required,
        "open_exceptions": open_exceptions,
        "blocking_open_exceptions": blocking_open_exceptions,
    }


def evaluate_flag_counts(steps: list[dict[str, Any]]) -> FlagCounts:
    """Count review-relevant flags across all steps."""
    missing_data = 0

    for step in steps:
        if not step.get("required_data_complete", True):
            missing_data += 1

    integrity_flags = evaluate_integrity_flags(steps)

    return FlagCounts(
        missing_required_data=missing_data,
        missing_required_signatures=evaluate_signature_completeness(steps),
        changed_since_review=integrity_flags["changed_since_review"],
        changed_since_signature=integrity_flags["changed_since_signature"],
        open_exceptions=integrity_flags["open_exceptions"],
        review_required=integrity_flags["review_required"],
        blocking_open_exceptions=integrity_flags["blocking_open_exceptions"],
    )


def evaluate_checklist(items: list[dict[str, Any]]) -> ChecklistSummary:
    """Evaluate dossier checklist completeness."""
    expected = len(items)
    present = sum(1 for item in items if item.get("is_present"))
    missing = [
        str(item["document_name"]) for item in items if not item.get("is_present")
    ]
    return ChecklistSummary(
        expected_documents=expected,
        present_documents=present,
        missing_documents=missing,
    )


def _derive_step_flags(step: dict[str, Any]) -> list[str]:
    """Collect all active flags for a single step."""
    flags: list[str] = []
    if not step.get("required_data_complete", True):
        flags.append("missing_required_data")
    if step.get("requires_signature") and not step.get("has_signature"):
        flags.append("missing_required_signature")
    if step.get("changed_since_review"):
        flags.append("changed_since_review")
    if step.get("changed_since_signature"):
        flags.append("changed_since_signature")
    if step.get("review_required"):
        flags.append("review_required")
    if step.get("has_open_exception"):
        flags.append("open_exception")
    return flags


def _derive_step_severity(step: dict[str, Any], flags: list[str]) -> Severity:
    """Derive severity for a single step based on its flags."""
    red_flags = {"missing_required_data", "missing_required_signature"}
    if any(f in red_flags for f in flags):
        return "red"
    if step.get("has_open_exception") and step.get("open_exception_is_blocking"):
        return "red"
    if flags:
        return "amber"
    return "green"


def build_flagged_steps(steps: list[dict[str, Any]]) -> list[FlaggedStep]:
    """Build the list of steps that have at least one active flag."""
    flagged: list[FlaggedStep] = []
    for step in steps:
        flags = _derive_step_flags(step)
        if flags:
            flagged.append(
                FlaggedStep(
                    step_id=int(step["id"]),
                    step_reference=str(step["reference"]),
                    step_status=str(step["status"]),
                    flags=flags,
                    severity=_derive_step_severity(step, flags),
                )
            )
    return flagged


def derive_traffic_light_severity(
    flags: FlagCounts,
    step_summary: StepSummary,
) -> Severity:
    """Derive overall traffic-light severity for the batch.

    - **green**: no missing required data, no missing required signatures,
      no pending re-review, no blocking exceptions.
    - **amber**: dossier navigable but has changes, notes, or non-blocking
      issues needing attention.
    - **red**: missing required data, missing required signatures, or
      blocking exceptions unresolved.
    """
    if (
        flags.missing_required_data > 0
        or flags.missing_required_signatures > 0
        or flags.blocking_open_exceptions > 0
    ):
        return "red"

    if (
        flags.changed_since_review > 0
        or flags.changed_since_signature > 0
        or flags.review_required > 0
        or flags.open_exceptions > 0
        or step_summary.not_started > 0
        or step_summary.in_progress > 0
    ):
        return "amber"

    return "green"
