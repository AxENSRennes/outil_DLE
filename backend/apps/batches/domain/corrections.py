from __future__ import annotations

from typing import Any

from django.db import transaction

from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event
from apps.batches.models import BatchStep, StepStatus

CORRECTABLE_STATUSES = {
    StepStatus.IN_PROGRESS,
    StepStatus.COMPLETE,
    StepStatus.SIGNED,
}


def submit_correction(
    *,
    step: BatchStep,
    actor: Any,
    site: Any,
    corrections: list[dict[str, Any]],
    reason_for_change: str,
    ip_address: str | None = None,
) -> Any:
    """Submit a controlled correction to a batch step's data.

    Wraps both the data update and audit event write in a single
    atomic transaction (fail-closed pattern).

    Raises ValueError if:
    - step status is not correctable (not_started)
    - reason_for_change is blank/whitespace-only
    - corrections list is empty
    - any correction entry has an empty field_name
    """
    if step.status not in CORRECTABLE_STATUSES:
        raise ValueError(
            f"Step status '{step.status}' is not correctable. "
            "Only in_progress, complete, or signed steps can be corrected."
        )

    stripped_reason = reason_for_change.strip()
    if not stripped_reason:
        raise ValueError("reason_for_change is required and cannot be blank.")

    if not corrections:
        raise ValueError("At least one correction entry is required.")

    for entry in corrections:
        field_name = entry.get("field_name", "")
        if not field_name or not str(field_name).strip():
            raise ValueError("Each correction entry must have a non-empty field_name.")

    correction_details: list[dict[str, Any]] = []
    data = dict(step.data_json) if step.data_json else {}

    for entry in corrections:
        field_name = entry["field_name"]
        new_value = entry.get("new_value")
        old_value = data.get(field_name)

        correction_details.append(
            {
                "field_name": field_name,
                "old_value": old_value,
                "new_value": new_value,
            }
        )
        data[field_name] = new_value

    with transaction.atomic():
        step.data_json = data
        step.save(update_fields=["data_json"])

        audit_event = record_audit_event(
            AuditEventType.CORRECTION_SUBMITTED,
            actor=actor,
            site=site,
            target_type="batch_step",
            target_id=step.pk,
            metadata={
                "batch_id": step.batch_id,
                "reason_for_change": stripped_reason,
                "corrections": correction_details,
                "ip_address": ip_address or "",
            },
        )

    return audit_event
