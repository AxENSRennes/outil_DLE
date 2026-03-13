from __future__ import annotations

from datetime import datetime

from django.db.models import Q, QuerySet

from apps.audit.models import AuditEvent


def get_audit_events_for_target(
    target_type: str,
    target_id: int,
) -> QuerySet[AuditEvent]:
    """Return events linked to a specific target record, in chronological order."""
    return AuditEvent.objects.filter(
        target_type=target_type,
        target_id=target_id,
    ).order_by("occurred_at", "id")


def get_audit_events_for_batch_context(
    batch_id: int,
) -> QuerySet[AuditEvent]:
    """Return events for a batch: direct batch-level events plus step-level
    events that carry ``batch_id`` in their metadata.  Chronological order.

    Performance note: the ``metadata__batch_id`` lookup is not indexed.
    Consider a functional GIN index on metadata if query volume grows.

    Callers must store ``batch_id`` as an integer in metadata (not a string)
    to ensure the JSONField lookup matches correctly."""
    return AuditEvent.objects.filter(
        Q(target_type="batch", target_id=batch_id) | Q(metadata__batch_id=batch_id)
    ).order_by("occurred_at", "id")


def get_audit_events_by_actor(
    actor_id: int,
    since: datetime | None = None,
) -> QuerySet[AuditEvent]:
    """Return events for a specific actor, optionally filtered by timestamp."""
    qs = AuditEvent.objects.filter(actor_id=actor_id)
    if since is not None:
        qs = qs.filter(occurred_at__gte=since)
    return qs.order_by("occurred_at", "id")
