from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.audit.models import AuditEvent, AuditEventType
from apps.audit.services import record_audit_event
from apps.batches.models import BatchStep, StepStatus

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

CORRECTABLE_STATUSES = {
    StepStatus.IN_PROGRESS,
    StepStatus.COMPLETE,
    StepStatus.SIGNED,
}


JSONScalar = str | int | float | bool | None


def _is_supported_correction_value(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def submit_correction(
    *,
    step: BatchStep,
    actor: AbstractBaseUser,
    corrections: list[dict[str, Any]],
    reason_for_change: str,
    ip_address: str | None = None,
) -> AuditEvent:
    """Submit a controlled correction to a batch step's data.

    Wraps both the data update and audit event write in a single
    atomic transaction (fail-closed pattern).

    Raises ValueError if:
    - step status is not correctable (not_started)
    - reason_for_change is blank/whitespace-only
    - corrections list is empty
    - any correction entry has an empty field_name
    - duplicate field_name values exist within the corrections list
    """
    stripped_reason = reason_for_change.strip()
    if not stripped_reason:
        raise ValueError("reason_for_change is required and cannot be blank.")

    if not corrections:
        raise ValueError("At least one correction entry is required.")

    seen_field_names: set[str] = set()
    for entry in corrections:
        field_name = entry.get("field_name", "")
        if not field_name or not str(field_name).strip():
            raise ValueError("Each correction entry must have a non-empty field_name.")
        if "new_value" not in entry:
            raise ValueError("Each correction entry must include new_value.")
        new_value = entry["new_value"]
        if not _is_supported_correction_value(new_value):
            raise ValueError(
                "Each correction entry new_value must be a string, number, boolean, or null."
            )
        if field_name in seen_field_names:
            raise ValueError(
                f"Duplicate field_name '{field_name}' in corrections. "
                "Each field may only appear once per correction request."
            )
        seen_field_names.add(field_name)

    with transaction.atomic():
        locked_step = (
            BatchStep.objects.select_related("batch__site").select_for_update().get(pk=step.pk)
        )

        if locked_step.status not in CORRECTABLE_STATUSES:
            raise ValueError(
                f"Step status '{locked_step.status}' is not correctable. "
                "Only in_progress, complete, or signed steps can be corrected."
            )
        correction_details: list[dict[str, JSONScalar]] = []
        data = dict(locked_step.data_json) if locked_step.data_json else {}

        for entry in corrections:
            field_name = str(entry["field_name"]).strip()
            new_value = entry["new_value"]
            old_value = data.get(field_name)

            correction_details.append(
                {
                    "field_name": field_name,
                    "old_value": old_value,
                    "new_value": new_value,
                }
            )
            data[field_name] = new_value

        locked_step.data_json = data
        locked_step.save(update_fields=["data_json"])

        audit_event = record_audit_event(
            AuditEventType.CORRECTION_SUBMITTED,
            actor=actor,
            site=locked_step.batch.site,
            target_type="batch_step",
            target_id=locked_step.pk,
            metadata={
                "batch_id": locked_step.batch_id,
                "reason_for_change": stripped_reason,
                "corrections": correction_details,
                "ip_address": ip_address,
            },
        )

    return audit_event
