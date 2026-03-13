# Story 6.1: Compose the Required Dossier Structure from Batch Context

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a production or quality user,
I want the system to determine which dossier elements are required for a batch based on its operational context,
so that execution and review are driven by the right document set instead of a generic one-size-fits-all packet.

## Acceptance Criteria

1. Given a batch contains contextual attributes such as line, machine, format family, or paillette relevance, when the system resolves the dossier structure for that batch, then it determines which sub-documents and controls are required for that batch context, and the required structure is attached to the batch as a governed operational expectation.
2. Given not all dossier elements are applicable in every situation, when the system evaluates the batch context, then non-applicable controls or documents are excluded or marked not applicable according to governed rules, and they do not behave as if they were mandatory by default.
3. Given execution and review both depend on the same dossier expectation, when the required dossier structure is generated, then it can be reused by both workflow execution and completeness review, and later stories do not need to recompute separate versions of the required document set.
4. Given dossier composition must remain backend-owned business logic, when this story is implemented, then the conditional composition rules are enforced from a canonical backend service or read model, and frontend features consume the result instead of implementing document-selection logic locally.
5. Given this story should provide a standalone business capability, when it is completed, then the system can resolve the correct dossier structure from batch context, and repeated control generation, governed calculations, and export behavior remain outside the scope of this story.

## Tasks / Subtasks

- [x] Create the `exports` Django app with the standard app layout (AC: 4, 5)
  - [x] Create `backend/apps/exports/` following the canonical structure: `api/`, `domain/`, `selectors/`, `tests/`, `models.py`, `admin.py`, `apps.py`
  - [x] Register `ExportsConfig` in `INSTALLED_APPS` in `backend/config/settings/base.py`
  - [x] Verify the app passes `make check` with no models yet

- [x] Define dossier composition models (AC: 1, 2, 3)
  - [x] Create `DossierProfile` model — a reusable composition rule set linked to an MMR template version. Stores the governed rules that determine which sub-documents and controls are required based on batch contextual attributes. Uses a JSONB field for the conditional rule definitions (e.g., "if paillette_present then require sub-document X") and a structured list of all possible sub-document/control identifiers the template can produce.
  - [x] Create `BatchDossierStructure` model — the resolved dossier expectation for a specific batch. Links to the `Batch` and to the `DossierProfile` that was used for resolution. Stores the resolved list of required elements, excluded/not-applicable elements, and the batch context snapshot that was evaluated. Immutable once generated (append-only semantics for audit traceability).
  - [x] Create `DossierElement` model — an individual item within a resolved `BatchDossierStructure`. Each element represents a required sub-document or control with: element type (sub-document, in-process control, box-level control, checklist item), display order, applicability status (required, not_applicable), and a reference identifier linking back to the template definition.
  - [x] Use `on_delete=models.PROTECT` on all foreign keys to maintain referential integrity for regulated data.
  - [x] Add appropriate database indexes for batch-based lookups and element ordering.
  - [x] Generate additive-only migrations.

- [x] Implement the dossier composition domain service (AC: 1, 2, 4)
  - [x] Create `backend/apps/exports/domain/composition.py` with a `resolve_dossier_structure(batch)` function that:
    - Reads the batch's contextual attributes (line, machine, format family, paillette relevance) from the batch and its template version
    - Loads the associated `DossierProfile` from the batch's template version
    - Evaluates the conditional composition rules against the batch context
    - Determines which sub-documents and controls are required vs. not-applicable
    - Creates and persists a `BatchDossierStructure` with the resolved `DossierElement` entries
    - Returns the resolved structure for immediate use
  - [x] Implement rule evaluation logic that supports context-based inclusion/exclusion:
    - Boolean context flags (e.g., paillette_present → include paillette controls)
    - Categorical matching (e.g., format_family == "X" → include format-specific sub-documents)
    - Default-required elements that are always included regardless of context
  - [x] Ensure the composition service is idempotent: calling it again for the same batch returns the existing resolved structure rather than creating duplicates, unless explicitly forced to regenerate
  - [x] Keep the service stateless regarding external dependencies — it reads from models and writes to models, no external API calls

- [x] Implement selectors for dossier structure read models (AC: 3)
  - [x] Create `backend/apps/exports/selectors/dossier_structure.py` with query functions:
    - `get_batch_dossier_structure(batch_id)` — returns the resolved structure with all elements for a given batch
    - `get_dossier_completeness_checklist(batch_id)` — returns the expected document checklist derived from the resolved structure, suitable for review surfaces
    - `has_resolved_dossier(batch_id)` — boolean check for whether a batch has a resolved structure
  - [x] Use dataclass-based read models (frozen=True) for clean API boundaries
  - [x] Optimize queries with `select_related` and `prefetch_related` where appropriate

- [x] Expose dossier structure via REST API (AC: 3, 4)
  - [x] Create `GET /api/v1/batches/{batch_id}/dossier-structure/` endpoint that returns the resolved dossier structure for a batch
  - [x] Create `POST /api/v1/batches/{batch_id}/resolve-dossier/` action endpoint that triggers dossier composition for a batch that doesn't yet have a resolved structure
  - [x] Add response serializers for the dossier structure read model including nested elements
  - [x] Apply site-scoped role permissions — production and quality roles can read; composition trigger requires appropriate role
  - [x] Add `@extend_schema()` decorators for drf-spectacular OpenAPI generation
  - [x] Enforce CSRF protection on the POST action endpoint
  - [x] Wire URLs into `backend/shared/api/urls.py` under the existing `/api/v1/` prefix

- [x] Add Django admin for dossier models (AC: 1, 2)
  - [x] Register `DossierProfile` with admin — allow creation and editing of composition rules
  - [x] Register `BatchDossierStructure` as read-only in admin (override `has_add_permission`, `has_change_permission`, `has_delete_permission` to return `False`) — resolved structures are governed records
  - [x] Register `DossierElement` as read-only inline on `BatchDossierStructure`

- [x] Write comprehensive tests (AC: 1, 2, 3, 4, 5)
  - [x] Domain tests for composition service:
    - Resolves correct elements for a batch with full context (all attributes present)
    - Excludes non-applicable elements based on context (e.g., no paillette controls when paillette_present=False)
    - Includes default-required elements regardless of context
    - Handles edge cases: missing context attributes, empty rule set, all elements excluded
    - Idempotency: second call returns existing structure without creating duplicates
  - [x] API tests:
    - GET returns resolved structure with correct element list
    - GET returns 404 for batch without resolved structure
    - POST resolve-dossier creates structure and returns it
    - POST resolve-dossier for already-resolved batch returns existing structure
    - Permission denied for unauthenticated requests
    - CSRF enforced on POST endpoint
  - [x] Model tests:
    - DossierProfile stores and retrieves JSONB rules correctly
    - BatchDossierStructure enforces referential integrity
    - DossierElement ordering is consistent
  - [x] Run `make check` before closing the story

## Dev Notes

### Story Intent

This story introduces the backend-owned dossier composition capability that all later Epic 6 stories depend on. The system must resolve which sub-documents and controls are required for a specific batch based on its operational context (line, machine, format family, paillette presence), and persist that resolved structure as the governed expectation for execution and review.

This is the foundation for:
- Story 6.2 (repeated control generation — builds on resolved structure to create control instances)
- Story 6.3 (governed calculations — uses resolved structure to identify calculation targets)
- Story 6.4 (reference attachment — attaches references to elements in the resolved structure)
- Story 6.5 (dossier export — exports the complete resolved and populated dossier)

The story should deliver composition rules, a resolution service, and a read API. It should NOT implement repeated control instantiation, calculations, reference attachment, or export.

### Story Foundation

- Epic 6 is about contextual dossier composition and export.
- This story covers FR45 (conditional sub-document selection based on context), FR51 (marking controls as not-applicable), and partially FR48 (completeness checklist foundation).
- The story must remain self-contained: it resolves and persists the dossier structure as a standalone capability without requiring later stories.
- Execution and review workflows (Epics 3, 5) will consume the resolved structure as a read model — this story provides the source of truth.

### Dependencies on Earlier Epics

**CRITICAL: This story depends on models and services from earlier epics that must be implemented first.**

- **Epic 2 (Template Governance):** Requires `MMR`, `MMRVersion` models with template definitions, step structures, and the batch instantiation mechanism. The dossier composition rules are defined at the template version level.
- **Epic 2, Story 2.5:** Requires `Batch` model with contextual attributes (line, machine, format_family, paillette_present) and a link to the originating `MMRVersion`.
- **Epic 3 (Batch Execution):** The batch execution flow triggers dossier resolution when a batch is opened. While Story 6.1 doesn't implement execution, it needs the batch model and context attributes.

If implementing out of order, the developer may need to:
1. Create stub/foundation models for `Batch` and `MMRVersion` if they don't exist yet
2. Or coordinate with Epic 2 implementation to ensure models are available
3. The `DossierProfile` model links to `MMRVersion`; the `BatchDossierStructure` links to `Batch`

### Technical Requirements

- Use `/home/axel/wsl_venv/bin/python` for Django management commands, tests, and package operations.
- The architecture places dossier/export FRs in `backend/apps/exports/`. Use this as the app name even though this story focuses on composition rather than export — it keeps the codebase aligned with the planned architecture.
- Dossier composition rules use a JSONB field within `DossierProfile` for flexible, configurable conditional logic. This follows the architecture's "hybrid relational + JSONB model" strategy: relational tables for identity and relationships, JSONB for configurable rule definitions.
- The composition service must be deterministic: same batch context + same rules = same resolved structure, every time.
- The resolved `BatchDossierStructure` is immutable once created. If composition rules change, a new resolution can be triggered explicitly (force-regenerate), but the old structure remains for audit trail purposes.
- All domain logic lives in `backend/apps/exports/domain/composition.py` — no business rules in serializers, views, or admin.
- Do not introduce caching. PostgreSQL is the single source of truth per architecture decisions.
- Do not introduce async/background processing. Keep dossier resolution synchronous per MVP strategy.

### Architecture Compliance

- Create the new app at `backend/apps/exports/` following the canonical structure:
  - `api/` for serializers, views, route wiring, and request/response contracts
  - `domain/` for composition business logic
  - `selectors/` for optimized reads and query composition
  - `models.py` for data models
  - `tests/` for domain, API, and integration tests
- Domain code (`domain/`) must NOT import from `api/` packages — enforce the architecture boundary.
- API code (`api/`) can call domain services and selectors.
- Shared utilities (permissions, error handling) come from `backend/shared/` — do not duplicate.
- Follow the action-oriented API pattern: use explicit `POST .../resolve-dossier/` for composition triggers instead of generic PATCH mutations.
- Use problem-details error responses (already configured via `shared.api.exceptions.problem_details_exception_handler`).
- Use drf-spectacular `@extend_schema()` for OpenAPI documentation.
- Respect modular-monolith boundaries: the exports app can import from `batches` and `mmr` apps for model references, but should not reach into their `api/` packages.
- Run `python tools/check_backend_architecture.py` to verify boundary compliance.

### Library / Framework Requirements

- Django 5.2 LTS — do not upgrade. Use the pinned version from `pyproject.toml`.
- Django REST Framework 3.16+ with `SessionAuthentication` — same baseline as existing endpoints.
- drf-spectacular 0.29+ for OpenAPI schema generation on the new endpoints.
- PostgreSQL 17 for JSONB fields and querying of composition rules.
- No new dependencies required for this story. The JSONB rule evaluation is pure Python logic operating on deserialized JSON structures.
- CSRF protection must be enforced on unsafe (POST) endpoints using `@method_decorator(csrf_protect, name="dispatch")`.

### File Structure Requirements

- New app to create:
  - `backend/apps/exports/__init__.py`
  - `backend/apps/exports/apps.py` — `ExportsConfig` with `default_auto_field` and `verbose_name`
  - `backend/apps/exports/models.py` — `DossierProfile`, `BatchDossierStructure`, `DossierElement`
  - `backend/apps/exports/admin.py` — admin registrations with read-only for resolved structures
  - `backend/apps/exports/migrations/__init__.py`
  - `backend/apps/exports/domain/__init__.py`
  - `backend/apps/exports/domain/composition.py` — `resolve_dossier_structure()` service
  - `backend/apps/exports/selectors/__init__.py`
  - `backend/apps/exports/selectors/dossier_structure.py` — read model queries
  - `backend/apps/exports/api/__init__.py`
  - `backend/apps/exports/api/serializers.py` — response serializers for dossier structure
  - `backend/apps/exports/api/views.py` — API views for GET and POST endpoints
  - `backend/apps/exports/api/urls.py` — URL patterns
  - `backend/apps/exports/tests/__init__.py`
  - `backend/apps/exports/tests/test_composition.py` — domain service tests
  - `backend/apps/exports/tests/test_api.py` — API endpoint tests
  - `backend/apps/exports/tests/test_models.py` — model tests
- Existing files to modify:
  - `backend/config/settings/base.py` — add `ExportsConfig` to `INSTALLED_APPS`
  - `backend/shared/api/urls.py` — wire exports API URLs

### Testing Requirements

- Domain tests (`test_composition.py`):
  - `resolve_dossier_structure` produces correct elements for batch with all context attributes
  - Non-applicable elements are excluded when context flags are false (e.g., paillette_present=False)
  - Default-required elements always appear regardless of context
  - Categorical matching produces correct element set (e.g., format_family-specific documents)
  - Idempotency: second resolution call returns existing structure without duplication
  - Force-regenerate creates new structure while preserving old one
  - Edge cases: batch with no context attributes, profile with empty rules, profile with all-excluded rules
- API tests (`test_api.py`):
  - `GET /api/v1/batches/{id}/dossier-structure/` returns resolved structure with nested elements
  - `GET` returns 404 when batch has no resolved structure
  - `POST /api/v1/batches/{id}/resolve-dossier/` creates and returns resolved structure
  - `POST` for already-resolved batch returns existing structure (idempotent)
  - Unauthenticated requests are rejected (401)
  - Unauthorized roles are rejected (403)
  - CSRF is enforced on POST endpoint
  - Non-existent batch returns 404
- Model tests (`test_models.py`):
  - `DossierProfile` JSONB rules store and retrieve correctly
  - `BatchDossierStructure` enforces FK constraints (PROTECT)
  - `DossierElement` ordering is consistent
  - Admin permissions: resolved structures are read-only
- Quality commands:
  - `make lint`
  - `make typecheck`
  - `make test`
  - `make architecture-check`
  - Prefer `make check` before closing the story

### Previous Story Intelligence

- No previous stories exist in Epic 6 — this is the first story.
- From Epic 1 stories (the only implemented epic):
  - Story 1.3 established the canonical patterns for app creation, domain services, API views, serializers, admin, and tests. Follow these patterns exactly.
  - Story 1.3 review feedback highlighted the importance of fail-closed patterns, comprehensive negative-path testing, and CSRF enforcement — apply those lessons here.
  - The existing `apps.audit` module provides `record_audit_event()` — use it for any state-changing operations that need audit trails.
  - The `shared/permissions/site_roles.py` module provides `SiteScopedRolePermission` — reuse for endpoint authorization.
  - The `shared/api/exceptions.py` provides the problem-details error handler — already wired in DRF settings.
  - Test patterns: use `@pytest.mark.django_db`, the CSRF test helpers from `apps/authz/tests/helpers.py`, and `APIClient`.

### Git Intelligence Summary

- Recent commits (all from Epic 1, Story 1.3):
  - `bde7acc` Merge pull request #5 — workstation auth
  - `a980fe1` Harden audit event typing and lock throttling
  - `c70f8d2` fix(authz): harden FK, admin delete, CSRF and add lock fail-closed test
  - `600433f` fix(audit): protect FK integrity and add IP to success events
  - `5f14659` Extract shared client IP helper
- Practical implications:
  - The codebase emphasizes FK integrity with `PROTECT`, admin read-only for audit records, CSRF enforcement, and fail-closed security patterns
  - Follow the same commit discipline: small, focused commits with clear messages
  - The `shared/http.py` module provides `get_client_ip()` — reuse if audit events need IP context
  - Architecture boundary checks are enforced — `tools/check_backend_architecture.py` must pass

### Latest Technical Information

- Django 5.2 LTS is the current line (5.2.12 released 2026-03-04). Stay on 5.2 per `pyproject.toml` constraints.
- Django `JSONField` (backed by PostgreSQL `jsonb`) is fully supported for storing and querying composition rules. Key capabilities:
  - Direct JSON path lookups: `DossierProfile.objects.filter(rules__contains={"key": "value"})`
  - Nested key extraction: `F('rules__some_nested_key')`
  - No additional libraries needed for JSONB — it's built into Django's ORM
- DRF 3.16+ supports all patterns used in this story (SessionAuthentication, ViewSets, custom actions, nested serializers).
- drf-spectacular 0.29+ supports `@extend_schema()` for action endpoints and nested response serializers.
- No external library additions are needed for this story.

### Project Context Reference

No `project-context.md` file was present in the repository when this story was created.

Use these source artifacts instead:

- [epics.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/epics.md) — Epic 6 complete scope and all story definitions
- [architecture.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/architecture.md) — dossier composition strategy, backend app structure, model patterns, API contracts
- [prd.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/prd.md) — FR45 (conditional sub-documents), FR46 (repeated controls), FR47 (cross-document rules), FR48 (completeness), FR51 (not-applicable marking)
- [ux-design-specification.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/ux-design-specification.md) — DossierIntegritySummary component, review surfaces, step-first paradigm
- [architecture-decisions.md](/home/axel/DLE-SaaS/docs/decisions/architecture-decisions.md) — frozen domain model, hybrid relational+JSONB strategy, backend-owned composition
- [Makefile](/home/axel/DLE-SaaS/Makefile) — canonical local verification commands
- [pyproject.toml](/home/axel/DLE-SaaS/pyproject.toml) — pinned Django, DRF, and drf-spectacular versions
- [1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md](/home/axel/DLE-SaaS/_bmad-output/implementation-artifacts/1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md) — canonical patterns for app creation, domain services, API views, tests

### Project Structure Notes

- The backend currently has three feature apps: `authz`, `sites`, `audit`.
- The architecture reserves `exports/` for dossier composition and export features — this is the first app in that domain area.
- The architecture also reserves `mmr/`, `batches/`, `signatures/`, `reviews/`, `releases/`, `references/`, `integrations/` — none of these exist yet.
- This story's `exports` app will need FK references to `Batch` and `MMRVersion` models. If those models don't exist yet when implementation starts, coordinate with Epic 2 implementation or create the necessary foundation models first.
- The frontend reserves `frontend/src/features/dossier-exports/` for dossier-related UI features. This story is backend-only; no frontend work is required.
- `/api/v1/` is the canonical API prefix. New dossier endpoints should be wired there.

### References

- [epics.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/epics.md) — Epic 6 story definitions, acceptance criteria, and cross-story dependencies
- [architecture.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/architecture.md) — dossier composition service design, app structure, model patterns, API conventions, security requirements
- [prd.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/prd.md) — FR45, FR46, FR47, FR48, FR51, NFR performance/security/reliability requirements
- [ux-design-specification.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/ux-design-specification.md) — DossierIntegritySummary, ReviewExceptionList, step-first principle, traffic-light severity model
- [architecture-decisions.md](/home/axel/DLE-SaaS/docs/decisions/architecture-decisions.md) — frozen domain model (MMR, Batch, BatchStep), hybrid relational+JSONB strategy, backend-owned dossier composition, synchronous MVP export
- [Makefile](/home/axel/DLE-SaaS/Makefile) — `make check` and component commands
- [pyproject.toml](/home/axel/DLE-SaaS/pyproject.toml) — Django 5.2, DRF 3.16+, drf-spectacular 0.29+, PostgreSQL 17
- [backend/apps/audit/models.py](/home/axel/DLE-SaaS/backend/apps/audit/models.py) — AuditEvent model pattern (PROTECT FK, auto_now_add, JSONB metadata, ClassVar indexes)
- [backend/apps/audit/admin.py](/home/axel/DLE-SaaS/backend/apps/audit/admin.py) — read-only admin pattern for governed records
- [backend/apps/authz/api/views.py](/home/axel/DLE-SaaS/backend/apps/authz/api/views.py) — APIView pattern with CSRF, throttling, extend_schema
- [backend/apps/authz/domain/workstation.py](/home/axel/DLE-SaaS/backend/apps/authz/domain/workstation.py) — domain service pattern (functions, typed args, audit integration)
- [backend/apps/authz/selectors/access_context.py](/home/axel/DLE-SaaS/backend/apps/authz/selectors/access_context.py) — dataclass-based read model pattern
- [backend/shared/permissions/site_roles.py](/home/axel/DLE-SaaS/backend/shared/permissions/site_roles.py) — SiteScopedRolePermission reusable permission
- [backend/shared/api/exceptions.py](/home/axel/DLE-SaaS/backend/shared/api/exceptions.py) — problem-details error handler
- [backend/apps/authz/tests/helpers.py](/home/axel/DLE-SaaS/backend/apps/authz/tests/helpers.py) — CSRF test helper pattern
- [1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md](/home/axel/DLE-SaaS/_bmad-output/implementation-artifacts/1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md) — latest story implementation patterns and review feedback

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Stale test_dle_saas DB required manual cleanup before first test run
- URL pattern ordering in shared/api/urls.py shifted positional indices — moved exports include to end to preserve existing test expectations

### Completion Notes List

- Created `exports` app with canonical structure (api/, domain/, selectors/, tests/)
- Created foundation stub apps `mmr` and `batches` with minimal models as FK targets (Epic 2 not yet implemented, per Dev Notes guidance)
- Implemented `DossierProfile`, `BatchDossierStructure`, `DossierElement` models with PROTECT FK, JSONB rules, ClassVar indexes, unique constraints
- Implemented `resolve_dossier_structure()` domain service with rule evaluation engine supporting: eq, neq, in, not_in, truthy, falsy operators; default-required elements; idempotency; force-regenerate with audit preservation
- Implemented frozen dataclass read models in selectors: `DossierStructureReadModel`, `DossierElementReadModel`, `DossierCompletenessItem`
- Exposed `GET /api/v1/batches/{batch_id}/dossier-structure/` and `POST /api/v1/batches/{batch_id}/resolve-dossier/` endpoints with CSRF protection, extend_schema, and IsAuthenticated permission
- Admin: DossierProfile editable, BatchDossierStructure + DossierElement read-only (append-only governed records)
- 32 new tests: 13 domain (composition), 10 API (GET/POST/auth/CSRF/422), 9 model (FK PROTECT, ordering, uniqueness, admin permissions)
- All 100 tests pass (68 existing + 32 new), zero regressions
- All quality gates pass: lint, typecheck, security (bandit, pip-audit), architecture boundary check

### Change Log

- 2026-03-13: Story 6.1 implementation complete — dossier composition service, models, API, admin, and comprehensive tests

### File List

New files:
- backend/apps/exports/__init__.py
- backend/apps/exports/apps.py
- backend/apps/exports/models.py
- backend/apps/exports/admin.py
- backend/apps/exports/migrations/__init__.py
- backend/apps/exports/migrations/0001_initial.py
- backend/apps/exports/migrations/0002_batchdossierstructure_exports_bds_one_active_per_batch.py
- backend/apps/exports/domain/__init__.py
- backend/apps/exports/domain/composition.py
- backend/apps/exports/selectors/__init__.py
- backend/apps/exports/selectors/dossier_structure.py
- backend/apps/exports/api/__init__.py
- backend/apps/exports/api/serializers.py
- backend/apps/exports/api/views.py
- backend/apps/exports/api/urls.py
- backend/apps/exports/tests/__init__.py
- backend/apps/exports/tests/test_composition.py
- backend/apps/exports/tests/test_api.py
- backend/apps/exports/tests/test_models.py
- backend/apps/mmr/__init__.py
- backend/apps/mmr/apps.py
- backend/apps/mmr/models.py
- backend/apps/mmr/admin.py
- backend/apps/mmr/migrations/__init__.py
- backend/apps/mmr/migrations/0001_initial.py
- backend/apps/mmr/domain/__init__.py
- backend/apps/mmr/selectors/__init__.py
- backend/apps/mmr/api/__init__.py
- backend/apps/mmr/tests/__init__.py
- backend/apps/batches/__init__.py
- backend/apps/batches/apps.py
- backend/apps/batches/models.py
- backend/apps/batches/admin.py
- backend/apps/batches/migrations/__init__.py
- backend/apps/batches/migrations/0001_initial.py
- backend/apps/batches/migrations/0002_initial.py
- backend/apps/batches/domain/__init__.py
- backend/apps/batches/selectors/__init__.py
- backend/apps/batches/api/__init__.py
- backend/apps/batches/tests/__init__.py

New files (review fix migrations):
- backend/apps/audit/migrations/0004_alter_auditevent_event_type.py
- backend/apps/exports/migrations/0002_batchdossierstructure_exports_bds_one_active_per_batch.py

Modified files:
- backend/config/settings/base.py (added MmrConfig, BatchesConfig, ExportsConfig to INSTALLED_APPS)
- backend/shared/api/urls.py (wired exports API URLs)
- backend/shared/api/exceptions.py (added UnprocessableEntity)
- backend/apps/audit/models.py (added DOSSIER_RESOLVED)
- backend/apps/exports/models.py (added UniqueConstraint on BatchDossierStructure)
- backend/apps/exports/domain/composition.py (audit event, race condition handling, not_in bug fix, actor/site params)
- backend/apps/exports/api/views.py (SiteScopedRolePermission, get_site(), problem-details 422)
- backend/apps/exports/api/serializers.py (removed dead DossierCompletenessItemSerializer)
- backend/apps/exports/tests/test_api.py (SiteRoleAssignment fixtures, role denial tests, 422 format update)
- backend/apps/exports/tests/test_composition.py (not_in bug test, audit event tests)
- _bmad-output/implementation-artifacts/sprint-status.yaml (story status update)
