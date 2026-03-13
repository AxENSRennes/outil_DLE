# Audit Event Taxonomy

This document defines the canonical audit event types for DLE-SaaS, their metadata contracts, and instrumentation guidance for domain services.

## Event Type Enum

All event types live in `apps.audit.models.AuditEventType`. Values use **past-tense business naming** (e.g. `batch_created`, not `create_batch`).

### Auth-Domain Events (Story 1.3)

| Event Type | Description |
|---|---|
| `identify` | User identified at workstation via PIN |
| `switch_user` | Active workstation user changed |
| `lock_workstation` | Workstation locked, session cleared |
| `identify_failed` | Failed identification attempt |
| `signature_reauth_succeeded` | Signature re-authentication succeeded |
| `signature_reauth_failed` | Signature re-authentication failed |

### Batch-Domain Events (Story 4.1)

| Event Type | Workflow Action | target_type | Recommended Metadata |
|---|---|---|---|
| `batch_created` | Batch instantiation | `batch` | `mmr_version_id`, `site_id`, `batch_number` |
| `step_draft_saved` | `save_step_draft` | `batch_step` | `batch_id`, `field_count`, `ip_address` |
| `step_completed` | `complete_step` | `batch_step` | `batch_id`, `completion_note` |
| `step_signed` | `sign_step` | `batch_step` | `batch_id`, `signature_meaning`, `signer_role` |
| `correction_submitted` | `request_correction` | `batch_step` | `batch_id`, `reason_for_change`, `field_name` |
| `batch_submitted_for_pre_qa` | `submit_for_pre_qa` | `batch` | `step_count`, `completed_count` |
| `pre_qa_review_confirmed` | `confirm_pre_qa_review` | `batch` | `review_note` |
| `change_reviewed` | `mark_change_reviewed` | `batch_step` | `batch_id`, `reviewer_note` |
| `quality_review_started` | `start_quality_review` | `batch` | |
| `batch_returned_for_correction` | `return_for_correction` | `batch` | `return_note` |
| `batch_released` | `release_batch` | `batch` | `release_note`, `signature_meaning` |
| `batch_rejected` | `reject_batch` | `batch` | `rejection_reason` |

## Target Linkage

Each audit event optionally links to a domain record via two fields:

- **`target_type`** (`CharField`, max 64): canonical domain entity type string — `"batch"`, `"batch_step"`, `"signature"`.
- **`target_id`** (`PositiveIntegerField`, nullable): primary key of the affected record.

Both fields must be provided together or both omitted. The audit service validates this constraint at the Python level, and a database CHECK constraint (`audit_target_type_id_consistent`) enforces it at the storage level.

Existing auth-domain events have `target_type=""` and `target_id=None`, which is correct — they operate on session/workstation context, not domain records.

### Why plain strings instead of GenericForeignKey?

Target linkage uses plain string + integer fields (not Django `ContentType` / `GenericForeignKey`) to keep the audit app decoupled from apps that may not exist yet (`apps.batches`, `apps.signatures`). When those apps are created, proper FK constraints can be added via a subsequent migration if desired.

## Metadata Conventions

- Metadata is a JSON object stored in `AuditEvent.metadata`.
- The audit service **strips sensitive keys** recursively before persisting: `password`, `pin`, `token`, `secret`, `api_key`, `private_key`, `credential`, `credentials`, `authorization`, `cookie`, `session_key`, `access_token`, `refresh_token`, `client_secret`.
- Metadata schema per event type is **recommended but not enforced** at the model level. Domain services are responsible for passing correct metadata.
- **`ip_address`**: recommended for all events where a request context is available. Use `shared.http.get_client_ip(request)`. This value is advisory/best-effort since it comes from client-supplied headers.

## Instrumentation Guide for Domain Services

### Actor requirement for batch-domain events

Batch-domain events are **attributed** — the `actor` parameter is mandatory. The audit service raises `ValueError` if `actor` is `None` for any batch-domain event type. Auth-domain events (e.g. `lock_workstation`) may have a null actor for system-initiated actions.

### Recording an event

```python
from apps.audit.models import AuditEventType
from apps.audit.services import record_audit_event

event = record_audit_event(
    AuditEventType.BATCH_CREATED,
    actor=request.user,
    site=current_site,
    target_type="batch",
    target_id=batch.pk,
    metadata={
        "mmr_version_id": batch.mmr_version_id,
        "batch_number": batch.number,
        "ip_address": get_client_ip(request),
    },
)
```

### Fail-closed pattern

If audit recording must succeed for the regulated action to be valid, the caller wraps both in the same database transaction:

```python
from django.db import transaction

with transaction.atomic():
    batch = Batch.objects.create(...)
    record_audit_event(
        AuditEventType.BATCH_CREATED,
        actor=request.user,
        target_type="batch",
        target_id=batch.pk,
        metadata={...},
    )
```

If `record_audit_event` raises, the transaction rolls back and the batch creation is undone. This ensures that regulated actions never silently succeed without an audit trail.

### Querying audit events

```python
from apps.audit.selectors import (
    get_audit_events_for_target,
    get_audit_events_for_batch_context,
    get_audit_events_by_actor,
)

# Events for a specific record
events = get_audit_events_for_target("batch", batch_id)

# All events in a batch context (batch + step-level via metadata)
events = get_audit_events_for_batch_context(batch_id)

# Events by a specific actor
events = get_audit_events_by_actor(user_id, since=some_datetime)
```

## Database Indexes

| Index | Fields | Purpose |
|---|---|---|
| `audit_event_type_occurred_idx` | `(event_type, occurred_at)` | Filter by event type with time range |
| `audit_target_type_id_idx` | `(target_type, target_id)` | Batch-scoped and record-scoped queries |
| `audit_actor_occurred_idx` | `(actor, occurred_at)` | Actor history queries |

## Cross-References

- [Architecture Decisions 15-16](/docs/decisions/architecture-decisions.md) — audit event taxonomy design decisions
- [Workstation Auth](/docs/implementation/workstation-auth.md) — auth-domain event types and patterns established in Story 1.3
