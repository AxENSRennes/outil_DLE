# Story 4.2: Correct Previously Entered Batch Data with Required Reason for Change

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator or authorized production user,
I want to correct previously entered batch data through a controlled change flow with a required reason,
so that dossier errors can be fixed without losing traceability or creating silent overwrites.

## Acceptance Criteria

1. **Given** a batch step already contains saved or completed data, **When** an authorized user initiates a correction on an editable regulated value, **Then** the system creates a controlled correction action rather than silently replacing the prior value, **And** the corrected record remains linked to the affected batch context.
2. **Given** regulated corrections require justification, **When** a user submits a correction, **Then** the system requires a reason for change before accepting it, **And** the reason is stored with the correction event.
3. **Given** attribution must remain explicit, **When** a correction is accepted, **Then** the system records who made the correction and when it was made, **And** the corrected value can be distinguished from the prior value in later traceability views.
4. **Given** some users may not be authorized to modify regulated data, **When** an unauthorized user attempts to submit a correction, **Then** the system rejects the action server-side, **And** the original regulated value remains unchanged.
5. **Given** this story is focused on the correction transaction itself, **When** it is implemented, **Then** authorized users can submit controlled corrections with required justification, **And** changed-since-review flags, reviewer history surfaces, and post-correction disposition workflows remain outside the scope of this story.

## Tasks / Subtasks

- [x] Add `data_json` field to BatchStep for step field data storage (AC: 1, 3)
  - [x] Add `data_json = JSONField(default=dict, blank=True)` to `BatchStep` model in `backend/apps/batches/models.py` for storing step field values as `{ "field_name": value }` pairs.
  - [x] Generate additive migration `backend/apps/batches/migrations/0003_batchstep_data_json.py`.
  - [x] Existing BatchStep rows get empty dict default — no data loss.

- [x] Create correction domain service (AC: 1, 2, 3)
  - [x] Create `backend/apps/batches/domain/__init__.py` and `backend/apps/batches/domain/corrections.py`.
  - [x] Implement `submit_correction(*, step: BatchStep, actor: User, site: Site, corrections: list[dict], reason_for_change: str) -> AuditEvent`:
    - Validate step status is correctable (`in_progress`, `complete`, or `signed`; reject `not_started`).
    - Validate `reason_for_change` is non-empty after stripping whitespace.
    - Validate `corrections` list is non-empty and each entry has `field_name` (str, non-empty) and `new_value`.
    - For each correction entry, capture the old value from `step.data_json.get(field_name)`.
    - Apply corrections to `step.data_json` — update each field_name with the new_value.
    - Save the updated `step.data_json` via `step.save(update_fields=["data_json"])`.
    - Record `AuditEventType.CORRECTION_SUBMITTED` audit event with `target_type="batch_step"`, `target_id=step.pk`, and metadata: `{ "batch_id": step.batch_id, "reason_for_change": reason_for_change, "corrections": [{ "field_name": ..., "old_value": ..., "new_value": ... }], "ip_address": ... }`.
    - Wrap both the data update and the audit write in `transaction.atomic()` — fail-closed pattern.
    - Return the created `AuditEvent`.
  - [x] Raise `ValueError` if step status is `not_started` (no data to correct).
  - [x] Raise `ValueError` if `reason_for_change` is blank.

- [x] Create correction API endpoint (AC: 1, 2, 3, 4)
  - [x] Create `backend/apps/batches/api/__init__.py`, `backend/apps/batches/api/serializers.py`, `backend/apps/batches/api/views.py`, `backend/apps/batches/api/urls.py`.
  - [x] Implement `CorrectionRequestSerializer`:
    - `corrections` field: `ListField(child=CorrectionEntrySerializer())` — typed nested serializer, NOT bare `ListField`.
    - `reason_for_change` field: `CharField(required=True, min_length=1, max_length=2000)`.
  - [x] Implement `CorrectionEntrySerializer`:
    - `field_name`: `CharField(required=True, min_length=1, max_length=200)`.
    - `new_value`: field accepting string/number/bool/null (use a custom field or `serializers.JSONField()` since values are truly dynamic).
  - [x] Implement `CorrectionResponseSerializer`:
    - `correction_id`: `IntegerField` (the AuditEvent PK).
    - `step_id`: `IntegerField`.
    - `corrected_at`: `DateTimeField`.
    - `corrected_by`: `IntegerField` (actor PK).
    - `corrections_applied`: typed nested list with `field_name`, `old_value`, `new_value`.
    - `reason_for_change`: `CharField`.
  - [x] Implement `SubmitCorrectionView(APIView)`:
    - URL: `POST /api/v1/batch-steps/<step_id>/corrections`.
    - Permission: `IsAuthenticated` + `SiteScopedRolePermission` with `required_site_roles = (SiteRole.OPERATOR, SiteRole.PRODUCTION_REVIEWER)`.
    - Resolve the step directly and load `batch.site` for the site-scoped role check.
    - Use `get_site_for_object(obj)` returning `step.batch.site` for site-scoped role check.
    - On 403 or 404 for step: return 404 (fail-closed, no enumeration — same pattern as `ReviewSummaryView`).
    - Deserialize request with `CorrectionRequestSerializer`.
    - Call `submit_correction(...)` domain service.
    - Return `CorrectionResponseSerializer` with HTTP 201.
    - On `ValueError` from domain service: return 400 with problem-details JSON.
  - [x] Wire URL in `backend/apps/batches/api/urls.py` and include in main URL conf.
  - [x] Add drf-spectacular `@extend_schema` decorators for OpenAPI generation.

- [x] Add comprehensive tests (AC: 1, 2, 3, 4, 5)
  - [x] Create `backend/apps/batches/tests/__init__.py`, `backend/apps/batches/tests/test_corrections_domain.py`, `backend/apps/batches/tests/test_corrections_api.py`.
  - [x] **Domain tests** (`test_corrections_domain.py`):
    - Correction on `in_progress` step succeeds with audit event and data update.
    - Correction on `complete` step succeeds.
    - Correction on `signed` step succeeds (post-signature correction).
    - Correction on `not_started` step raises `ValueError`.
    - Empty `reason_for_change` raises `ValueError`.
    - Whitespace-only `reason_for_change` raises `ValueError`.
    - Empty `corrections` list raises `ValueError`.
    - Correction entry with empty `field_name` raises `ValueError`.
    - Old value is correctly captured in audit event metadata.
    - Correcting a non-existent field captures `null` as old value.
    - Multiple field corrections in single request — all applied atomically.
    - Audit event has correct `target_type="batch_step"`, `target_id=step.pk`.
    - Audit event metadata contains `batch_id`, `reason_for_change`, `corrections`, `ip_address`.
    - Transaction atomicity: if audit event write fails, step data is NOT updated.
    - Audit event actor matches the provided actor.
  - [x] **API tests** (`test_corrections_api.py`):
    - Authenticated operator can submit correction — 201 response with correct shape.
    - Authenticated production_reviewer can submit correction — 201.
    - Unauthenticated request → 401.
    - User without OPERATOR or PRODUCTION_REVIEWER role on the batch's site → 404 (fail-closed).
    - Missing `reason_for_change` → 400.
    - Empty `corrections` list → 400.
    - Missing `new_value` → 400.
    - Object/array `new_value` payloads → 400.
    - Non-existent step_id → 404.
    - Not-started step correction → 400.
    - Response includes `correction_id`, `step_id`, `corrected_at`, `corrected_by`, `corrections_applied`, `reason_for_change`.

- [x] Run quality gates (AC: all)
  - [x] `make lint`
  - [x] `make typecheck`
  - [x] `make test`
  - [x] `make architecture-check`
  - [x] `make check`

## Dev Notes

### Story Intent

This story implements the **controlled correction transaction** for batch step data. The core requirement from GxP compliance is that regulated data corrections must never silently overwrite prior values — they must create an explicit, attributed, justified correction event. The `CORRECTION_SUBMITTED` audit event type was already established in Story 4.1 specifically for this purpose.

The correction flow is a first-class domain action (architecture: `request_correction`), not a generic PATCH. It captures old value, new value, reason for change, and actor attribution in a single atomic transaction. The audit event metadata serves as the permanent, immutable record of what changed and why.

### Scope Boundaries

**In scope:**
- `data_json` field on BatchStep for step field data storage
- Correction domain service with fail-closed audit recording
- REST API endpoint for submitting corrections
- Request/response serializers with typed nested structure
- Authorization enforcement (site-scoped role check)
- Comprehensive domain and API tests

**Out of scope:**
- Setting `changed_since_review`, `changed_since_signature`, or `review_required` flags (Story 4.3)
- Reviewer history views or change history API (Story 4.4)
- Frontend correction modal, ChangeHistoryBlock component, or any UI
- PIN-based step-up re-authentication before correction (will be wired by the frontend calling the existing re-auth endpoint before submitting the correction)
- Return-for-correction batch lifecycle transitions (quality review disposition)
- Step completion or signature workflows (Epic 3)

### Technical Requirements

- Use `/home/axel/wsl_venv/bin/python` for Django management commands, tests, and package operations.
- The correction is an **atomic domain transaction**: both the step data update and the audit event write must succeed or both must roll back. Use `transaction.atomic()`.
- Follow the fail-closed pattern from Story 4.1: if the audit write fails, the data correction must not be persisted. The domain service wraps both operations in a single transaction.
- The `CORRECTION_SUBMITTED` audit event type already exists in `AuditEventType` (added in Story 4.1). Do NOT re-add it. Use it as-is.
- Corrections do not change step status. A `complete` step remains `complete` after correction. A `signed` step remains `signed`. Status transitions are not part of this story.
- The `data_json` JSONField stores step field values as flat key-value pairs: `{"temperature": "22.5", "pressure": "1.013", "operator_note": "..."}`. Field names are strings; values may be string, number, boolean, or null.
- Audit event metadata must capture the correction detail per the established taxonomy: `batch_id` (int), `reason_for_change` (str), `corrections` (list of `{field_name, old_value, new_value}`), `ip_address` (str, advisory).
- Never use `DictField()` or bare `ListField()` for structured correction payloads in serializers — always use typed nested serializers (CLAUDE.md rule).

### Architecture Compliance

- Keep correction domain logic in `backend/apps/batches/domain/corrections.py`. Do not put business rules in serializers or views.
- The API layer (`api/views.py`) handles HTTP concerns: deserialization, permission checks, response formatting. It calls the domain service for business logic.
- Follow the established modular-monolith boundary:
  - `models.py` — data definitions (BatchStep.data_json addition)
  - `domain/corrections.py` — write operations (submit_correction)
  - `api/serializers.py` — request/response shape validation
  - `api/views.py` — HTTP endpoints
  - `api/urls.py` — URL routing
  - `tests/` — test coverage
- The batches domain service depends on `apps.audit.services.record_audit_event` for audit recording. This is a valid cross-app dependency: domain service → audit service.
- `apps.batches.domain` must not import from `apps.batches.api` or any other feature's `api/` package.
- The endpoint follows the architecture's canonical action pattern: `POST /api/v1/batch-steps/{step_id}/corrections`. This is a dedicated action endpoint, NOT a generic PATCH.
- Return 404 for both missing resources AND authorization failures (fail-closed, no enumeration — same pattern as `ReviewSummaryView`).
- Errors use problem-details JSON format via the existing `problem_details_exception_handler` in `backend/shared/api/exceptions.py`.
  [Source: backend/shared/api/exceptions.py]

### Library / Framework Requirements

- Django 5.2 LTS (pinned `>=5.2,<5.3` in pyproject.toml). Do not upgrade.
- Django REST Framework 3.16.x with `SessionAuthentication`.
- drf-spectacular 0.29.x for OpenAPI schema generation. Add `@extend_schema` decorators.
- pytest-django for tests. Use `@pytest.mark.django_db` on all database tests.
- factory-boy for test fixtures. Reuse existing factories if available, or create `BatchFactory`, `BatchStepFactory` in `backend/apps/batches/tests/factories.py`.
- mypy with django-stubs for type checking.
- ruff for linting.
- bandit for security scanning.

### File Structure Requirements

**New files to create:**
- `backend/apps/batches/domain/__init__.py` — Package init.
- `backend/apps/batches/domain/corrections.py` — Correction domain service.
- `backend/apps/batches/api/__init__.py` — Package init.
- `backend/apps/batches/api/serializers.py` — Request/response serializers.
- `backend/apps/batches/api/views.py` — SubmitCorrectionView.
- `backend/apps/batches/api/urls.py` — URL routing.
- `backend/apps/batches/tests/__init__.py` — Package init (if not exists).
- `backend/apps/batches/tests/factories.py` — Test factories for Batch, BatchStep.
- `backend/apps/batches/tests/test_corrections_domain.py` — Domain service tests.
- `backend/apps/batches/tests/test_corrections_api.py` — API endpoint tests.
- `backend/apps/batches/migrations/0003_batchstep_data_json.py` — Additive migration for data_json field.

**Existing files to modify:**
- `backend/apps/batches/models.py` — Add `data_json` JSONField to BatchStep.
- `backend/config/urls.py` (or equivalent root URL conf) — Include batches API URLs.

**Do NOT create:**
- Any frontend files (no React components, no TypeScript).
- Any new audit event types (use existing `CORRECTION_SUBMITTED`).
- Any review/disposition endpoints (Story 4.3/4.4).
- Any correction-related selectors for history display (Story 4.4).

### Testing Requirements

- **Domain tests** (`test_corrections_domain.py`):
  - Happy path: correction on `in_progress`, `complete`, and `signed` steps.
  - Error case: correction on `not_started` step rejected.
  - Error case: blank or whitespace-only `reason_for_change` rejected.
  - Error case: empty corrections list rejected.
  - Error case: correction entry with empty `field_name` rejected.
  - Verify old value captured correctly in audit metadata (existing value and null for non-existent field).
  - Verify multiple corrections in single request all applied atomically.
  - Verify audit event attributes: `event_type`, `target_type`, `target_id`, `actor`, `metadata` keys.
  - Verify transaction atomicity: simulate audit write failure → step data unchanged.
  - Verify `data_json` is updated with new values after correction.

- **API tests** (`test_corrections_api.py`):
  - 201 response for authorized operator with valid payload.
  - 201 response for authorized production_reviewer.
  - 403 for unauthenticated request.
  - 404 for user without required site role (fail-closed).
  - 400 for missing `reason_for_change`.
  - 400 for empty corrections list.
  - 404 for non-existent batch or step.
  - 404 for step not belonging to specified batch.
  - Verify response shape matches `CorrectionResponseSerializer`.
  - Verify audit event created with correct metadata via DB assertion.

- **Quality commands:**
  - `make lint`
  - `make typecheck`
  - `make test`
  - `make architecture-check`
  - `make check`

### Previous Story Intelligence

**Story 4.1 established the audit infrastructure this story depends on:**
- `AuditEventType.CORRECTION_SUBMITTED` is already defined in the enum and migrated.
- `record_audit_event()` accepts `target_type`, `target_id`, `metadata`, and `actor` — use it directly.
- The audit event taxonomy documents `correction_submitted` with recommended metadata: `batch_id`, `reason_for_change`, `field_name`. Story 4.2 extends this with `corrections` list containing `{field_name, old_value, new_value}` per correction.
- Fail-closed pattern is critical: if audit write fails, the correction must roll back. Use `transaction.atomic()` wrapping both operations.
- Model-level validation ensures batch-domain events require an actor. The domain service must always pass `actor`.
  [Source: backend/apps/audit/models.py, backend/apps/audit/services.py]

**Story 4.1 review findings relevant to 4.2:**
- [High] Actor enforcement is now in both service and model layers — the domain service must always provide the actor.
- [Medium] target_type is normalized (stripped) by the model — pass clean values.
- [Medium] Tests should verify not just service-level validation but also that the data state is correct after the operation.

**Story 5.1 established the reviews app pattern to follow:**
- `ReviewSummaryView` uses fail-closed 404 for both missing resources and permission failures — replicate this pattern.
- `SiteScopedRolePermission` with `get_site_for_object()` — reuse for correction endpoint.
- `domain/` contains frozen dataclasses for value objects; `selectors/` for read queries.
- `api/serializers.py` uses typed nested serializers (e.g., `StepSummarySerializer`, `FlagCountsSerializer`).
  [Source: backend/apps/reviews/api/views.py, backend/apps/reviews/domain/review_summary.py]

### Git Intelligence Summary

Recent commits show the audit infrastructure is stable and battle-tested:
- `551fb04` Merged PR #11 — fixed audit CHECK constraint conditions.
- `1cd46f6` Generated missing migrations for audit event_type and sites product options.
- `030f264` Fixed audit CHECK constraints with `condition=` and added `lock_failed` to 0005.
- `2d7a3b5` Merged PR #9 — Story 4.1 batch audit events.
- `2501751` Merged PR #7 — Story 2.1 MMR and draft version lifecycle.

Practical implications:
- The audit app has been through multiple rounds of hardening. Reuse `record_audit_event()` as-is.
- The batches app is still a stub — Story 4.2 is the first to add domain logic and API endpoints to it.
- The reviews app (Story 5.1) provides the established pattern for API views, serializers, and site-scoped permissions in a feature app.
- Migration numbering: audit is at 0008, batches is at 0002. Next batches migration is 0003.

### Batch-Domain Event Reference

The `correction_submitted` event is documented in `docs/implementation/audit-event-taxonomy.md`:

| Event Type | Workflow Action | target_type | Metadata |
|---|---|---|---|
| `correction_submitted` | `request_correction` | `batch_step` | `batch_id`, `reason_for_change`, `corrections: [{field_name, old_value, new_value}]`, `ip_address` |

### API Contract Reference

**Endpoint:** `POST /api/v1/batch-steps/{step_id}/corrections`

**Request body:**
```json
{
  "corrections": [
    { "field_name": "temperature", "new_value": "23.1" },
    { "field_name": "pressure", "new_value": "1.015" }
  ],
  "reason_for_change": "Transcription error on temperature and pressure readings"
}
```

**Response (201 Created):**
```json
{
  "correction_id": 42,
  "step_id": 7,
  "corrected_at": "2026-03-13T14:30:00Z",
  "corrected_by": 5,
  "corrections_applied": [
    { "field_name": "temperature", "old_value": "22.5", "new_value": "23.1" },
    { "field_name": "pressure", "old_value": "1.013", "new_value": "1.015" }
  ],
  "reason_for_change": "Transcription error on temperature and pressure readings"
}
```

**Error responses:**
- 400: Invalid payload (missing reason, empty corrections, invalid field_name) — problem-details JSON.
- 404: Step not found or user not authorized (fail-closed).
- 403: Not authenticated.

### Project Structure Notes

- The batches app (`backend/apps/batches/`) currently contains only models, admin, and migrations (stub for Story 5.1).
- This story adds the first domain logic (`domain/corrections.py`) and API endpoints (`api/`) to the batches app.
- Follow the same sub-package structure as the reviews app: `domain/`, `api/`, `tests/`.
- The `data_json` field on BatchStep is the first step toward full step data storage. Later stories in Epic 2/3 will expand on this with template-driven field schemas, validation rules, and completion gating.
- The `changed_since_review`, `changed_since_signature`, and `review_required` boolean flags already exist on BatchStep. Story 4.3 will use them — this story does NOT set them.

### References

- [epics.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/planning-artifacts/epics.md) — Epic 4 scope, Story 4.2 acceptance criteria, cross-story dependencies, Story 4.3/4.4 scope boundaries
- [architecture.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/planning-artifacts/architecture.md) — `POST /api/v1/batch-steps/{id}/corrections` endpoint contract, `request_correction` canonical action, hybrid relational+JSONB model, fail-closed transaction pattern, canonical batch lifecycle states
- [prd.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/planning-artifacts/prd.md) — FR18 (controlled change flow), FR19 (reason for change), FR20 (re-review after changes), FR21 (explicit integrity states), NFR security (100% audit trail coverage)
- [ux-design-specification.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/planning-artifacts/ux-design-specification.md) — Correction modal UX, Journey 2 (Karim correction flow), ChangeHistoryBlock component anatomy, "correction is a workflow not a failure" principle, reason-for-change textarea, PIN re-auth before correction
- [architecture-decisions.md](/home/axel/DLE-SaaS-epic-4/docs/decisions/architecture-decisions.md) — Decision 7 (review states survive corrections), Decision 16 (frozen workflow states), Decision 17 (action-based workflow contracts)
- [audit-event-taxonomy.md](/home/axel/DLE-SaaS-epic-4/docs/implementation/audit-event-taxonomy.md) — `correction_submitted` event definition, metadata contract, fail-closed transaction example
- [4-1-record-attributed-audit-events-for-regulated-batch-actions.md](/home/axel/DLE-SaaS-epic-4/_bmad-output/implementation-artifacts/4-1-record-attributed-audit-events-for-regulated-batch-actions.md) — Previous story learnings, audit service API, review findings, established patterns
- [backend/apps/audit/models.py](/home/axel/DLE-SaaS-epic-4/backend/apps/audit/models.py) — AuditEventType.CORRECTION_SUBMITTED, model constraints, fail-closed model validation
- [backend/apps/audit/services.py](/home/axel/DLE-SaaS-epic-4/backend/apps/audit/services.py) — `record_audit_event()` signature, metadata sanitization, actor enforcement
- [backend/apps/audit/selectors.py](/home/axel/DLE-SaaS-epic-4/backend/apps/audit/selectors.py) — `get_audit_events_for_target()` for querying correction history
- [backend/apps/batches/models.py](/home/axel/DLE-SaaS-epic-4/backend/apps/batches/models.py) — BatchStep model (stub), StepStatus enum, review flags, BatchStatus enum
- [backend/apps/reviews/api/views.py](/home/axel/DLE-SaaS-epic-4/backend/apps/reviews/api/views.py) — `ReviewSummaryView` pattern (fail-closed 404, SiteScopedRolePermission, get_site_for_object)
- [backend/apps/reviews/domain/review_summary.py](/home/axel/DLE-SaaS-epic-4/backend/apps/reviews/domain/review_summary.py) — Domain logic pattern with frozen dataclasses
- [backend/shared/api/exceptions.py](/home/axel/DLE-SaaS-epic-4/backend/shared/api/exceptions.py) — problem_details_exception_handler for error responses
- [backend/shared/permissions/site_roles.py](/home/axel/DLE-SaaS-epic-4/backend/shared/permissions/site_roles.py) — SiteScopedRolePermission, get_site_for_object pattern
- [backend/shared/http.py](/home/axel/DLE-SaaS-epic-4/backend/shared/http.py) — `get_client_ip()` helper for advisory IP in audit metadata
- [Makefile](/home/axel/DLE-SaaS-epic-4/Makefile) — Quality gate commands
- [pyproject.toml](/home/axel/DLE-SaaS-epic-4/pyproject.toml) — Pinned Django 5.2, DRF 3.16, drf-spectacular 0.29
- [CLAUDE.md](/home/axel/DLE-SaaS-epic-4/CLAUDE.md) — Fail-closed pattern, no DictField/ListField for structured data, audit immutability, architecture boundaries, API contract rules

## Change Log

- 2026-03-13: Implemented controlled correction transaction for batch step data — domain service, API endpoint, and comprehensive tests (29 tests total: 15 domain + 14 API).
- 2026-03-13: Fixed code review findings by switching to the canonical step-scoped correction route, restricting correction values to JSON scalars/null, deriving audit site from the batch step, and locking the step row before applying corrections.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Migration 0003_batchstep_data_json required `--fake` apply because column already existed in database from prior development.
- Unauthenticated endpoint returns 401 (not 403) due to `get_authenticate_header` returning "Session" — test adjusted to match actual DRF behavior.
- Targeted correction pytest runs required `--reuse-db --nomigrations` because the shared local `test_dle_saas` database was already in use by another session.

### Completion Notes List

- Added `data_json = JSONField(default=dict, blank=True)` to BatchStep model with additive migration 0003.
- Hardened `submit_correction()` in `batches/domain/corrections.py` with explicit `new_value` presence checks, scalar-only correction values, row-level locking via `select_for_update()`, and audit-site derivation from `step.batch.site`.
- Switched `SubmitCorrectionView` to the canonical step-scoped endpoint `POST /api/v1/batch-steps/{step_id}/corrections` while keeping fail-closed 404 authorization behavior through `step.batch.site`.
- Expanded correction coverage to 39 targeted tests, including missing `new_value`, object/array rejection, batch-site audit attribution, and stale-instance overwrite protection.
- Verified with `/home/axel/wsl_venv/bin/pytest backend/apps/batches/tests/test_corrections_domain.py backend/apps/batches/tests/test_corrections_api.py -q --reuse-db --nomigrations`, `/home/axel/wsl_venv/bin/python manage.py check`, and full `make check`.

### File List

**New files:**
- backend/apps/batches/domain/__init__.py
- backend/apps/batches/domain/corrections.py
- backend/apps/batches/api/__init__.py
- backend/apps/batches/api/serializers.py
- backend/apps/batches/api/views.py
- backend/apps/batches/api/urls.py
- backend/apps/batches/tests/__init__.py
- backend/apps/batches/tests/test_corrections_domain.py
- backend/apps/batches/tests/test_corrections_api.py
- backend/apps/batches/migrations/0003_batchstep_data_json.py

**Modified files:**
- backend/apps/batches/models.py (added data_json field to BatchStep)
- backend/shared/api/urls.py (included batches API URLs)
- _bmad-output/planning-artifacts/architecture.md (aligned correction endpoint contract and response summary)
- _bmad-output/implementation-artifacts/4-2-correct-previously-entered-batch-data-with-required-reason-for-change.md (updated route, verification notes, and review outcome)

### Senior Developer Review (AI)

**Reviewer:** Axel
**Date:** 2026-03-13
**Outcome:** Approved after fixes

#### Summary

- Re-reviewed the Story 4.2 implementation after fixing the previously reported issues.
- The git worktree had tracked code and story/doc updates only for the correction flow scope.
- Re-verified with:
  - `/home/axel/wsl_venv/bin/pytest backend/apps/batches/tests/test_corrections_domain.py backend/apps/batches/tests/test_corrections_api.py -q --reuse-db --nomigrations`
  - `/home/axel/wsl_venv/bin/python manage.py check`

#### Findings

1. **[Resolved] Missing `new_value` entries were accepted and silently wrote `null`.**
   The correction service and API now reject entries that omit `new_value`, closing the silent data-loss path for non-API callers and invalid payloads.

2. **[Resolved] The API accepted nested JSON objects and arrays for regulated correction values.**
   The request contract is now limited to string, number, boolean, or `null`, matching the story scope and preventing nested JSON blobs from entering `data_json`.

3. **[Resolved] Concurrent or stale correction writes could overwrite newer batch-step data.**
   The domain service now reloads the current row under `select_for_update()` before computing old/new values and saving, so corrections are based on the locked database state rather than a stale in-memory instance.

4. **[Resolved] Audit events could be recorded under a caller-supplied site unrelated to the corrected step.**
   The correction service now derives the audit site from `step.batch.site`, so correction events cannot drift away from the batch context.

5. **[Resolved] The public contract and implementation used different correction URLs.**
   The endpoint, tests, and architecture artifact are now aligned on `POST /api/v1/batch-steps/{step_id}/corrections`.

#### Developer Follow-up

- 2026-03-13: Refactored the correction endpoint to the canonical step-scoped route and updated tests/docs to match.
- 2026-03-13: Added scalar-only correction value validation in both serializer and domain layers.
- 2026-03-13: Added row locking and stale-instance protection in `submit_correction()`.
- 2026-03-13: Re-ran targeted correction suites successfully, completed a Django system check, and passed `make check`.
