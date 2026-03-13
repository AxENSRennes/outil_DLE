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


def record_audit_event(
    event_type: AuditEventType,
    *,
    actor: Any | None = None,
    site: Any | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    validated_event_type = AuditEventType(event_type)
    return AuditEvent.objects.create(
        event_type=validated_event_type,
        actor=actor,
        site=site,
        metadata=_sanitize_metadata(metadata or {}),
    )
