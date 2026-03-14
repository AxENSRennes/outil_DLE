# Story 3.1: Open a Batch and Navigate Its Step-by-Step Execution Flow

Status: done

## Story

As an operator on a shared workstation,
I want to open the active batch and move through its ordered execution steps with clear status visibility,
So that I can immediately understand where the dossier stands and continue work without searching through the full record.

## Acceptance Criteria (BDD)

### AC1: Batch Access & Step Presentation

**Given** a governed batch has already been instantiated from a template snapshot
**When** an authorized operator accesses that batch
**Then** the system returns the batch execution view for that operator
**And** the ordered execution steps are presented from the batch snapshot rather than from the current live template definition.

### AC2: Execution Status Visibility

**Given** operators need immediate clarity on shared workstations
**When** the execution flow is displayed
**Then** each batch step shows a visible execution status
**And** the operator can identify the current step and overall progression without opening the entire dossier.

### AC3: Step Navigation & Context Loading

**Given** execution must follow the governed step sequence
**When** the operator navigates between available steps
**Then** the system allows navigation within the batch's defined execution structure
**And** the active step context is loaded consistently from the batch record.

### AC4: No Reviewer Gates Between Ordinary Steps (MVP Constraint)

**Given** the MVP should avoid introducing unnecessary reviewer gates during ordinary production flow
**When** the execution shell is implemented
**Then** the batch navigation model supports normal progression across ordinary steps without requiring pre-QA or quality approval between them
**And** later blocking rules can be applied only where specific required controls demand it.

### AC5: Story Scope Boundary

**Given** this story should remain focused on the base execution shell
**When** it is completed
**Then** operators can access a batch and navigate its step sequence with status visibility
**And** draft save behavior, completion gating, instructions access, and signature actions remain outside the scope of this story.

## Tasks / Subtasks

### Backend: Create `apps.batches` Django App

- [x] Task 1: Create app structure and models (AC: #1)
  - [x] 1.1: Create `backend/apps/batches/` app with standard structure (api/, domain/, selectors/, models.py, admin.py, tests/)
  - [x] 1.2: Implement `Batch` model using `django_models_v1.py` as reference blueprint (see Dev Notes > Model Reference)
  - [x] 1.3: Implement `BatchStep` model using blueprint reference
  - [x] 1.4: Implement status enums: `BatchStatus`, `BatchStepStatus` - align values with architecture canonical states (see Dev Notes > Status Alignment)
  - [x] 1.5: Register app in `INSTALLED_APPS` in `config/settings/base.py`
  - [x] 1.6: Create and run migrations
  - [x] 1.7: Configure Django admin with read-focused permissions (batch/step records should not be editable via admin in production)

### Backend: Batch Execution Read API

- [x] Task 2: Create batch execution endpoint (AC: #1, #2, #3)
  - [x] 2.1: Create `GET /api/v1/batches/{id}/execution/` endpoint returning full batch execution view
  - [x] 2.2: Create `BatchExecutionSerializer` with nested step list, batch header, operator context
  - [x] 2.3: Create `StepSummarySerializer` (id, sequence_order, title, status, step_key, is_applicable, signature_state)
  - [x] 2.4: Compute `current_step_id` server-side (first non-completed applicable step in sequence order)
  - [x] 2.5: Ensure steps are returned ordered by `sequence_order` from the batch record, NOT from live template

- [x] Task 3: Create step detail endpoint (AC: #3)
  - [x] 3.1: Create `GET /api/v1/batch-steps/{id}/` endpoint returning full step context
  - [x] 3.2: Create `BatchStepDetailSerializer` (step data, field definitions from step_definition snapshot, status, metadata)
  - [x] 3.3: Return step definition (fields, instructions, kind, signature policy) from the batch snapshot JSONB - do NOT re-query MMRVersion

- [x] Task 4: Wire URL routing and permissions (AC: #1)
  - [x] 4.1: Create `apps/batches/api/urls.py` with batch and batch-step routes
  - [x] 4.2: Include in `config/urls.py` under `/api/v1/batches/`
  - [x] 4.3: Apply site-scoped operator permission check (reuse `SiteScopedRolePermission`)
  - [x] 4.4: Apply `@csrf_protect` if any POST endpoints added
  - [x] 4.5: Add `@extend_schema` decorators for OpenAPI documentation

### Backend: Seed Data and Testing

- [x] Task 5: Create seed data for batch execution testing (AC: #1-#4)
  - [x] 5.1: Create management command `seed_batch_demo` that creates a realistic batch with steps from the MMR version example (`mmr-version-example.json`)
  - [x] 5.2: Ensure seed batch has mixed step statuses (some not_started, some in_progress, some completed) to test the navigation shell
  - [x] 5.3: Link batch to an existing site and create test operator users with appropriate roles

- [x] Task 6: Write comprehensive backend tests (AC: #1-#5)
  - [x] 6.1: Test authorized operator can access batch execution view
  - [x] 6.2: Test unauthorized user (wrong site, wrong role) receives 403
  - [x] 6.3: Test unauthenticated user receives 401
  - [x] 6.4: Test step ordering matches `sequence_order` from batch record
  - [x] 6.5: Test each step includes visible status in response
  - [x] 6.6: Test `current_step_id` points to first non-completed applicable step
  - [x] 6.7: Test step detail endpoint returns frozen step definition from snapshot
  - [x] 6.8: Test nonexistent batch returns 404
  - [x] 6.9: Test batch from different site is not accessible (site-scoping)

### Frontend: Execution Feature Module

- [x] Task 7: Create `features/execution/` module structure (AC: #2, #3)
  - [x] 7.1: Set up directory: `components/`, `api/`, `schemas/`, `pages/`, `tests/`
  - [x] 7.2: Create TanStack Query hooks: `useBatchExecution(batchId)`, `useStepDetail(stepId)`
  - [x] 7.3: Create Zod schemas for API response validation
  - [x] 7.4: Create TypeScript types for `BatchExecution`, `StepSummary`, `StepDetail`, `StepStatus`

- [x] Task 8: Implement StepSidebar component (AC: #2)
  - [x] 8.1: Create persistent left sidebar (240px fixed width) showing all batch steps
  - [x] 8.2: Batch context header block: lot number, product name, batch status
  - [x] 8.3: Scrollable step list with StepStatusBadge for each step
  - [x] 8.4: Implement StepStatusBadge with redundant coding (color + icon + text) - see UX Status Table below
  - [x] 8.5: Active step highlighting: blue left border (#1971C2) + semibold text
  - [x] 8.6: Click handler to navigate between steps
  - [x] 8.7: Keyboard navigation: Arrow Up/Down to move focus, Enter to select, `aria-current="step"` on active
  - [x] 8.8: Responsive collapse to icon-only (56px) on viewport < 1280px, expand on hover/click

- [x] Task 9: Implement BatchExecutionShell layout (AC: #1, #2, #3)
  - [x] 9.1: Create app shell with CSS Grid: sidebar (240px fixed) + main content (centered, max-width 720px) + header (56px fixed)
  - [x] 9.2: Integrate IdentityBanner at top (reuse from Story 1.3 frontend if exists, or create with current operator display + Switch/Lock buttons)
  - [x] 9.3: Create StepExecutor area displaying active step title + step kind + field definitions (read-only for this story)
  - [x] 9.4: Auto-position on `current_step_id` (first non-completed step) on initial batch load
  - [x] 9.5: Wire React Router route: `/batches/:batchId/execution`

- [x] Task 10: Write frontend tests (AC: #1-#5)
  - [x] 10.1: StepSidebar renders all steps with correct status badges
  - [x] 10.2: StepSidebar highlights active step correctly
  - [x] 10.3: Keyboard navigation works (Arrow keys, Enter)
  - [x] 10.4: BatchExecutionShell renders batch header and step content
  - [x] 10.5: Auto-positions on current step on load
  - [x] 10.6: Accessibility tests with axe-core (contrast, ARIA, keyboard)
  - [x] 10.7: Responsive sidebar collapse at 1280px breakpoint

## Dev Notes

### Critical Architecture Constraints

1. **Batch Snapshot Immutability** - Steps MUST be loaded from the frozen `snapshot_json` / `step_definition` JSONB, NOT from the current live template. This is the core architectural invariant. A batch created from MMRVersion v3 must always show v3's steps, even if the template is now at v5.

2. **No Direct Status PATCH** - Direct arbitrary PATCH on batch status, step status, or any state field is FORBIDDEN per architecture. All transitions go through domain service actions (future stories 3.2-3.5).

3. **Site-Scoped Authorization** - Every batch endpoint MUST verify the requesting operator has a role on the batch's site. Use `SiteScopedRolePermission` from `shared/permissions/site_roles.py`.

4. **Fail-Closed Security** - Any security-critical operation MUST use try/finally patterns. Follow Story 1.3 established patterns.

5. **MVP Constraint: No Reviewer Gates** - Do NOT implement pre-QA or quality approval gates between ordinary execution steps. Navigation is free-flowing. Blocking rules come in Story 3.3.

6. **This Story is READ-ONLY** - This story creates the execution **shell** only. No data entry, no step completion, no signing, no draft saving. Those are Stories 3.2-3.5. The StepExecutor should display step field definitions but NOT render editable form inputs.

### Dependency: Epic 2 Models Not Yet Implemented

Epic 2 stories (MMR template governance, batch instantiation) are all in "backlog". This means:
- No `MMR`, `MMRVersion`, `Product`, or `Organization` models exist in the codebase yet
- The `Batch` model requires an `mmr_version` FK

**Recommended approach:** Create the `Batch` and `BatchStep` models in this story with `mmr_version_id` as a nullable FK (or IntegerField) for now. Use the seed command to create test data directly. When Epic 2 is implemented, the FK will be properly linked to the `MMRVersion` model.

Alternatively, create minimal stub models for `MMRVersion` (just id + `schema_json`) in the batches app to allow proper FK relationships. The developer should choose the approach that best fits the codebase state at implementation time.

### Model Reference: `django_models_v1.py`

A reference model blueprint exists at `_bmad-output/implementation-artifacts/django_models_v1.py`. Use it as a starting point but note these adjustments:

**`Batch` model key fields:**
- `site` (FK to Site, PROTECT) - for site-scoped access control
- `mmr_version` (FK - see dependency note above)
- `batch_number` (unique identifier, e.g., "LOT-2026-001")
- `status` (TextChoices enum - see status alignment below)
- `snapshot_json` (JSONField) - the FROZEN template definition at batch creation time
- `lot_size_target`, `lot_size_actual` (DecimalField, nullable)
- `created_by` (FK to User)
- `batch_context_json` (JSONField) - runtime context (line, machine, format, glitter mode)
- Timestamps: `created_at`, `started_at`, `completed_at`

**`BatchStep` model key fields:**
- `batch` (FK to Batch, CASCADE)
- `step_key` (CharField) - matches key in snapshot (e.g., "fabrication_bulk")
- `occurrence_key` (CharField) - for repeated steps (e.g., "team-A", "box-1")
- `occurrence_index` (PositiveIntegerField) - occurrence counter
- `title` (CharField) - human-readable step title
- `sequence_order` (PositiveIntegerField) - execution order
- `is_applicable` (BooleanField) - whether step applies to this batch context
- `status` (TextChoices enum)
- `data_json` (JSONField) - step execution payload (empty for this story)
- `meta_json` (JSONField) - step metadata
- Blocking policy fields: `blocks_execution_progress`, `blocks_step_completion`, `blocks_signature`, `blocks_pre_qa_handoff`
- Review/signature state fields for future stories
- Timestamps and attribution fields

### Status Alignment: Architecture vs Reference Models

The architecture document and `django_models_v1.py` use slightly different status values. **Align with the architecture document** as the authoritative source:

| Concept | Architecture (USE THIS) | django_models_v1.py |
|---|---|---|
| Batch active | `in_progress` | `in_execution` |
| Batch awaiting review | `awaiting_pre_qa` | `review_required` |
| Step not started | `not_started` | `not_started` |
| Step in progress | `in_progress` | `in_progress` |
| Step complete | `complete` | `completed` |
| Step signed | `signed` | `signed` |

**For this story, relevant statuses are limited to:**
- Batch: `in_progress` (the only status where operators execute)
- Steps: `not_started`, `in_progress`, `complete`, `signed` (display only, no transitions)

### MMR Version Snapshot Schema

The batch's `snapshot_json` follows the schema defined at `_bmad-output/implementation-artifacts/mmr-version-schema-minimal.json`. Key structures the developer must understand:

```json
{
  "schemaVersion": "v1",
  "templateCode": "...",
  "templateName": "...",
  "product": { "productCode": "...", "productName": "...", "family": "...", "formatLabel": "..." },
  "stepOrder": ["step_key_1", "step_key_2", ...],
  "steps": {
    "step_key_1": {
      "key": "...", "title": "...", "kind": "...", "instructions": "...",
      "fields": [{ "key": "...", "type": "text|number|decimal|select|...", "label": "...", "required": true }],
      "signaturePolicy": { "required": true, "meaning": "performed_by" },
      "blockingPolicy": { ... },
      "repeatPolicy": { "mode": "single|per_team|per_box|per_event", ... },
      "applicability": { "machineCodes": [...], "whenNotApplicable": "mark_na" }
    }
  }
}
```

A full realistic example is at `_bmad-output/implementation-artifacts/mmr-version-example.json` (9 steps, French cosmetics production dossier).

### API Contract

**GET /api/v1/batches/{id}/execution/**

```json
{
  "id": "uuid",
  "batch_number": "LOT-2026-001",
  "status": "in_progress",
  "product_name": "Parfum 100mL",
  "product_code": "CHR-PARF-100ML",
  "site": { "code": "CHR", "name": "Chateau-Renard" },
  "template_name": "Chateau-Renard - Parfum 100mL pilot",
  "template_code": "CHR-PARFUM-100ML-PILOT",
  "steps": [
    {
      "id": "uuid",
      "step_key": "fabrication_bulk",
      "sequence_order": 1,
      "title": "Dossier de fabrication bulk",
      "kind": "manufacturing",
      "status": "complete",
      "is_applicable": true,
      "signature_state": "signed",
      "requires_signature": true
    },
    {
      "id": "uuid",
      "step_key": "weighing",
      "sequence_order": 2,
      "title": "Fichier de pesee",
      "kind": "weighing",
      "status": "in_progress",
      "is_applicable": true,
      "signature_state": "required",
      "requires_signature": true
    }
  ],
  "current_step_id": "uuid-of-weighing-step",
  "progress": { "total": 9, "completed": 1, "applicable": 8 }
}
```

**GET /api/v1/batch-steps/{id}/**

```json
{
  "id": "uuid",
  "batch_id": "uuid",
  "step_key": "weighing",
  "sequence_order": 2,
  "title": "Fichier de pesee",
  "kind": "weighing",
  "status": "in_progress",
  "is_applicable": true,
  "instructions": "Renseigner la pesee et calculer les controles issus du fichier client.",
  "fields": [
    { "key": "density_from_bulk_record", "type": "decimal", "label": "Densite dossier de fabrication", "required": true },
    { "key": "format_code", "type": "select", "label": "Type de format", "required": true,
      "options": [{"value": "10mL", "label": "10mL"}, {"value": "100mL_ulli", "label": "100mL Ulli"}] },
    { "key": "gross_measurements", "type": "number_series", "label": "Serie de poids bruts", "required": true }
  ],
  "signature_policy": { "required": true, "meaning": "performed_by" },
  "blocking_policy": {
    "blocks_execution_progress": false,
    "blocks_step_completion": true,
    "blocks_signature": true,
    "blocks_pre_qa_handoff": true
  },
  "data": {},
  "meta": {}
}
```

### Frontend Component Architecture

```
frontend/src/features/execution/
├── components/
│   ├── BatchExecutionShell.tsx   # App shell: Grid layout (sidebar + main + header)
│   ├── StepSidebar.tsx           # Fixed left sidebar with step list
│   ├── StepSidebarItem.tsx       # Individual step row in sidebar
│   ├── StepStatusBadge.tsx       # Status indicator (color + icon + text)
│   ├── BatchHeader.tsx           # Batch context: lot, product, template, status
│   ├── StepExecutor.tsx          # Main content: active step details (read-only)
│   └── StepFieldList.tsx         # Read-only field definition display
├── api/
│   ├── queries.ts                # TanStack Query hooks (useBatchExecution, useStepDetail)
│   └── types.ts                  # API response TypeScript types
├── schemas/
│   └── execution.ts              # Zod schemas for API response validation
├── pages/
│   └── BatchExecutionPage.tsx    # React Router page component
└── tests/
    ├── StepSidebar.test.tsx
    ├── StepStatusBadge.test.tsx
    ├── BatchExecutionShell.test.tsx
    └── StepExecutor.test.tsx
```

### UX Status Badge Reference

| Step State | Color | Icon | Text | CSS |
|---|---|---|---|---|
| Not Started | Gray | Empty circle | "Not Started" | `text-gray-500` / `#868E96` |
| In Progress | Blue | Filled dot (pulsing) | "In Progress" | `text-blue-700` / `#1971C2` |
| Complete | Green | Checkmark | "Complete" | `text-green-700` / `#2B8A3E` |
| Signed | Green | Lock | "Signed" | `text-green-700` / `#2B8A3E` |
| N/A | Gray | Dash | "N/A" | `text-gray-400` / `#ADB5BD` |

All status indicators MUST use redundant coding: color + icon + text. Never convey status by color alone.

### Layout Specification

- **App Shell:** CSS Grid with `grid-template-columns: 240px 1fr` and `grid-template-rows: 56px 1fr`
- **Sidebar:** Fixed 240px, scrollable step list, batch header at top. Collapses to 56px icon-only below 1280px viewport.
- **Main content:** Centered, `max-width: 720px`, single-column layout
- **Header:** Fixed 56px IdentityBanner showing current operator, Switch User, Lock buttons
- **Active step highlight:** Blue left border (`border-left: 3px solid #1971C2`), semibold text
- **Spacing:** 16px between fields (md), 24px between sections (lg)
- **Interactive targets:** Minimum 44x44px click area on all interactive elements

### Accessibility Requirements (Non-Negotiable)

- `aria-current="step"` on the active step in sidebar
- `aria-live="polite"` on main content area for dynamic step changes
- Keyboard navigation: Arrow Up/Down through sidebar steps, Enter to select
- Focus management: auto-focus first element when step loads
- Skip link to main content on page load
- WCAG AA contrast: 4.5:1 for text, 3:1 for interactive elements
- Focus ring: 2px solid blue outline with 2px offset on all interactive elements
- All icon-only buttons must have `aria-label`
- Semantic HTML: `<nav>` for sidebar, `<main>` for step content, `<header>` for identity banner

### Existing Code to Reuse

**Backend (from Stories 1.1-1.3):**
- `shared/permissions/site_roles.py` → `SiteScopedRolePermission`, `get_active_site_by_code()`
- `shared/http.py` → `get_client_ip()` (for audit metadata)
- `shared/api/exceptions.py` → `problem_details_exception_handler`
- `apps/authz/domain/policies.py` → `user_has_site_role()`, `user_has_any_site_role()`, `get_authorized_sites()`
- `apps/authz/selectors/access_context.py` → `list_site_access_contexts()`
- `apps/audit/services.py` → `record_audit_event()` (for batch access auditing)
- Test helpers: `csrf_client()`, `post_json()` from `apps/authz/tests/helpers.py`

**Pattern references:**
- App structure: follow `apps/authz/` layout (api/, domain/, selectors/, tests/)
- Serializer pattern: request-shape serializers, nested response composition
- View pattern: `APIView` with explicit `permission_classes`, `@extend_schema`
- Admin pattern: follow `apps/audit/admin.py` for read-only admin classes

### Testing Patterns

Follow the established test conventions from Story 1.3:

```python
@pytest.mark.django_db
def test_authorized_operator_can_access_batch_execution():
    # Setup: site, user, role assignment, batch with steps
    site = Site.objects.create(code="CHR", name="Chateau-Renard", is_active=True)
    user = get_user_model().objects.create_user(username="op1", password="test")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR, is_active=True)
    batch = Batch.objects.create(site=site, batch_number="LOT-001", status="in_progress", ...)

    client, token = csrf_client(user=user)
    response = client.get(f"/api/v1/batches/{batch.id}/execution/")

    assert response.status_code == 200
    assert response.json()["batch_number"] == "LOT-001"
    assert len(response.json()["steps"]) == expected_step_count
```

Run `make check` after implementation to verify lint, typecheck, tests, security, and architecture constraints all pass.

### Previous Story Intelligence (Story 1.3)

**Patterns to replicate:**
1. Atomic audit + auth operations with explicit failure closure
2. Problem-details error responses with `code` and `type` fields
3. CSRF protection on all unsafe endpoints
4. OpenAPI docs with `@extend_schema` on every view
5. Comprehensive test coverage: success, failure, security, permissions, audit

**Pitfalls to avoid:**
1. Don't forget CSRF protection (was caught in Story 1.3 review)
2. Don't leak sensitive data in error responses
3. Audit batch access events for traceability
4. Site-scope ALL queries (no cross-site data leakage)
5. Use `PROTECT` on FKs to prevent cascade deletion of critical records

### Git Intelligence

Recent commits show iterative security hardening pattern:
- `a980fe1` - Harden audit event typing and lock throttling
- `c70f8d2` - Harden FK, admin delete, CSRF
- `600433f` - Protect FK integrity, add IP to success events
- `5f14659` - Extract shared client IP helper

**Lesson:** Design for security from the start. Story 1.3 required multiple hardening commits post-implementation. For Story 3.1:
- Add CSRF from day one on any POST endpoints
- Set up FK with PROTECT (not CASCADE) on critical relations
- Audit batch access from the start
- Lock down admin from the start

### Project Structure Notes

- New backend app: `backend/apps/batches/` following established domain app pattern
- New frontend feature: `frontend/src/features/execution/` following feature module pattern
- URL routing: add `batches/` path to `config/urls.py` API v1 router
- Settings: add `"apps.batches"` to `INSTALLED_APPS` in `config/settings/base.py`
- No conflicts with existing apps expected
- Architecture checker (`check_backend_architecture.py`) will validate app boundaries and import rules

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3] - Epic objectives, all story acceptance criteria, cross-story dependencies
- [Source: _bmad-output/planning-artifacts/architecture.md#Batch Execution] - API contracts, canonical lifecycle states, step state machine
- [Source: _bmad-output/planning-artifacts/architecture.md#Security] - Shared workstation auth model, session management, RBAC
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend] - React/TypeScript stack, TanStack Query, component organization
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Operator Execution] - StepSidebar, StepExecutor, IdentityBanner, layout specs
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Accessibility] - WCAG AA, keyboard-first, redundant coding
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Status Badges] - Color/icon/text status badge specification
- [Source: _bmad-output/implementation-artifacts/django_models_v1.py] - Reference model blueprint (Batch, BatchStep, enums)
- [Source: _bmad-output/implementation-artifacts/mmr-version-schema-minimal.json] - MMR snapshot JSON schema
- [Source: _bmad-output/implementation-artifacts/mmr-version-example.json] - Realistic 9-step French cosmetics production template
- [Source: _bmad-output/implementation-artifacts/1-3-*.md] - Previous story patterns, test approaches, security learnings
- [Source: docs/implementation/workstation-auth.md] - Workstation auth API contracts and audit taxonomy
- [Source: docs/implementation/authorization-policy.md] - Site-scoped RBAC enforcement

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Session required context compaction and continuation due to large scope

### Completion Notes List

- Backend `apps.batches` app created with Batch and BatchStep models aligned to architecture document statuses
- mmr_version_id implemented as PositiveIntegerField (nullable) since Epic 2 models don't exist yet
- Batch execution read API (GET /api/v1/batches/{id}/execution/) with server-computed current_step_id, progress summary, and step definitions from frozen snapshot_json
- Step detail API (GET /api/v1/batches/steps/{id}/) returning fields, instructions, signature_policy, blocking_policy from batch snapshot JSONB
- Site-scoped authorization via SiteScopedRolePermission with object-level site resolution
- Django admin configured read-only for batch/step records
- seed_batch_demo management command creates realistic 9-step batch from mmr-version-example.json
- 18 backend tests covering AC1-AC3, security (403/404), and edge cases - all passing
- Frontend execution feature module with shadcn/ui components (Badge, Sidebar, Card, ScrollArea, Separator, Skeleton)
- TanStack Query hooks with Zod v4 schema validation
- StepSidebar with keyboard navigation (Arrow Up/Down/Enter), aria-current="step"
- BatchExecutionShell with auto-positioning on current_step_id
- 16 frontend tests (StepStatusBadge, StepSidebar, BatchExecutionShell) - all passing
- `make check` passes: ruff, ESLint, mypy, tsc, pytest (86), vitest (16), bandit, pip-audit, architecture-check, react-doctor

### File List

**Backend (new):**
- backend/apps/batches/__init__.py
- backend/apps/batches/apps.py
- backend/apps/batches/models.py
- backend/apps/batches/admin.py
- backend/apps/batches/selectors/execution.py
- backend/apps/batches/api/serializers.py
- backend/apps/batches/api/views.py
- backend/apps/batches/api/urls.py
- backend/apps/batches/management/commands/seed_batch_demo.py
- backend/apps/batches/tests/__init__.py
- backend/apps/batches/tests/test_api.py

**Backend (modified):**
- backend/config/settings/base.py (added apps.batches to INSTALLED_APPS)
- backend/shared/api/urls.py (added batches URL include)

**Frontend (new):**
- frontend/src/features/execution/api/types.ts
- frontend/src/features/execution/api/queries.ts
- frontend/src/features/execution/schemas/execution.ts
- frontend/src/features/execution/components/StepStatusBadge.tsx
- frontend/src/features/execution/components/StepSidebarItem.tsx
- frontend/src/features/execution/components/StepSidebar.tsx
- frontend/src/features/execution/components/BatchHeader.tsx
- frontend/src/features/execution/components/StepFieldList.tsx
- frontend/src/features/execution/components/StepExecutor.tsx
- frontend/src/features/execution/components/BatchExecutionShell.tsx
- frontend/src/features/execution/pages/BatchExecutionPage.tsx
- frontend/src/features/execution/tests/StepStatusBadge.test.tsx
- frontend/src/features/execution/tests/StepSidebar.test.tsx
- frontend/src/features/execution/tests/BatchExecutionShell.test.tsx

**Frontend (modified):**
- frontend/src/app/router.tsx (added batches/:batchId/execution route)
- frontend/src/shared/ui/sidebar.tsx (fixed import path)
- frontend/src/shared/lib/index.ts (created barrel export for cn)
- frontend/src/shared/lib/utils.ts (created re-export for cn)
- frontend/src/test/setup.ts (added matchMedia, scrollIntoView, ResizeObserver stubs)
