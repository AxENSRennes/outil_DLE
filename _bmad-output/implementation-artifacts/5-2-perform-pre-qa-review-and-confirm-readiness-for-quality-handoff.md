# Story 5.2: Perform Pre-QA Review and Confirm Readiness for Quality Handoff

Status: review

## Story

As a production supervisor or pre-QA reviewer,
I want a dedicated pre-QA review action over the dossier summary and exceptions,
So that I can confirm readiness for quality handoff or stop the dossier before it reaches quality with obvious issues.

## Acceptance Criteria

1. **Given** a batch has reached the point where production wants to hand it off, **When** a pre-QA reviewer opens the dedicated review surface, **Then** they can assess dossier completeness from a review-oriented interface, **And** they are not forced through the operator execution workflow to perform review.

2. **Given** the pre-QA reviewer needs to catch obvious dossier defects early, **When** the reviewer inspects the batch summary and exceptions, **Then** they can identify missing data, missing signatures, changed records, and other visible review-relevant issues, **And** they can use that information before confirming handoff readiness.

3. **Given** pre-QA is a distinct workflow state from execution and quality review, **When** the reviewer confirms the dossier as ready, **Then** the system records a pre-QA review action and moves the batch into the appropriate pre-QA-confirmed handoff state, **And** that state is distinguishable from both ordinary execution and quality review states.

4. **Given** a dossier may still require correction before quality receives it, **When** the reviewer determines the dossier is not ready, **Then** the system does not confirm quality handoff readiness, **And** later correction or return workflows remain possible without pretending the dossier passed pre-QA.

5. **Given** this story is focused on pre-QA confirmation rather than full quality disposition, **When** it is completed, **Then** production review can confirm or withhold readiness for quality handoff as a standalone capability, **And** quality decision-making, rejection, release, and final disposition remain outside the scope of this story.

## Tasks / Subtasks

- [x] **Task 1: Add ReviewEvent model to reviews app** (AC: 3)
  - [x] 1.1 Create `ReviewEvent` model in `backend/apps/reviews/models.py` with fields: `batch` (FK), `reviewer` (FK to User), `event_type` (CharField with choices), `step` (FK to BatchStep, nullable), `note` (TextField, blank), `occurred_at` (DateTimeField, auto_now_add), `metadata` (JSONField)
  - [x] 1.2 Define `ReviewEventType` TextChoices enum: `PRE_QA_CONFIRMED`, `CHANGE_MARKED_REVIEWED`
  - [x] 1.3 Add append-only admin for ReviewEvent (has_add/change/delete_permission return False)
  - [x] 1.4 Generate and apply migration

- [x] **Task 2: Add new audit event types** (AC: 3)
  - [x] 2.1 Add `PRE_QA_REVIEW_CONFIRMED` and `REVIEW_ITEM_MARKED_REVIEWED` to `AuditEventType` in `backend/apps/audit/models.py`
  - [x] 2.2 Generate migration for the new choices

- [x] **Task 3: Implement pre-QA review domain services** (AC: 3, 4)
  - [x] 3.1 Create `backend/apps/reviews/domain/pre_qa_review.py`
  - [x] 3.2 Implement `confirm_pre_qa_review(batch, reviewer, note=None)`:
    - Validate batch status is `awaiting_pre_qa` or `in_pre_qa_review`; raise `ValidationError` otherwise
    - Validate no red-severity blocking conditions remain (call `get_batch_review_summary` and check severity is not `red`); raise `ValidationError` if blocked
    - Create `ReviewEvent(event_type=PRE_QA_CONFIRMED, batch=batch, reviewer=reviewer, note=note)`
    - Update `batch.status` to `awaiting_quality_review` and save
    - Record audit event `PRE_QA_REVIEW_CONFIRMED` with metadata `{batch_id, batch_reference, reviewer_id, note}`
    - Return updated batch
  - [x] 3.3 Implement `mark_step_reviewed(batch, step, reviewer, note=None)`:
    - Validate batch status is `awaiting_pre_qa` or `in_pre_qa_review`
    - Validate step belongs to the batch
    - Validate step has at least one reviewable flag (`changed_since_review` or `review_required`); `changed_since_signature` remains a re-signature integrity signal and is not cleared by review
    - Clear `changed_since_review` and `review_required` flags on the step; save
    - If batch status is `awaiting_pre_qa`, transition to `in_pre_qa_review`
    - Create `ReviewEvent(event_type=CHANGE_MARKED_REVIEWED, batch=batch, step=step, reviewer=reviewer, note=note)`
    - Record audit event `REVIEW_ITEM_MARKED_REVIEWED` with metadata `{batch_id, step_id, step_reference, reviewer_id}`
    - Return updated step

- [x] **Task 4: Implement pre-QA review API endpoints** (AC: 1, 2, 3, 4)
  - [x] 4.1 Create `backend/apps/reviews/api/views_pre_qa.py` (or add to existing views.py)
  - [x] 4.2 Implement `ConfirmPreQaReviewView` — `POST /api/v1/batches/{batch_id}/pre-qa-review/confirm`
    - Request serializer: `ConfirmPreQaReviewRequestSerializer` with optional `note` field
    - Response serializer: `PreQaReviewConfirmationSerializer` with `batch_id`, `batch_reference`, `batch_status`, `confirmed_at`, `reviewer_note`
    - Permission: `IsAuthenticated` + `SiteScopedRolePermission` with `required_site_roles = (SiteRole.PRODUCTION_REVIEWER,)`
    - Call `confirm_pre_qa_review` domain service
    - Return 200 on success, 400 on validation errors (problem-details format)
  - [x] 4.3 Implement `MarkStepReviewedView` — `POST /api/v1/batches/{batch_id}/review-items/{step_id}/mark-reviewed`
    - Request serializer: `MarkStepReviewedRequestSerializer` with optional `note` field
    - Response serializer: `MarkStepReviewedResponseSerializer` with `step_id`, `step_reference`, `review_status`, `flags_cleared`
    - Permission: `IsAuthenticated` + `SiteScopedRolePermission` with `required_site_roles = (SiteRole.PRODUCTION_REVIEWER,)`
    - Call `mark_step_reviewed` domain service
    - Return 200 on success, 400 on validation errors
  - [x] 4.4 Add `@extend_schema` decorators for drf-spectacular documentation
  - [x] 4.5 Wire URL patterns into `backend/apps/reviews/api/urls.py`
  - [x] 4.6 Ensure URL patterns are registered in `backend/shared/api/urls.py`

- [x] **Task 5: Build frontend pre-QA review feature** (AC: 1, 2)
  - [x] 5.1 Create `frontend/src/features/pre-qa-review/` directory structure:
    - `api/` — API client hooks
    - `components/` — UI components
    - `routes/` — route-level pages
  - [x] 5.2 Install required shadcn/ui components: `npx shadcn@latest add badge card table alert-dialog scroll-area collapsible separator tooltip` from `frontend/` directory
  - [x] 5.3 Create shared API client utility `frontend/src/shared/api/client.ts`:
    - `apiFetch(path, options)` wrapper around `fetch` that prepends `appConfig.apiBaseUrl`, includes credentials, handles CSRF, and parses JSON
    - All API calls go through this utility
  - [x] 5.4 Create API hooks in `frontend/src/features/pre-qa-review/api/`:
    - `use-review-summary.ts` — TanStack Query hook wrapping `GET /batches/{id}/review-summary`
    - `use-confirm-pre-qa-review.ts` — TanStack mutation wrapping `POST /batches/{id}/pre-qa-review/confirm`
    - `use-mark-step-reviewed.ts` — TanStack mutation wrapping `POST /batches/{id}/review-items/{id}/mark-reviewed`
  - [x] 5.5 Create `ReviewExceptionList` component in `frontend/src/features/pre-qa-review/components/ReviewExceptionList.tsx`:
    - Summary bar: total steps, green/amber/red counts
    - Exception items: step reference, issue type (missing data, unsigned, changed), severity badge
    - Click to expand step detail with flags
    - "Mark as Reviewed" button on items with `changed_since_review` or `review_required` flags
    - Keyboard accessible: arrow keys through list, Enter to expand
  - [x] 5.6 Create `PreQaReviewPage` route component in `frontend/src/features/pre-qa-review/routes/PreQaReviewPage.tsx`:
    - Fetches review summary for batch (from URL param)
    - Displays batch header (reference, status, overall severity)
    - Renders `ReviewExceptionList` with flagged steps
    - "Confirm Handoff" primary action button (disabled when severity is red)
    - Confirm action uses AlertDialog for confirmation before submitting
    - Shows loading/error states
  - [x] 5.7 Register route in `frontend/src/app/router.tsx`: `/review/:batchId`
  - [x] 5.8 Type definitions: create `frontend/src/features/pre-qa-review/types.ts` with TypeScript interfaces matching API response shapes (use `snake_case` matching backend)

- [x] **Task 6: Write backend tests** (AC: 1, 2, 3, 4, 5)
  - [x] 6.1 Domain unit tests in `backend/apps/reviews/tests/test_pre_qa_review_domain.py`:
    - Confirm succeeds when batch is `awaiting_pre_qa` with green/amber severity
    - Confirm fails when batch has red severity (blocking issues)
    - Confirm fails from invalid batch states (in_progress, released, etc.)
    - Confirm transitions batch to `awaiting_quality_review`
    - Confirm creates ReviewEvent with correct type and metadata
    - Confirm records audit event
    - Mark-reviewed clears `changed_since_review` and `review_required` flags
    - Mark-reviewed transitions batch from `awaiting_pre_qa` to `in_pre_qa_review`
    - Mark-reviewed fails for step without reviewable flags
    - Mark-reviewed fails for step not in the batch
    - Mark-reviewed creates ReviewEvent and audit event
  - [x] 6.2 API integration tests in `backend/apps/reviews/tests/test_pre_qa_review_api.py`:
    - Authenticated production_reviewer gets 200 on confirm
    - Authenticated production_reviewer gets 200 on mark-reviewed
    - Unauthenticated user gets 401
    - User without production_reviewer role gets 404 (fail-closed)
    - Quality_reviewer cannot confirm pre-QA (only production_reviewer)
    - Confirm returns correct response shape
    - Mark-reviewed returns correct response shape
    - Confirm with red severity returns 400 with problem-details
    - Invalid batch state returns 400
    - Non-existent batch returns 404

- [x] **Task 7: Write frontend tests** (AC: 1, 2)
  - [x] 7.1 Install `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom` as devDependencies if not present
  - [x] 7.2 Component tests for `ReviewExceptionList`: renders flagged steps, severity badges, mark-reviewed button, keyboard navigation
  - [x] 7.3 Component tests for `PreQaReviewPage`: loading state, error state, confirm button disabled when red severity, confirm dialog interaction

- [x] **Task 8: Run quality gates** (AC: all)
  - [x] 8.1 `make check` passes (lint, typecheck, test, security, architecture-check)

## Dev Notes

### Dependencies on Story 5.1 (CRITICAL)

Story 5.1 created the foundation this story builds on:
- **`reviews` app** with `domain/review_summary.py`, `selectors/review_summary.py`, `api/serializers.py`, `api/views.py`
- **`batches` app** with stub models: `Batch`, `BatchStep`, `StepSignature`, `DossierChecklistItem`
- **Review summary endpoint** `GET /api/v1/batches/{batch_id}/review-summary` already returns traffic-light severity, flagged steps, and checklist completeness
- **`SiteScopedRolePermission`** already configured for reviewer roles
- **Frozen dataclasses** for review read models: `ReviewSummary`, `FlaggedStep`, `FlagCounts`, etc.

Reuse `get_batch_review_summary()` from `reviews/selectors/review_summary.py` to check severity before confirming handoff.

### Canonical Batch Lifecycle States Relevant to This Story

```
in_progress → awaiting_pre_qa → in_pre_qa_review → awaiting_quality_review
```

- `awaiting_pre_qa`: batch submitted by production, waiting for reviewer to start
- `in_pre_qa_review`: reviewer is actively inspecting (implicit transition on first mark-reviewed action)
- `awaiting_quality_review`: pre-QA confirmed, ready for quality handoff

The `confirm_pre_qa_review` action accepts batches in `awaiting_pre_qa` OR `in_pre_qa_review` and transitions to `awaiting_quality_review`.

### Existing BatchStatus Enum (in `backend/apps/batches/models.py`)

```python
class BatchStatus(models.TextChoices):
    IN_PROGRESS = "in_progress"
    AWAITING_PRE_QA = "awaiting_pre_qa"
    IN_PRE_QA_REVIEW = "in_pre_qa_review"
    AWAITING_QUALITY_REVIEW = "awaiting_quality_review"
    IN_QUALITY_REVIEW = "in_quality_review"
    RETURNED_FOR_CORRECTION = "returned_for_correction"
    RELEASED = "released"
    REJECTED = "rejected"
```

These already exist from Story 5.1 stub models. No changes needed.

### ReviewEvent Model Design

ReviewEvent is a **first-class domain model** (not just an audit entry). The architecture specifies `review_events` as a relational table alongside `batches`, `signatures`, and `audit_events`.

```python
class ReviewEventType(models.TextChoices):
    PRE_QA_CONFIRMED = "pre_qa_confirmed"
    CHANGE_MARKED_REVIEWED = "change_marked_reviewed"
    # Future: QUALITY_REVIEW_STARTED, RELEASED, REJECTED, RETURNED_FOR_CORRECTION

class ReviewEvent(models.Model):
    batch = models.ForeignKey("batches.Batch", on_delete=models.PROTECT, related_name="review_events")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="review_events")
    event_type = models.CharField(max_length=64, choices=ReviewEventType.choices)
    step = models.ForeignKey("batches.BatchStep", on_delete=models.PROTECT, null=True, blank=True, related_name="review_events")
    note = models.TextField(blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
```

Admin: append-only (has_add/change/delete_permission all return False). All fields readonly.

### API Contracts

**Endpoint 1:** `POST /api/v1/batches/{batch_id}/pre-qa-review/confirm`

- **Auth:** Session-based + `PRODUCTION_REVIEWER` role at batch's site
- **Request:**
```json
{
  "note": "All exceptions reviewed, dossier ready for quality."
}
```
- **Response (200 OK):**
```json
{
  "batch_id": 42,
  "batch_reference": "LOT-2026-0042",
  "batch_status": "awaiting_quality_review",
  "confirmed_at": "2026-03-13T14:30:00+01:00",
  "reviewer_note": "All exceptions reviewed, dossier ready for quality."
}
```
- **Error (400):** Problem-details with code `"pre_qa_review_blocked"` when severity is red, or `"invalid_batch_state"` when batch is not in an acceptable state
- **Error (401):** Not authenticated
- **Error (404):** Batch not found or user lacks production_reviewer role (fail-closed)

**Endpoint 2:** `POST /api/v1/batches/{batch_id}/review-items/{step_id}/mark-reviewed`

- **Auth:** Session-based + `PRODUCTION_REVIEWER` role at batch's site
- **Request:**
```json
{
  "note": "Change verified with operator."
}
```
- **Response (200 OK):**
```json
{
  "step_id": 5,
  "step_reference": "Step 5 - Filling",
  "review_status": "reviewed",
  "flags_cleared": ["changed_since_review", "review_required"],
  "batch_status": "in_pre_qa_review"
}
```
- **Error (400):** `"no_reviewable_flags"` when step has no review-clearable flags
- **Error (401/404):** Same as above; nested `step_id` lookup is fail-closed and returns `404` when the step is not found under the requested batch

### Validation Rules for Confirm Action

The `confirm_pre_qa_review` domain service MUST call `get_batch_review_summary(batch)` and check severity:
- **green or amber**: Confirmation allowed. Amber means there are non-blocking issues but the supervisor consciously accepts handoff.
- **red**: Confirmation blocked. Red means blocking conditions exist (missing required data, missing required signatures, blocking exceptions unresolved). Return error with details of what blocks confirmation.

This prevents the supervisor from confirming a dossier that is objectively incomplete.

### Frontend Architecture

**Route:** `/review/:batchId` — Pre-QA review page for a specific batch.

**Component hierarchy:**
```
PreQaReviewPage
  +-- BatchReviewHeader (reference, status, severity badge)
  +-- ReviewExceptionList
  |   +-- SummaryBar (total, green, amber, red counts)
  |   +-- FlaggedStepItem (per flagged step)
  |       +-- StepStatusBadge (severity color + icon)
  |       +-- FlagList (missing_data, unsigned, changed badges)
  |       +-- MarkReviewedButton (if reviewable flags present)
  +-- ConfirmHandoffSection
      +-- Button ("Confirm Quality Handoff") — primary, disabled when red
      +-- AlertDialog confirmation before submit
      +-- Optional note input (textarea)
```

**TanStack Query patterns:**
- `useQuery` for review summary (auto-refetch on mutation success)
- `useMutation` for confirm and mark-reviewed with `onSuccess` invalidating `review-summary` query key
- Error handling: display problem-details `detail` message in toast or inline alert

**No global state store needed.** All state is server state via TanStack Query or local via React primitives.

### shadcn/ui Components to Install

Install from `frontend/` directory:
```bash
npx shadcn@latest add badge card table alert-dialog scroll-area collapsible separator tooltip
```

These are needed for:
- `Badge` — severity indicators and flag badges
- `Card` — batch header card, exception item cards
- `AlertDialog` — confirm handoff confirmation dialog
- `Table` — step listing in exception list (optional, may use card-based layout)
- `ScrollArea` — scrollable exception list
- `Collapsible` — expandable step details
- `Separator` — visual section dividers
- `Tooltip` — disabled button explanation

### Shared API Client Utility

No shared `fetch` wrapper exists yet. Create `frontend/src/shared/api/client.ts`:

```typescript
import { appConfig } from "@/shared/config/app-config";

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${appConfig.apiBaseUrl}${path}`;
  const response = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw error;
  }
  return response.json();
}
```

This follows the existing `appConfig.apiBaseUrl` pattern and includes credentials for session-based auth.

### Security Requirements

- **RBAC enforcement server-side:** Only `PRODUCTION_REVIEWER` role can confirm pre-QA or mark steps reviewed. Quality reviewers should NOT have pre-QA confirm capability.
- **Fail-closed:** Return 404 (not 403) for unauthorized batch access to prevent enumeration.
- **CSRF protection:** POST endpoints require CSRF token. Django's SessionAuthentication enforces this. Frontend must send CSRF cookie.
- **Audit trail:** Every review action creates both a ReviewEvent (domain record) and an AuditEvent (audit trail). Use `finally` block for audit writes per CLAUDE.md security rules.
- **No step-up re-auth required:** Pre-QA confirmation is a review action, not an electronic signature. Step-up re-authentication is reserved for signature actions per architecture.

### Testing Requirements

**Backend test patterns (from Story 5.1 and 1.3):**
- `@pytest.mark.django_db` on all DB tests
- `get_user_model()` for user creation
- `APIClient` with `force_authenticate(user=...)` for API tests
- Explicit assertion of status codes, response shapes, field values
- Test unauthorized access (no session, wrong role, wrong site)
- factory-boy for fixtures (or inline creation if factory not yet built for reviews)

**Minimum backend test scenarios:**
1. Confirm succeeds from `awaiting_pre_qa` with green severity → 200, batch status `awaiting_quality_review`
2. Confirm succeeds from `in_pre_qa_review` with amber severity → 200
3. Confirm blocked with red severity → 400 with `pre_qa_review_blocked` code
4. Confirm from invalid state (`in_progress`) → 400 with `invalid_batch_state` code
5. Mark-reviewed clears flags on step → 200, flags cleared
6. Mark-reviewed transitions batch from `awaiting_pre_qa` to `in_pre_qa_review`
7. Mark-reviewed on step without reviewable flags → 400
8. Mark-reviewed on step not in batch → 404 (fail-closed nested lookup)
9. ReviewEvent created for both actions
10. AuditEvent created for both actions
11. Unauthenticated → 401
12. Wrong role (quality_reviewer) → 404
13. Non-existent batch → 404

**Frontend test scenarios:**
- ReviewExceptionList renders with flagged steps and severity badges
- Mark-reviewed button triggers mutation and refreshes summary
- Confirm button disabled when severity is red
- Confirm dialog appears before submission
- Loading and error states render correctly

### Code Conventions (Established Patterns)

- `from __future__ import annotations` in all Python files
- Full type hints (mypy strict mode)
- `snake_case` for Python; `camelCase` for TypeScript functions/variables; `PascalCase` for components/types
- `@extend_schema` on all API views for drf-spectacular
- Explicit request/response serializers with typed nested serializers (no DictField/ListField for structured data)
- Problem-details exceptions from DRF for errors
- `kebab-case` for non-component TypeScript files, `PascalCase` for React component files
- Path alias `@/*` for imports (resolves to `./src/*`)
- API JSON uses `snake_case` — no camelCase translation at boundary

### Library & Framework Requirements

| Library | Version | Usage |
|---------|---------|-------|
| Django | 5.2 LTS (>=5.2,<5.3) | Models, ORM, authentication |
| Django REST Framework | 3.16 (>=3.16,<3.17) | API views, serializers, permissions |
| drf-spectacular | 0.29 (>=0.29,<0.30) | OpenAPI schema |
| PostgreSQL | 17.x | Transactional datastore |
| React | 19.x | UI library |
| React Router DOM | 7.x | Client-side routing |
| TanStack Query | 5.x | Server state management |
| Zod | 4.x | Runtime type validation (for response parsing) |
| shadcn/ui + Radix UI | latest | UI primitives |
| Tailwind CSS | 4.x | Styling |
| lucide-react | latest | Icons |
| pytest + pytest-django | (dev) | Backend testing |
| factory-boy | (dev) | Backend test fixtures |
| Vitest | 3.x (dev) | Frontend testing |
| @testing-library/react | (dev) | Frontend component tests |

### Previous Story Intelligence (from Story 5.1)

**Patterns established:**
- Review summary uses frozen dataclasses as read models, NOT Django model instances
- Selector layer composes domain functions with ORM queries
- `SiteScopedRolePermission` with `allow_object_level_site_resolve = True` and `get_site_for_object()` method on view
- Stub batch models in `batches/models.py` are functional with all required fields and status enums
- URL patterns mounted via `shared/api/urls.py` include
- StepSignature admin is append-only (established immutability pattern)

**Debug log learnings:**
- URL pattern index: new URL includes added at end of `shared/api/urls.py` to preserve existing test references
- Ruff import sorting auto-fixes expected
- mypy strict: use `dict[str, Any]` for compatibility with Django ORM `.values()` returns

**Review feedback applied in 5.1:**
- Corrected auth/error semantics: `401` for unauthenticated, fail-closed `404` for unauthorized
- Distinguished blocking vs non-blocking exceptions in severity derivation
- Added `review_required` flag support
- Made signature admin records immutable

### Git Intelligence (Recent Commits)

```
5f40a43 Use tuples in frozen dataclasses and expose missing serializer fields
b7e0e6f Fix Greptile PR review findings for Story 5.1
c161fe7 Format Story 5.1 backend files
afd3956 Implement story 5.1 review summary
```

Key patterns from commits:
- Frozen dataclass fields use `tuple` not `list` for immutability
- Serializer fields explicitly expose all nested fields (no implicit DictField)
- Code formatting with ruff applied as standard

### Project Structure Notes

**New files to create:**
```
backend/apps/reviews/
  domain/
    pre_qa_review.py              # Domain service: confirm + mark-reviewed
  api/
    serializers_pre_qa.py         # Request/response serializers for pre-QA actions
    views_pre_qa.py               # ConfirmPreQaReviewView, MarkStepReviewedView
  tests/
    test_pre_qa_review_domain.py  # Domain unit tests
    test_pre_qa_review_api.py     # API integration tests

frontend/src/
  shared/
    api/
      client.ts                   # Shared fetch wrapper
  features/
    pre-qa-review/
      api/
        use-review-summary.ts     # TanStack Query hook
        use-confirm-pre-qa-review.ts
        use-mark-step-reviewed.ts
      components/
        ReviewExceptionList.tsx    # Exception-based review list
        FlaggedStepItem.tsx        # Individual flagged step row
        BatchReviewHeader.tsx      # Batch header with severity
        ConfirmHandoffSection.tsx  # Confirm action with dialog
      routes/
        PreQaReviewPage.tsx        # Route-level page component
      types.ts                    # TypeScript interfaces
```

**Files to modify:**
- `backend/apps/reviews/models.py` — Add ReviewEvent model and ReviewEventType enum
- `backend/apps/reviews/admin.py` — Add ReviewEventAdmin (append-only)
- `backend/apps/reviews/api/urls.py` — Add new endpoint URL patterns
- `backend/apps/audit/models.py` — Add new AuditEventType choices
- `backend/shared/api/urls.py` — Register new URL patterns if needed
- `frontend/src/app/router.tsx` — Add `/review/:batchId` route
- `frontend/package.json` — Add @testing-library devDependencies if not present

**URL mounting:** New endpoints mount under existing reviews URL namespace. The `review-items` sub-resource nests under batches to match the architecture contract: `/api/v1/batches/{batch_id}/review-items/{step_id}/mark-reviewed`.

### Architecture Compliance

- **Domain code CANNOT depend on API packages** — `domain/pre_qa_review.py` must not import from `api/`
- **API packages can call domain services and selectors** — views orchestrate between clients and backend
- **Workflow transitions are explicit backend action endpoints** — no arbitrary PATCH on batch status
- **Review flags are backend-derived** — frontend never reconstructs state from audit history
- **Problem-details error format** — use DRF exception handling with stable machine-readable codes
- **Additive-first migrations** — ReviewEvent is a new table, no destructive changes
- **Audit trail immutability** — ReviewEvent admin is append-only, audit events are append-only
- **Fail-closed security** — `finally` blocks for audit writes per CLAUDE.md

### Scope Boundaries (DO NOT IMPLEMENT)

- Quality review surface (Story 5.3)
- Quality disposition decisions — release, reject, return for correction (Story 5.4)
- Return-for-correction action from pre-QA (future scope — reviewer simply doesn't confirm)
- Batch creation or `submit_for_pre_qa` action (not in scope; test with batches already in correct state)
- Electronic signature on pre-QA confirmation (not required per architecture — this is a review action, not a signature)
- Frontend batch list/dashboard (this story focuses on single-batch review; batch list is future work)
- SSR or server-side rendering (authenticated SPA per architecture)
- Global state store (no Redux/Zustand — TanStack Query + React primitives only)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5 - Story 5.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Workflow State Model & Transitions]
- [Source: _bmad-output/planning-artifacts/architecture.md#MVP Public Contracts - POST pre-qa-review/confirm]
- [Source: _bmad-output/planning-artifacts/architecture.md#MVP Public Contracts - POST review-items/mark-reviewed]
- [Source: _bmad-output/planning-artifacts/architecture.md#Canonical Read Models for Review]
- [Source: _bmad-output/planning-artifacts/architecture.md#Backend App Internal Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#Transition Rules]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 3 - Supervisor Pre-QA Review]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#ReviewExceptionList Component]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#DossierIntegritySummary Component]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Review-by-Exception Dashboard Pattern]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Button Hierarchy for Review Actions]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#ISA-101 Color Strategy]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#State Badge Patterns]
- [Source: _bmad-output/planning-artifacts/prd.md#FR24-FR27 Review Requirements]
- [Source: _bmad-output/planning-artifacts/prd.md#FR48 Dossier Completeness for Reviewers]
- [Source: CLAUDE.md#Security & Defensive Coding Rules]
- [Source: CLAUDE.md#API Contract Rules]
- [Source: CLAUDE.md#Frontend Component Rules]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

- Ruff auto-fixed import sorting in `domain/pre_qa_review.py` (expected per Story 5.1 learnings)
- mypy strict: replaced reverse-relation access `batch.review_events` with explicit `ReviewEvent.objects.filter()` query
- ResizeObserver polyfill added to `test/setup.ts` for Radix ScrollArea compatibility with jsdom
- shadcn/ui badge.tsx and button.tsx emit react-refresh warnings (generated code, not project code)

### Completion Notes List

- Task 1: Created `ReviewEvent` model with `ReviewEventType` enum (`PRE_QA_CONFIRMED`, `CHANGE_MARKED_REVIEWED`). Append-only admin with all readonly_fields. Migration applied.
- Task 2: Added `PRE_QA_REVIEW_CONFIRMED` and `REVIEW_ITEM_MARKED_REVIEWED` to `AuditEventType`. Migration applied.
- Task 3: Implemented `confirm_pre_qa_review` and `mark_step_reviewed` domain services with full validation, audit trail in `finally` blocks, correct batch status transitions, and strict preservation of `changed_since_signature` until re-signature.
- Task 4: Created `ConfirmPreQaReviewView` and `MarkStepReviewedView` with typed serializers, `@extend_schema` decorators, fail-closed authorization (PRODUCTION_REVIEWER only), and problem-details error format.
- Task 5: Built complete frontend feature: shared `apiFetch` client, TanStack Query hooks, `ReviewExceptionList` with severity badges and collapsible details, `PreQaReviewPage` with AlertDialog confirmation, route registered at `/review/:batchId`.
- Task 6: 18 domain unit tests + 14 API integration tests covering all specified scenarios (valid states, invalid states, red/amber/green severity, auth, permissions, response shapes, review events, audit events).
- Task 7: 7 ReviewExceptionList component tests + 7 PreQaReviewPage tests covering loading/error states, severity badge rendering, confirm button disabled when red, confirm dialog interaction.
- Task 8: `make check` passes — all 155 backend tests, 15 frontend tests, lint, typecheck, security, architecture checks pass.

### Change Log

- 2026-03-13: Implemented Story 5.2 — pre-QA review and quality handoff confirmation (all 8 tasks)

### File List

**New files:**
- backend/apps/reviews/domain/pre_qa_review.py
- backend/apps/reviews/api/serializers_pre_qa.py
- backend/apps/reviews/api/views_pre_qa.py
- backend/apps/reviews/tests/test_pre_qa_review_domain.py
- backend/apps/reviews/tests/test_pre_qa_review_api.py
- backend/apps/reviews/migrations/0002_add_review_event.py
- backend/apps/audit/migrations/0004_add_pre_qa_review_event_types.py
- frontend/src/shared/api/client.ts
- frontend/src/shared/lib/index.ts
- frontend/src/features/pre-qa-review/types.ts
- frontend/src/features/pre-qa-review/api/use-review-summary.ts
- frontend/src/features/pre-qa-review/api/use-confirm-pre-qa-review.ts
- frontend/src/features/pre-qa-review/api/use-mark-step-reviewed.ts
- frontend/src/features/pre-qa-review/components/ReviewExceptionList.tsx
- frontend/src/features/pre-qa-review/components/ReviewExceptionList.test.tsx
- frontend/src/features/pre-qa-review/routes/PreQaReviewPage.tsx
- frontend/src/features/pre-qa-review/routes/PreQaReviewPage.test.tsx
- frontend/src/shared/ui/alert-dialog.tsx
- frontend/src/shared/ui/badge.tsx
- frontend/src/shared/ui/card.tsx
- frontend/src/shared/ui/collapsible.tsx
- frontend/src/shared/ui/scroll-area.tsx
- frontend/src/shared/ui/separator.tsx
- frontend/src/shared/ui/tooltip.tsx

**Modified files:**
- backend/apps/reviews/models.py
- backend/apps/reviews/admin.py
- backend/apps/reviews/api/urls.py
- backend/apps/audit/models.py
- frontend/src/app/router.tsx
- frontend/src/test/setup.ts
- frontend/src/shared/ui/button.tsx (shadcn reinstall)
- frontend/package.json (added @testing-library dependencies)
- frontend/package-lock.json
- _bmad-output/implementation-artifacts/sprint-status.yaml
