# Story 4.1: Record Attributed Audit Events for Regulated Batch Actions

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a reviewer or regulated-system stakeholder,
I want the system to record attributed audit events for creation, update, completion, and signature-related actions on batch records,
so that dossier integrity can be reconstructed and trusted without relying on implicit or hidden state changes.

## Acceptance Criteria

1. **Given** a user performs a regulated action on a batch or batch step, **When** that action is accepted by the system, **Then** an audit event is recorded with the actor identity, timestamp, action type, and relevant batch context, **And** the event is linked to the affected regulated record.
2. **Given** multiple contributors may act on the same batch over time, **When** audit events are stored, **Then** the system preserves the sequence of attributable actions across contributors, **And** later stories can use that history without reconstructing authorship from unrelated data.
3. **Given** trust depends on complete traceability for important workflow actions, **When** step draft updates, step completion, signature actions, or other governed state transitions occur, **Then** the corresponding audit events are captured consistently, **And** the platform does not rely on silent record mutation without trace output.
4. **Given** auditability must support later review and correction flows, **When** this story is completed, **Then** later stories can read audit history from a canonical source tied to the batch domain, **And** they do not need to invent feature-local logging approaches.
5. **Given** this story is focused on foundational traceability rather than correction UX, **When** it is implemented, **Then** the system provides attributable audit event capture as a standalone capability, **And** reason-for-change flows, changed-since-review flags, and reviewer history views remain outside the scope of this story.

## Tasks / Subtasks

- [x] Extend AuditEventType enum with batch-domain event taxonomy (AC: 1, 3, 4)
  - [x] Add past-tense business-named event types to `apps.audit.models.AuditEventType` covering all canonical workflow actions from the architecture: `batch_created`, `step_draft_saved`, `step_completed`, `step_signed`, `batch_submitted_for_pre_qa`, `pre_qa_review_confirmed`, `quality_review_started`, `batch_released`, `batch_rejected`, `batch_returned_for_correction`, `correction_submitted`, `change_reviewed`.
  - [x] Keep existing auth-event types (`identify`, `switch_user`, `lock_workstation`, `identify_failed`, `signature_reauth_succeeded`, `signature_reauth_failed`) unchanged.
  - [x] Add an additive migration for the expanded choices. Do not alter existing event data.

- [x] Add target-record linkage fields to AuditEvent model (AC: 1, 2, 4)
  - [x] Add `target_type` (`CharField(max_length=64, blank=True, default="")`) to store the canonical domain entity type (e.g. `"batch"`, `"batch_step"`, `"signature"`). This is a plain string field, not a Django ContentType FK — keeps the model decoupled from apps that may not exist yet (batches, signatures, reviews).
  - [x] Add `target_id` (`PositiveIntegerField(null=True, blank=True)`) to store the PK of the affected record.
  - [x] Add a composite database index on `(target_type, target_id)` for efficient batch-scoped queries.
  - [x] Add a single-field index on `(actor_id, occurred_at)` for actor-history queries.
  - [x] Keep `actor`, `site`, `metadata` unchanged. Existing auth-event rows will have empty `target_type` and null `target_id`, which is correct.
  - [x] Generate an additive migration. Do not alter existing rows.

- [x] Extend the `record_audit_event` service with batch-context support (AC: 1, 3)
  - [x] Add optional `target_type: str` and `target_id: int | None` keyword arguments to `record_audit_event()`.
  - [x] Validate that `target_type` is a non-empty string when `target_id` is provided (and vice versa). Raise `ValueError` on mismatch.
  - [x] Preserve existing metadata sanitization and event-type validation behavior.
  - [x] Ensure `record_audit_event` remains synchronous and transactional — the caller's domain service controls the transaction boundary.

- [x] Add batch-scoped audit query selectors (AC: 2, 4)
  - [x] Create `backend/apps/audit/selectors.py` with query helpers:
    - `get_audit_events_for_target(target_type: str, target_id: int) -> QuerySet[AuditEvent]` — returns events linked to a specific record, ordered by `occurred_at` ascending (chronological).
    - `get_audit_events_for_batch_context(batch_id: int) -> QuerySet[AuditEvent]` — returns events where `target_type` is `"batch"` and `target_id` matches, OR `metadata` contains a `batch_id` key matching the given ID (for step-level events that also carry batch context in metadata). Ordered chronologically.
    - `get_audit_events_by_actor(actor_id: int, since: datetime | None = None) -> QuerySet[AuditEvent]` — returns events for a specific actor, optionally filtered by timestamp.
  - [x] Keep selectors as pure QuerySet builders — no side effects, no writes.

- [x] Update AuditEvent admin to display new fields (AC: 4)
  - [x] Add `target_type` and `target_id` to `list_display` and `list_filter` in `AuditEventAdmin`.
  - [x] Keep immutability guards (`has_add_permission`, `has_change_permission`, `has_delete_permission` returning `False`) unchanged.

- [x] Add comprehensive tests (AC: 1, 2, 3, 4, 5)
  - [x] Test that each new batch-domain event type can be recorded with target linkage and metadata.
  - [x] Test that `target_type` + `target_id` validation rejects mismatched values (e.g. target_id without target_type).
  - [x] Test that `get_audit_events_for_target` returns only events linked to the specified target, in chronological order.
  - [x] Test that `get_audit_events_for_batch_context` returns both batch-level and step-level events for a given batch ID.
  - [x] Test that `get_audit_events_by_actor` returns the correct filtered set.
  - [x] Test that existing auth-event recording still works unchanged (regression).
  - [x] Test that metadata sanitization still strips sensitive keys for batch-domain events.
  - [x] Test that AuditEvent admin immutability is preserved.
  - [x] Test that PROTECT FK constraints on actor and site still prevent cascade deletions.

- [x] Document the batch-domain audit event taxonomy (AC: 4)
  - [x] Create or extend `docs/implementation/audit-event-taxonomy.md` documenting:
    - Complete event type enum with descriptions and when each event is emitted.
    - Required and optional metadata fields per event type.
    - Target linkage conventions (`target_type` values and what `target_id` references).
    - Guidance for future domain services on how to call `record_audit_event`.
  - [x] Cross-reference the canonical workflow actions from the architecture document.

- [x] Run quality gates (AC: all)
  - [x] `make lint`
  - [x] `make typecheck`
  - [x] `make test`
  - [x] `make architecture-check`
  - [x] `make check`

## Dev Notes

### Story Intent

This story extends the existing `apps.audit` foundation — established in Story 1.3 for auth-event capture — to support the full batch-domain event taxonomy required by the architecture. It does NOT create batch, step, or signature models (those belong to Epic 2 and Epic 3). Instead, it provides the audit instrumentation infrastructure that those later domain services will call.

The key insight is that audit event capture must be a reusable, canonical service — not something each feature app reinvents. Story 4.1 ensures that when `apps.batches`, `apps.signatures`, and `apps.reviews` are implemented, they have a ready-made audit contract to call.

### Scope Boundaries

**In scope:**
- Extend AuditEventType enum with batch-domain event types
- Add target-record linkage to AuditEvent model
- Extend record_audit_event service
- Add audit query selectors for batch-scoped retrieval
- Tests and documentation

**Out of scope:**
- Batch, BatchStep, Signature, ReviewEvent models (Epic 2/3)
- Correction workflows and reason-for-change capture (Story 4.2)
- Changed-since-review flags and integrity states (Story 4.3)
- Reviewer history views (Story 4.4)
- Any frontend work
- Any API endpoints for audit event retrieval (will come with Story 4.4)

### Technical Requirements

- Use `/home/axel/wsl_venv/bin/python` for Django management commands, tests, and package operations.
- The `AuditEvent` model is append-only and immutable. Never allow updates or deletions of existing audit records.
- Keep `record_audit_event` synchronous. The calling domain service controls the database transaction boundary. If the audit write must succeed for the action to be valid, the caller wraps both in the same transaction.
- Follow the fail-closed pattern from Story 1.3: if audit recording fails, the regulated action should not silently succeed. Document this expectation for future callers.
- Target linkage uses plain `target_type` (string) + `target_id` (integer) fields, NOT Django `GenericForeignKey`. This avoids coupling the audit app to apps that don't exist yet and keeps the model simple and queryable. When batch models are created later, proper FK constraints can be added via a subsequent migration.
- Event type naming follows the architecture's past-tense business naming convention: `batch_created`, `step_signed`, `review_returned`, etc.
- Metadata schema per event type should be documented but not enforced at the model level. Domain services are responsible for passing correct metadata. The audit service only sanitizes sensitive keys.

### Architecture Compliance

- Keep all audit infrastructure in `backend/apps/audit/`. Do not scatter audit logic into other apps.
- Follow the established modular-monolith boundary pattern:
  - `models.py` for data definitions with constraints
  - `services.py` for write operations (record_audit_event)
  - `selectors.py` for read-only QuerySet builders (NEW in this story)
  - `admin.py` for Django admin with immutability guards
  - `tests/` for comprehensive test coverage
- Domain code in `apps.audit` must not import from `apps.authz.api`, `apps.batches`, or any other feature API package. It only depends on Django, its own models, and `settings.AUTH_USER_MODEL` / `apps.sites.Site` for existing FK references.
- New fields and event types use additive-only migrations. Do not alter existing columns or rows.
- Preserve the `on_delete=models.PROTECT` pattern on all FK references (actor, site) to prevent accidental data loss.
- Admin immutability guards must remain: `has_add_permission`, `has_change_permission`, `has_delete_permission` all return `False`.
  [Source: CLAUDE.md - Audit trail immutability rule]
- Hashed/sensitive fields must be excluded from admin forms or marked as readonly.
  [Source: CLAUDE.md - Credentials and secrets in admin rule]

### Library / Framework Requirements

- Django 5.2 LTS (pinned `>=5.2,<5.3` in pyproject.toml). Do not upgrade.
- Django REST Framework 3.16.x with `SessionAuthentication`. No new DRF endpoints in this story.
- drf-spectacular 0.29.x for OpenAPI generation. No new API schemas in this story.
- pytest-django for tests. Use `@pytest.mark.django_db` on all database tests.
- factory-boy is available for test fixtures if needed.
- mypy with django-stubs for type checking.
- ruff for linting.
- bandit for security scanning.

### File Structure Requirements

**Existing files to modify:**
- `backend/apps/audit/models.py` — Extend `AuditEventType` enum, add `target_type` and `target_id` fields to `AuditEvent`, add indexes.
- `backend/apps/audit/services.py` — Add `target_type` and `target_id` kwargs to `record_audit_event()`.
- `backend/apps/audit/admin.py` — Add new fields to `list_display` and `list_filter`.
- `backend/apps/audit/tests/test_services.py` — Extend with tests for new event types and target linkage.

**New files to create:**
- `backend/apps/audit/selectors.py` — Batch-scoped audit query helpers.
- `backend/apps/audit/tests/test_selectors.py` — Tests for the new selectors.
- `backend/apps/audit/migrations/0003_*.py` — Additive migration for new fields and indexes.
- `docs/implementation/audit-event-taxonomy.md` — Event type documentation and instrumentation contract.

**Do NOT create:**
- `backend/apps/batches/` — Belongs to Epic 2/3.
- `backend/apps/signatures/` — Belongs to Epic 3.
- `backend/apps/reviews/` — Belongs to Epic 5.
- Any frontend files.
- Any new API endpoints or serializers.

### Testing Requirements

- **Model tests:**
  - Each new AuditEventType value is valid and can be persisted.
  - target_type and target_id fields accept valid values and null.
  - Composite index on (target_type, target_id) exists (check via migration inspection or query plan).
  - Existing auth-event types still work unchanged (regression).

- **Service tests:**
  - `record_audit_event` with batch-domain event types and target linkage succeeds.
  - `record_audit_event` with target_id but no target_type raises ValueError.
  - `record_audit_event` with target_type but no target_id raises ValueError.
  - Metadata sanitization strips sensitive keys on batch-domain events.
  - Existing auth-event recording behavior is unchanged.

- **Selector tests:**
  - `get_audit_events_for_target("batch", 1)` returns only events with matching target_type and target_id.
  - `get_audit_events_for_target` returns results in chronological order (ascending).
  - `get_audit_events_for_batch_context(batch_id)` returns both batch-level and step-level events.
  - `get_audit_events_by_actor` with and without `since` filter.
  - Empty results when no matching events exist.

- **Admin tests:**
  - AuditEventAdmin still forbids add, change, delete.
  - New fields appear in list_display.

- **Regression tests:**
  - PROTECT FK on actor prevents user deletion when audit events exist.
  - PROTECT FK on site prevents site deletion when audit events exist.

- **Quality commands:**
  - `make lint`
  - `make typecheck`
  - `make test`
  - `make architecture-check`
  - `make check`

### Previous Story Intelligence

Story 1.3 established the audit foundation with the following patterns — reuse and extend them, do not reinvent:

- **AuditEvent model** uses `BigAutoField` PKs, `auto_now_add` timestamp, `JSONField` metadata, `PROTECT` FKs. Extend with new fields using the same patterns.
- **AuditEventType** is a `TextChoices` enum. Add new members following the same convention.
- **record_audit_event()** validates event_type via `AuditEventType(event_type)`, sanitizes metadata, and creates the event. Extend its signature, don't replace it.
- **Metadata sanitization** strips a known set of sensitive keys recursively. The same sanitization applies to batch-domain events.
- **Admin immutability** is enforced via permission overrides. Maintain it.
- **Fail-closed security pattern**: Story 1.3 review found that identify must fail closed if audit persistence fails. The same principle applies to batch-domain events: if audit recording fails for a regulated action, the action should not silently succeed. Document this expectation for callers.

Story 1.3 review findings that are relevant:
1. [High] Operations must fail closed if audit persistence fails — apply same pattern to batch audit guidance.
2. [Medium] Model-level validation must back up API-layer validation — apply to target_type/target_id validation.
3. [Medium] Always include client IP in failure event metadata — document as recommended metadata field.

### Git Intelligence Summary

Recent commits show a mature security-hardened authz/audit baseline:
- `bde7acc` merged Story 1.3 workstation auth
- `a980fe1` hardened audit event typing and lock throttling
- `c70f8d2` hardened FK constraints, admin delete, CSRF
- `600433f` protected FK integrity and added IP to success events
- `5f14659` extracted shared client IP helper (`backend/shared/http.py`)

Practical implications:
- The audit app is battle-tested with security reviews. Extend it carefully.
- Use the existing `get_client_ip()` helper from `backend/shared/http.py` when documenting recommended metadata fields.
- Follow the same incremental hardening approach: ship the foundation, then let code review catch edge cases.

### Batch-Domain Event Taxonomy Reference

The following event types map to the canonical workflow actions defined in the architecture. Each event should carry the specified metadata:

| Event Type | Workflow Action | target_type | Recommended Metadata |
|---|---|---|---|
| `batch_created` | (batch instantiation) | `batch` | `mmr_version_id`, `site_id`, `batch_number` |
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

This table is the authoritative event taxonomy for the MVP. Domain services in later stories MUST use these event types when recording audit events. Do not invent feature-local alternatives.

### Project Structure Notes

- The backend currently has three feature apps: `audit`, `authz`, `sites`.
- This story modifies only `apps.audit`. No new apps are created.
- The architecture reserves `backend/apps/batches/` for batch domain models (Epic 2/3). This story does NOT create that app.
- Target linkage via `target_type` + `target_id` is intentionally decoupled from the batch app. When `apps.batches` is created, a subsequent migration can add proper FK constraints if needed.
- The audit selectors in this story use `target_type` string matching. When batch models exist, callers can pass `"batch"` or `"batch_step"` as the target_type and the batch model's PK as target_id.

### References

- [epics.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/planning-artifacts/epics.md) - Epic 4 scope, Story 4.1 acceptance criteria, cross-story dependencies
- [architecture.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/planning-artifacts/architecture.md) - AuditEvent as relational entity, canonical workflow actions, event naming conventions, batch lifecycle states, data architecture, migration strategy
- [prd.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/planning-artifacts/prd.md) - FR16-FR23 (data integrity, corrections, traceability), NFR security (100% audit trail coverage), NFR reliability
- [ux-design-specification.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/planning-artifacts/ux-design-specification.md) - "Trust is visual" principle, ChangeHistoryBlock component, changed-since-review UX pattern, quality review traceability
- [architecture-decisions.md](/home/axel/DLE-SaaS-epic-4/docs/decisions/architecture-decisions.md) - Decision 2 (explicit domain entities), Decision 4 (relational vs JSONB), Decision 7 (re-review states), Decision 15-16 (audit event taxonomy)
- [workstation-auth.md](/home/axel/DLE-SaaS-epic-4/docs/implementation/workstation-auth.md) - Existing audit event types, AuditEventType enum, audit metadata conventions
- [authorization-policy.md](/home/axel/DLE-SaaS-epic-4/docs/implementation/authorization-policy.md) - Authorization enforcement patterns, domain helper conventions
- [1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/implementation-artifacts/1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md) - Previous story learnings, audit app foundation, fail-closed patterns, code review findings
- [backend/apps/audit/models.py](/home/axel/DLE-SaaS-epic-4/backend/apps/audit/models.py) - Existing AuditEvent model and AuditEventType enum
- [backend/apps/audit/services.py](/home/axel/DLE-SaaS-epic-4/backend/apps/audit/services.py) - Existing record_audit_event service with metadata sanitization
- [backend/apps/audit/admin.py](/home/axel/DLE-SaaS-epic-4/backend/apps/audit/admin.py) - Existing admin with immutability guards
- [backend/shared/http.py](/home/axel/DLE-SaaS-epic-4/backend/shared/http.py) - get_client_ip() helper for advisory IP logging
- [Makefile](/home/axel/DLE-SaaS-epic-4/Makefile) - Canonical quality gate commands
- [pyproject.toml](/home/axel/DLE-SaaS-epic-4/pyproject.toml) - Pinned Django 5.2, DRF 3.16, drf-spectacular 0.29

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Dev DB has inconsistent migration history (admin.0001_initial applied before authz.0001_initial). Migration 0003 was written manually. Tests use a fresh test DB and pass correctly.

### Completion Notes List

- Extended `AuditEventType` enum with 12 batch-domain event types following past-tense business naming convention from architecture.
- Added `target_type` (CharField) and `target_id` (PositiveIntegerField) to `AuditEvent` model for record linkage, with composite index `(target_type, target_id)` and actor history index `(actor, occurred_at)`.
- Extended `record_audit_event()` with `target_type` and `target_id` kwargs including mutual presence validation (ValueError on mismatch).
- Created `selectors.py` with three pure QuerySet builders: `get_audit_events_for_target`, `get_audit_events_for_batch_context`, `get_audit_events_by_actor`.
- Updated `AuditEventAdmin` with `target_type` and `target_id` in `list_display` and `target_type` in `list_filter`. Immutability guards preserved.
- Added 37 audit-specific tests (services, selectors, admin). Full backend suite: 100 tests passed, 0 regressions.
- Created `docs/implementation/audit-event-taxonomy.md` with complete event taxonomy, target linkage conventions, metadata contracts, fail-closed guidance, and instrumentation examples.
- All quality gates passed: lint, typecheck, test, architecture-check, security.

### Change Log

- 2026-03-13: Story 4.1 implementation complete — batch-domain audit event taxonomy, target linkage, selectors, admin, tests, documentation.

### File List

- `backend/apps/audit/models.py` (modified) — Extended AuditEventType enum, added target_type/target_id fields and indexes
- `backend/apps/audit/services.py` (modified) — Added target_type/target_id kwargs with validation
- `backend/apps/audit/admin.py` (modified) — Added target fields to list_display and list_filter
- `backend/apps/audit/selectors.py` (new) — Batch-scoped audit query helpers
- `backend/apps/audit/migrations/0003_add_batch_event_types_and_target_linkage.py` (new) — Additive migration
- `backend/apps/audit/tests/test_services.py` (modified) — Extended with target linkage and batch event tests
- `backend/apps/audit/tests/test_selectors.py` (new) — Selector tests
- `backend/apps/audit/tests/test_admin.py` (new) — Admin immutability and field display tests
- `docs/implementation/audit-event-taxonomy.md` (new) — Event taxonomy documentation
