from __future__ import annotations

from typing import Any

from apps.audit.models import AuditEvent

SENSITIVE_METADATA_KEYS = {"pin", "password", "secret", "credential", "credentials"}


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


def record_audit_event(
    event_type: str,
    *,
    actor: Any | None = None,
    site: Any | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        event_type=event_type,
        actor=actor,
        site=site,
        metadata=_sanitize_metadata(metadata or {}),
    )
