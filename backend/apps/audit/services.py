from __future__ import annotations

from typing import Any

from apps.audit.models import AuditEvent, AuditEventType

SENSITIVE_METADATA_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "client_secret",
    "cookie",
    "credential",
    "credentials",
    "password",
    "pin",
    "private_key",
    "refresh_token",
    "secret",
    "session_key",
    "token",
}


def _sanitize_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _sanitize_metadata(item)
            for key, item in value.items()
            if str(key).lower() not in SENSITIVE_METADATA_KEYS
        }
    if isinstance(value, list):
        return [_sanitize_metadata(item) for item in value]
    return value


BATCH_DOMAIN_EVENT_TYPES = frozenset({
    AuditEventType.BATCH_CREATED,
    AuditEventType.STEP_DRAFT_SAVED,
    AuditEventType.STEP_COMPLETED,
    AuditEventType.STEP_SIGNED,
    AuditEventType.BATCH_SUBMITTED_FOR_PRE_QA,
    AuditEventType.PRE_QA_REVIEW_CONFIRMED,
    AuditEventType.QUALITY_REVIEW_STARTED,
    AuditEventType.BATCH_RELEASED,
    AuditEventType.BATCH_REJECTED,
    AuditEventType.BATCH_RETURNED_FOR_CORRECTION,
    AuditEventType.CORRECTION_SUBMITTED,
    AuditEventType.CHANGE_REVIEWED,
})


def record_audit_event(
    event_type: AuditEventType,
    *,
    actor: Any | None = None,
    site: Any | None = None,
    metadata: dict[str, Any] | None = None,
    target_type: str = "",
    target_id: int | None = None,
) -> AuditEvent:
    validated_event_type = AuditEventType(event_type)
    target_type = target_type.strip()

    if validated_event_type in BATCH_DOMAIN_EVENT_TYPES and actor is None:
        raise ValueError("actor is required for batch-domain audit events")

    if target_id is not None and not target_type:
        raise ValueError("target_type is required when target_id is provided")
    if target_type and target_id is None:
        raise ValueError("target_id is required when target_type is provided")

    return AuditEvent.objects.create(
        event_type=validated_event_type,
        actor=actor,
        site=site,
        metadata=_sanitize_metadata(metadata or {}),
        target_type=target_type,
        target_id=target_id,
    )
