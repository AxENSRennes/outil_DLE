# Story 6.2: Generate Repeated In-Process and Box-Level Controls for the Batch

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a production or quality user,
I want repeated dossier controls to be generated as structured batch records rather than static placeholders,
so that recurring checks can be executed and reviewed as real governed records within the batch.

## Acceptance Criteria

1. Given the batch dossier structure includes controls that repeat by process, box, or other governed context, when the batch structure is generated or refreshed for operational use, then the system creates repeated control records as structured batch elements, and those controls are not represented only as a single static form instance.
2. Given repeated controls may depend on the resolved dossier context, when the system determines how many repeated records are needed, then it uses governed batch rules and context inputs to create the correct repeated set, and later execution and review flows can address each repeated control individually.
3. Given review and completeness logic must account for repeated records explicitly, when repeated controls exist in the batch, then they contribute to completeness and review expectations as distinct governed elements, and the platform can identify which repeated item is complete, incomplete, or reviewed.
4. Given this story is about repeated control modeling rather than calculations or export, when it is completed, then the batch dossier supports repeated structured control instances as a standalone capability, and calculation validation, external references, and dossier export remain outside the scope of this story.
5. Given execution and review features will rely on stable repeated-control semantics, when this story is reviewed, then the generated control instances are backed by canonical batch data structures, and later UI stories do not need to simulate repetition with frontend-only constructs.

## Tasks / Subtasks

- [x] Create the `batches` Django app with core domain models for Batch, BatchStep, and BatchDocumentRequirement (AC: 1, 4, 5)
  - [x] Create `backend/apps/batches/` app structure following the architecture layout: `api/`, `domain/`, `selectors/`, `tests/`, `models.py`, `admin.py`, `apps.py`.
  - [x] Implement the `Batch` model from the reference design in `django_models_v1.py` with FK to `sites.Site` and `authz.User`. Defer `Product` and `MMRVersion` FKs — use a JSONB `snapshot_json` field to carry the frozen template snapshot and a `batch_context_json` field for contextual attributes (line, machine, format_family, glitter_mode).
  - [x] Implement `BatchStep` model with `step_key`, `occurrence_key` (default `"default"`), `occurrence_index`, `title`, `sequence_order`, `source_document_code`, `is_applicable`, `applicability_basis_json`, `status`, `review_state`, `signature_state`, blocking flags (`blocks_execution_progress`, `blocks_step_completion`, `blocks_signature`, `blocks_pre_qa_handoff`), `data_json`, `meta_json`, and timestamps. Enforce `UniqueConstraint` on `(batch, step_key, occurrence_key)`.
  - [x] Implement `BatchDocumentRequirement` model with `document_code`, `title`, `source_step_key`, `is_required`, `is_applicable`, `repeat_mode` (using `BatchDocumentRepeatMode` choices: single, per_shift, per_team, per_box, per_event), `expected_count`, `actual_count`, `status` (expected, present, missing), `applicability_basis_json`, and `meta_json`. Enforce `UniqueConstraint` on `(batch, document_code)`.
  - [x] Implement all status/state enums: `BatchStatus`, `BatchStepStatus`, `StepReviewState`, `StepSignatureState`, `ReviewState`, `SignatureState`, `BatchDocumentStatus`, `BatchDocumentRepeatMode`.
  - [x] Create additive migrations. Register the app in `INSTALLED_APPS`.

- [x]Implement the repeated-control generation service in `batches/domain/` (AC: 1, 2, 5)
  - [x]Create `backend/apps/batches/domain/composition.py` with a `generate_repeated_controls` function (or service class) that takes a `Batch` instance and its frozen template snapshot.
  - [x]For each step in the template `stepOrder`, read the step's `repeatPolicy.mode`:
    - `single` -> create exactly 1 `BatchStep` with `occurrence_key="default"`, `occurrence_index=1`.
    - `per_shift` / `per_team` / `per_box` / `per_event` -> create the initial set of `BatchStep` records based on `repeatPolicy.minRecords` (defaulting to 1 if absent). For open-ended repeat modes (no `maxRecords` or `maxRecords > minRecords`), create only `minRecords` initially; additional occurrences are added later via an `add_occurrence` action.
  - [x]Each generated `BatchStep` must carry: `step_key` from the template step key, `occurrence_key` formed as `"{step_key}_{mode}_{index}"` (e.g., `"finished_product_control_per_box_1"`), `occurrence_index` as a 1-based integer, `title` from the template, `sequence_order` computed from the step's position in `stepOrder` plus occurrence offset, `source_document_code` from the step key, blocking flags from `blockingPolicy`, signature state from `signaturePolicy`, and field schema stored in `meta_json`.
  - [x]Apply applicability rules: if the step has an `applicability` filter, evaluate it against `batch_context_json`. Set `is_applicable=False` and record the evaluation basis in `applicability_basis_json` when the batch context does not match. Non-applicable steps with `whenNotApplicable="mark_na"` are created with `is_applicable=False`; steps with `whenNotApplicable="hidden"` are skipped entirely (not created as `BatchStep` records).
  - [x]Create a corresponding `BatchDocumentRequirement` for each step, with `repeat_mode` matching the template `repeatPolicy.mode`, `expected_count` set to the number of `BatchStep` records actually generated, and `is_applicable` matching the applicability evaluation.

- [x]Implement an `add_occurrence` domain action for open-ended repeat modes (AC: 1, 2)
  - [x]Create `backend/apps/batches/domain/occurrences.py` with an `add_occurrence(batch, step_key)` function.
  - [x]Validate that the step's `repeatPolicy.mode` is not `single` and that adding another occurrence does not exceed `maxRecords` (if defined).
  - [x]Generate the next `BatchStep` with `occurrence_index = max(existing) + 1` and `occurrence_key` following the same naming pattern.
  - [x]Update the corresponding `BatchDocumentRequirement.expected_count` and `actual_count`.
  - [x]Raise a domain error if the repeat policy does not allow more occurrences.

- [x]Implement completeness selectors for repeated controls (AC: 3)
  - [x]Create `backend/apps/batches/selectors/completeness.py` with queries that:
    - Count total vs. completed vs. incomplete `BatchStep` records per `step_key` group, including only `is_applicable=True` steps.
    - Return per-document-requirement completeness: `expected_count` vs. `actual_count` (steps with `status >= completed`).
    - Identify which individual repeated occurrence is complete, incomplete, signed, or reviewed.
  - [x]These selectors power the `ChecklistCompleteness` and `DossierIntegritySummary` read models referenced by the architecture.

- [x]Expose minimal API endpoints for batch composition and occurrence management (AC: 1, 2, 3, 5)
  - [x]Create `POST /api/v1/batches/{id}/compose` action endpoint that triggers the composition service (generates all steps including repeated controls from the frozen template snapshot). This endpoint is idempotent: re-composition replaces `not_started` steps only, preserving any in-progress or completed data.
  - [x]Create `POST /api/v1/batches/{batch_id}/steps/{step_key}/occurrences` action endpoint that calls `add_occurrence` for open-ended repeat modes.
  - [x]Create `GET /api/v1/batches/{id}/steps` read endpoint returning all `BatchStep` records grouped by `step_key` with occurrence detail, applicability, and status.
  - [x]Create `GET /api/v1/batches/{id}/document-requirements` read endpoint returning all `BatchDocumentRequirement` records with completeness counts.
  - [x]Follow existing API patterns: DRF serializers, problem-details errors, snake_case JSON, drf-spectacular schema annotations.

- [x]Implement Django admin for batch models with audit-safe configuration (AC: 5)
  - [x]Register `Batch`, `BatchStep`, and `BatchDocumentRequirement` in admin.
  - [x]Mark `snapshot_json`, `data_json`, `meta_json`, `applicability_basis_json` as `readonly_fields` in admin forms.
  - [x]Use `list_display` with key fields and status for quick inspection.

- [x]Write comprehensive backend tests (AC: 1, 2, 3, 4, 5)
  - [x]Test `generate_repeated_controls` with the pilot template example: verify correct `BatchStep` count for single, per_team, per_box, per_event modes.
  - [x]Test applicability evaluation: verify `gencod_control_uni2_uni3` is `is_applicable=False` when machine is not UNI2/UNI3; verify `intermediate_leakage_pms_glitter` is `is_applicable=False` when machine is not PMS or glitter_mode is not `with_glitter`.
  - [x]Test `whenNotApplicable="hidden"` steps are not created vs. `"mark_na"` steps are created with `is_applicable=False`.
  - [x]Test `add_occurrence` succeeds for per_box mode and respects `maxRecords` limit for per_event mode (e.g., gencod control capped at 3).
  - [x]Test `add_occurrence` raises domain error for single-mode steps.
  - [x]Test completeness selectors return correct counts for mixed complete/incomplete occurrences.
  - [x]Test `BatchDocumentRequirement` expected_count matches generated step count and updates on `add_occurrence`.
  - [x]Test `compose` endpoint idempotency: re-composing does not destroy in-progress step data.
  - [x]Test API serialization: verify JSON output shape matches architecture read model contracts.
  - [x]Test model constraints: unique constraint on `(batch, step_key, occurrence_key)` prevents duplicates.
  - [x]Run `make check` before closing the story.

## Dev Notes

### Story Intent

This story introduces the backend capability for generating repeated control records within a batch dossier. In the real dossier de lot workflow, many controls are not single occurrences: finished product controls repeat per box, packaging execution repeats per team/shift, and in-process controls like gencod checks repeat per event (start/middle/end). Today on paper, operators have pre-printed repeated forms. In the digital system, these must be modeled as individual, addressable, governable batch step records.

This is a pure backend/data-modeling story. It creates the domain models, composition service, and API surface that later execution UI stories (Epic 3) and review stories (Epic 5) will consume. The frontend does not own repetition logic — it receives the composed structure from the backend.

### Story Foundation

- Epic 6 exists to provide the dossier composition, calculation, reference, and export capabilities.
- Story 6.1 (Compose the Required Dossier Structure from Batch Context) resolves which sub-documents are required based on batch context. Story 6.2 extends this by generating the actual repeated `BatchStep` records for those requirements.
- Story 6.2 is scoped to repeated control generation only. Governed calculations (6.3), structured references (6.4), and dossier export (6.5) remain out of scope.
- The `batches` app does not exist yet in the codebase. This story creates it with the core models needed for batch execution.
- The `mmr` app (template governance) is not yet implemented. This story works with a frozen template snapshot stored in `Batch.snapshot_json` rather than requiring a live `MMRVersion` FK. The FK can be added when the `mmr` app is implemented in Epic 2.
- The existing reference design in `django_models_v1.py` and the MMR version schema in `mmr-version-schema-minimal.json` / `mmr-version-example.json` define the data contracts this story must implement.

### Technical Requirements

- Use `/home/axel/wsl_venv/bin/python` for Django management commands, tests, and package operations.
- PostgreSQL 17.x is the database. Use standard Django model fields; JSONB is used for `snapshot_json`, `batch_context_json`, `data_json`, `meta_json`, and `applicability_basis_json`.
- The `Batch.snapshot_json` field stores a frozen copy of the MMR version schema at instantiation time. The composition service reads step definitions, repeat policies, applicability rules, and blocking policies from this snapshot.
- The `Batch.batch_context_json` field stores operational attributes like `{"line_code": "PMS", "machine_code": "PMS", "format_family": "100mL", "glitter_mode": "with_glitter"}`. The composition service evaluates applicability rules against this context.
- The repeat modes map directly from the MMR schema `repeatPolicy.mode` to `BatchDocumentRepeatMode` choices:
  - `single` -> exactly one record, `occurrence_key="default"`.
  - `per_shift`, `per_team`, `per_box`, `per_event` -> N records, `occurrence_key="{step_key}_{mode}_{index}"`.
- `minRecords` in the template defines the minimum initial set. `maxRecords` (if present) caps the total allowed. When `maxRecords` is absent, the step allows unlimited additional occurrences.
- The composition service must be deterministic: given the same snapshot and context, it produces the same set of BatchStep records.
- All regulated workflow state changes must go through explicit domain actions, not direct ORM mutations from views.
- Defer `Product` and `MMRVersion` FK relationships until Epic 2 ships those models. Use `snapshot_json` as the source of truth for now.

### Architecture Compliance

- Create `backend/apps/batches/` with `api/`, `domain/`, `selectors/`, `tests/`, `models.py`, `admin.py`, `apps.py` per the architecture project structure. [Source: architecture.md lines 605-610]
- Business logic lives in `domain/`. Composition service in `domain/composition.py`, occurrence management in `domain/occurrences.py`. [Source: architecture.md lines 735-739]
- Optimized reads live in `selectors/`. Completeness queries in `selectors/completeness.py`. [Source: architecture.md line 738]
- API endpoints live in `api/`. Serializers, views, URL routing, and drf-spectacular schema. [Source: architecture.md line 737]
- Domain code must not depend on API packages. API code can call domain services and selectors. [Source: architecture.md line 737]
- The composition service implements the "generating repeated in-process and box-level control records" responsibility of the backend dossier-composition service. [Source: architecture.md lines 362-369]
- Use the hybrid relational + JSONB modeling strategy: relational for `Batch`, `BatchStep`, `BatchDocumentRequirement`; JSONB for template snapshots, field schemas, conditional rules, and step payloads. [Source: architecture.md lines 149-152]
- Follow REST-first API under `/api/v1/` with problem-details errors and stable machine-readable codes. [Source: architecture.md lines 318-319]
- Direct arbitrary PATCH semantics on batch status or step state are forbidden. Use explicit action endpoints. [Source: architecture.md lines 301-314]

### Library / Framework Requirements

- Django 5.2 LTS (already pinned in `pyproject.toml`). Do not upgrade the framework.
- Django REST Framework 3.16 with `SessionAuthentication`.
- drf-spectacular for OpenAPI schema generation. Annotate all new endpoints.
- No new library dependencies should be needed for this story. The composition logic is pure Python operating on Django models and JSON data.

### File Structure Requirements

- New app to create:
  - `backend/apps/batches/__init__.py`
  - `backend/apps/batches/apps.py`
  - `backend/apps/batches/models.py` — Batch, BatchStep, BatchDocumentRequirement, all enums
  - `backend/apps/batches/admin.py` — Admin registration with readonly JSONB fields
  - `backend/apps/batches/migrations/__init__.py`
  - `backend/apps/batches/migrations/0001_initial.py` — Additive migration
  - `backend/apps/batches/domain/__init__.py`
  - `backend/apps/batches/domain/composition.py` — `generate_repeated_controls` service
  - `backend/apps/batches/domain/occurrences.py` — `add_occurrence` action
  - `backend/apps/batches/selectors/__init__.py`
  - `backend/apps/batches/selectors/completeness.py` — Completeness queries
  - `backend/apps/batches/api/__init__.py`
  - `backend/apps/batches/api/serializers.py` — DRF serializers for Batch, BatchStep, BatchDocumentRequirement
  - `backend/apps/batches/api/views.py` — Compose, add-occurrence, list endpoints
  - `backend/apps/batches/api/urls.py` — URL routing
  - `backend/apps/batches/tests/__init__.py`
  - `backend/apps/batches/tests/test_models.py` — Model constraint tests
  - `backend/apps/batches/tests/test_composition.py` — Composition service tests
  - `backend/apps/batches/tests/test_occurrences.py` — Add-occurrence tests
  - `backend/apps/batches/tests/test_completeness.py` — Completeness selector tests
  - `backend/apps/batches/tests/test_api.py` — API endpoint tests
- Existing files to modify:
  - `backend/config/settings/base.py` — Add `"apps.batches"` to `INSTALLED_APPS`
  - `backend/shared/api/urls.py` or `backend/config/urls.py` — Wire `batches` API URLs

### Testing Requirements

- Composition service tests:
  - Generate steps from the pilot template (`mmr-version-example.json`): verify 9 step definitions produce the correct number of `BatchStep` records (single steps = 1 each; per_team = 1 initial; per_box = 1 initial; per_event with minRecords=3 = 3 records).
  - Applicability: for context `{"machine_code": "PMS", "glitter_mode": "with_glitter"}`, `gencod_control_uni2_uni3` is not applicable (mark_na), `intermediate_leakage_pms_glitter` is applicable.
  - Applicability: for context `{"machine_code": "UNI2"}`, `gencod_control_uni2_uni3` is applicable, `intermediate_leakage_pms_glitter` is not applicable (mark_na).
  - Verify `occurrence_key` uniqueness within each batch.
  - Verify `sequence_order` respects `stepOrder` from the template.
  - Verify `BatchDocumentRequirement` records are created with correct `repeat_mode` and `expected_count`.
- Add-occurrence tests:
  - Adding a box occurrence to `finished_product_control` succeeds and increments `occurrence_index`.
  - Adding beyond `maxRecords` for `gencod_control_uni2_uni3` (max 3) raises domain error.
  - Adding occurrence to a `single`-mode step raises domain error.
  - `BatchDocumentRequirement.expected_count` and `actual_count` update correctly.
- Completeness selector tests:
  - Mixed states: 3 of 5 box controls completed returns correct counts.
  - Non-applicable steps excluded from completeness calculations.
  - Per-document completeness aggregation matches expectations.
- API tests:
  - `POST /api/v1/batches/{id}/compose` returns composed structure with all steps.
  - `POST /api/v1/batches/{id}/steps/{step_key}/occurrences` adds occurrence and returns updated step list.
  - `GET /api/v1/batches/{id}/steps` returns grouped step structure with occurrence detail.
  - `GET /api/v1/batches/{id}/document-requirements` returns completeness data.
  - Compose is idempotent: second call does not duplicate or destroy existing steps.
- Model constraint tests:
  - Unique constraint on `(batch, step_key, occurrence_key)` rejects duplicates.
  - Unique constraint on `(batch, document_code)` rejects duplicate document requirements.
- Regression tests:
  - Existing auth/audit endpoints still work after adding the batches app.
- Quality commands:
  - `make lint`
  - `make typecheck`
  - `make test`
  - `make check`

### Reference Data: Pilot Template Repeat Modes

The pilot template (`mmr-version-example.json`) defines these repeat patterns that the composition service must handle:

| Step Key | Kind | Repeat Mode | minRecords | maxRecords | Applicability |
|---|---|---|---|---|---|
| `fabrication_bulk` | manufacturing | single | 1 | 1 | Always |
| `weighing` | weighing | single | 1 | 1 | Always |
| `line_cleaning_previous_run` | preparation | single | 1 | 1 | Always |
| `packaging_execution` | packaging | per_team | 1 | - | Always |
| `finished_product_control` | finished_product_control | per_box | 1 | - | Always |
| `gencod_control_uni2_uni3` | in_process_control | per_event | 3 | 3 | machineCodes: [UNI2, UNI3], mark_na |
| `intermediate_leakage_pms_glitter` | in_process_control | per_box | 1 | - | machineCodes: [PMS] + glitterMode: with_glitter, mark_na |
| `dossier_checklist_pre_qa` | review | single | 1 | 1 | Always |
| `pre_qa_review` | pre_qa_review | single | 1 | 1 | Always |

### Git Intelligence Summary

- Recent commits focus on Epic 1 Story 1.3 (workstation auth): security hardening, fail-closed patterns, FK PROTECT, CSRF enforcement, timing side-channel fixes, hashed PIN storage.
- Patterns to follow:
  - Use `on_delete=models.PROTECT` for FKs to `User` and `Site` (prevent accidental cascade deletion of regulated records).
  - Use `on_delete=models.CASCADE` for FKs within the batch hierarchy (`BatchStep` -> `Batch`, `BatchDocumentRequirement` -> `Batch`) since these are owned children.
  - Follow fail-closed patterns for domain actions: if audit or composition fails, the batch should not be left in an inconsistent state.
  - Keep endpoint behavior explicit and heavily tested with negative paths.
- The current backend has `authz`, `audit`, and `sites` apps. This story adds the `batches` app as the fourth domain app.

### Project Context Reference

No `project-context.md` file was present in the repository when this story was created.

Use these source artifacts instead:

- [epics.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/planning-artifacts/epics.md) — Epic 6 scope and Story 6.2 acceptance criteria
- [architecture.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/planning-artifacts/architecture.md) — Dossier composition service, data model, service boundaries, API contracts
- [prd.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/planning-artifacts/prd.md) — FR45, FR46, FR47, FR48, FR50, FR51
- [ux-design-specification.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/planning-artifacts/ux-design-specification.md) — Step-first execution pattern, review-by-exception dashboard
- [django_models_v1.py](/home/axel/DLE-SaaS-epic-6/_bmad-output/implementation-artifacts/django_models_v1.py) — Reference data model design
- [mmr-version-schema-minimal.json](/home/axel/DLE-SaaS-epic-6/_bmad-output/implementation-artifacts/mmr-version-schema-minimal.json) — MMR version JSON schema with repeatPolicy and applicability definitions
- [mmr-version-example.json](/home/axel/DLE-SaaS-epic-6/_bmad-output/implementation-artifacts/mmr-version-example.json) — Pilot template with concrete repeated controls (per_box, per_team, per_event)
- [Makefile](/home/axel/DLE-SaaS-epic-6/Makefile) — Canonical local verification commands
- [1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/implementation-artifacts/1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md) — Most recent completed story for code patterns and conventions

### Project Structure Notes

- The backend currently has three feature apps under `backend/apps/`: `authz`, `audit`, and `sites`.
- There is no `batches/`, `mmr/`, `signatures/`, `reviews/`, or `exports/` app yet. This story creates the first of those.
- The `batches` app will be the foundation for execution stories in Epic 3, review stories in Epic 5, and the rest of Epic 6.
- Since `mmr` does not exist yet, the `Batch` model cannot have a live FK to `MMRVersion`. Instead, store the full template snapshot in `snapshot_json`. When Epic 2 ships the `mmr` app, a later migration can add the FK.
- Since `Product` is not yet implemented (it is defined in `django_models_v1.py` but not yet as a Django app), defer the `Product` FK as well. The product context is available in `batch_context_json` and `snapshot_json`.
- The `backend/config/settings/base.py` INSTALLED_APPS list needs to include `"apps.batches"`.

### References

- [epics.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/planning-artifacts/epics.md) — Epic 6 Story 6.2 scope, acceptance criteria, and cross-story dependencies
- [architecture.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/planning-artifacts/architecture.md) — Dossier composition service (lines 362-369), data model (lines 144-159), service boundaries (lines 735-739), API contracts (lines 316-360), naming patterns (lines 433-457), project structure (lines 605-645)
- [prd.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/planning-artifacts/prd.md) — FR45 (conditional sub-documents), FR46 (repeated control records), FR47 (cross-document rules), FR48 (completeness against checklist), FR50 (blocking when controls incomplete), FR51 (mark N/A based on context)
- [ux-design-specification.md](/home/axel/DLE-SaaS-epic-6/_bmad-output/planning-artifacts/ux-design-specification.md) — Step-first execution principle, review-by-exception dashboard, changed-since-review states
- [django_models_v1.py](/home/axel/DLE-SaaS-epic-6/_bmad-output/implementation-artifacts/django_models_v1.py) — Reference model design for Batch, BatchStep, BatchDocumentRequirement, all enums
- [mmr-version-schema-minimal.json](/home/axel/DLE-SaaS-epic-6/_bmad-output/implementation-artifacts/mmr-version-schema-minimal.json) — JSON Schema with repeatPolicy, applicability, blockingPolicy, signaturePolicy definitions
- [mmr-version-example.json](/home/axel/DLE-SaaS-epic-6/_bmad-output/implementation-artifacts/mmr-version-example.json) — Pilot template with concrete repeat modes (per_box, per_team, per_event) and applicability filters
- [sprint-status.yaml](/home/axel/DLE-SaaS-epic-6/_bmad-output/implementation-artifacts/sprint-status.yaml) — Story tracking and status
- [backend/apps/authz/models.py](/home/axel/DLE-SaaS-epic-6/backend/apps/authz/models.py) — User model and SiteRole for FK references
- [backend/apps/sites/models.py](/home/axel/DLE-SaaS-epic-6/backend/apps/sites/models.py) — Site model for FK reference
- [backend/apps/audit/models.py](/home/axel/DLE-SaaS-epic-6/backend/apps/audit/models.py) — AuditEvent model pattern
- [backend/config/settings/base.py](/home/axel/DLE-SaaS-epic-6/backend/config/settings/base.py) — INSTALLED_APPS to extend

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Cleaned stale `__pycache__` files from previous branch migrations (audit app 0003-0009) that were corrupting test DB schema.
- Fixed brittle test in `backend/tests/test_health_api.py` that used hardcoded URL pattern indices instead of name lookup.

### Completion Notes List

- Created `batches` Django app with full architecture-compliant structure (api/, domain/, selectors/, tests/).
- Implemented `Batch`, `BatchStep`, `BatchDocumentRequirement` models with all enums (`BatchStatus`, `BatchStepStatus`, `StepReviewState`, `StepSignatureState`, `ReviewState`, `SignatureState`, `BatchDocumentStatus`, `BatchDocumentRepeatMode`).
- `Batch` model defers `Product`/`MMRVersion` FKs; uses `snapshot_json` for template and `batch_context_json` for operational context.
- `BatchStep` has `UniqueConstraint` on `(batch, step_key, occurrence_key)`.
- `BatchDocumentRequirement` has `UniqueConstraint` on `(batch, document_code)`.
- Composition service (`domain/composition.py`) generates repeated controls from frozen template snapshot with full applicability evaluation (machineCodes, glitterMode, lineCodes, formatFamilies, siteCodes) and `whenNotApplicable` handling (mark_na vs hidden).
- `add_occurrence` action (`domain/occurrences.py`) adds new occurrences for open-ended repeat modes with `maxRecords` validation.
- Completeness selectors (`selectors/completeness.py`) provide per-step_key group counts, per-document requirement completeness, and individual occurrence details.
- REST API endpoints: `POST /compose`, `POST /steps/{key}/occurrences`, `GET /steps`, `GET /document-requirements` with DRF serializers and drf-spectacular annotations.
- Django admin with `readonly_fields` for all JSONB fields.
- 68 tests covering: model constraints, composition service (PMS+glitter and UNI2 contexts), applicability evaluation, idempotency, add_occurrence (success/max/single-mode errors), completeness selectors, API endpoints (auth, CSRF, 404, response shapes).
- `make check` passes: lint, typecheck, 136 tests, security scan, architecture check.

### Change Log

- 2026-03-13: Initial implementation of story 6.2 — created batches app with repeated control generation capability.

### File List

**New files:**
- backend/apps/batches/__init__.py
- backend/apps/batches/apps.py
- backend/apps/batches/models.py
- backend/apps/batches/admin.py
- backend/apps/batches/migrations/__init__.py
- backend/apps/batches/migrations/0001_initial.py
- backend/apps/batches/domain/__init__.py
- backend/apps/batches/domain/composition.py
- backend/apps/batches/domain/occurrences.py
- backend/apps/batches/selectors/__init__.py
- backend/apps/batches/selectors/completeness.py
- backend/apps/batches/api/__init__.py
- backend/apps/batches/api/serializers.py
- backend/apps/batches/api/views.py
- backend/apps/batches/api/urls.py
- backend/apps/batches/tests/__init__.py
- backend/apps/batches/tests/conftest.py
- backend/apps/batches/tests/test_models.py
- backend/apps/batches/tests/test_composition.py
- backend/apps/batches/tests/test_occurrences.py
- backend/apps/batches/tests/test_completeness.py
- backend/apps/batches/tests/test_api.py

**Modified files:**
- backend/config/settings/base.py — Added `apps.batches.apps.BatchesConfig` to INSTALLED_APPS
- backend/shared/api/urls.py — Wired `batches/` API URLs
- backend/tests/test_health_api.py — Fixed brittle URL pattern index lookup to use name-based resolution
