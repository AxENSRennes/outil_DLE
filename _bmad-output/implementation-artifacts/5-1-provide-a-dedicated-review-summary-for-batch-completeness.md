# Story 5.1: Provide a Dedicated Review Summary for Batch Completeness

Status: done

## Story

As a production or quality reviewer,
I want a dedicated review-oriented summary of the batch dossier,
So that I can see completeness, missing signatures, and review-relevant issues without entering the operator execution flow.

## Acceptance Criteria

1. **Given** a batch exists with execution, signature, and integrity-state data, **When** a reviewer opens the batch for review, **Then** the system returns a dedicated review-oriented summary for that batch, **And** that summary is distinct from the operator execution experience.

2. **Given** reviewers need to assess dossier readiness quickly, **When** the summary is displayed, **Then** it shows the current completeness state of the dossier against the expected checklist, **And** it highlights missing data, missing signatures, and review-relevant changed states.

3. **Given** review should be driven by trusted backend semantics, **When** the summary is generated, **Then** it is built from canonical batch, signature, checklist, and integrity-state data, **And** the reviewer does not need to infer dossier health from raw execution details.

4. **Given** pre-QA and quality review will later diverge in behavior, **When** this story is implemented, **Then** the platform provides a shared review summary foundation usable by both review roles, **And** pre-QA confirmation, quality disposition, and release decisions remain outside the scope of this story.

5. **Given** this story should unlock later review surfaces in parallel, **When** it is completed, **Then** the review summary becomes a reusable read model for subsequent pre-QA and quality stories, **And** later stories can build on it without redefining completeness semantics.

## Tasks / Subtasks

- [x] **Task 1: Create `reviews` Django app scaffold** (AC: 3, 4)
  - [x] 1.1 Create `backend/apps/reviews/` with `api/`, `domain/`, `selectors/`, `tests/` subdirectories
  - [x] 1.2 Register app in `config/settings/base.py` INSTALLED_APPS
  - [x] 1.3 Create initial empty migration

- [x] **Task 2: Implement review summary selector** (AC: 1, 2, 3)
  - [x] 2.1 Create `backend/apps/reviews/selectors/review_summary.py`
  - [x] 2.2 Implement `get_batch_review_summary(batch_id)` that computes:
    - Step completion counts (total, complete, signed, not_started, in_progress)
    - Missing required data flags per step
    - Missing required signature flags per step
    - Changed-since-review flags per step
    - Changed-since-signature flags per step
    - Open exception counts
    - Dossier checklist completeness (expected vs. present documents)
  - [x] 2.3 Implement traffic-light severity derivation: green / amber / red
  - [x] 2.4 Return structured read model (dict or dataclass), not a Django model instance

- [x] **Task 3: Implement review summary domain service** (AC: 3, 5)
  - [x] 3.1 Create `backend/apps/reviews/domain/review_summary.py`
  - [x] 3.2 Implement completeness evaluation logic:
    - `evaluate_step_completeness(batch)` - per-step status with flags
    - `evaluate_signature_completeness(batch)` - missing signature detection
    - `evaluate_integrity_flags(batch)` - changed-since-review/signature detection
    - `derive_traffic_light_severity(summary)` - green/amber/red classification
  - [x] 3.3 Document severity rules:
    - **green**: no missing required data, no missing required signatures, no pending re-review, no blocking exceptions
    - **amber**: dossier navigable but needs attention (changes, notes, non-blocking issues)
    - **red**: blocked for handoff (missing required data, missing required signatures, blocking exceptions unresolved)

- [x] **Task 4: Implement review summary API endpoint** (AC: 1, 2)
  - [x] 4.1 Create `GET /api/v1/batches/{id}/review-summary` endpoint
  - [x] 4.2 Create `ReviewSummarySerializer` for response shape
  - [x] 4.3 Wire URL into batch routes
  - [x] 4.4 Add `@extend_schema` decorator for drf-spectacular documentation
  - [x] 4.5 Enforce authentication + role-based access (production_reviewer OR quality_reviewer)

- [x] **Task 5: Write tests** (AC: 1, 2, 3, 4, 5)
  - [x] 5.1 Unit tests for severity derivation logic (green/amber/red scenarios)
  - [x] 5.2 Unit tests for completeness evaluation (all-complete, partial, empty batch)
  - [x] 5.3 API integration tests for review-summary endpoint (auth, permissions, response shape)
  - [x] 5.4 Test that unauthenticated and unauthorized users are rejected
  - [x] 5.5 Test edge cases: batch with no steps, batch with all steps signed, batch with corrections

- [x] **Task 6: Run quality gates** (AC: all)
  - [x] 6.1 `make check` passes (lint, typecheck, test, security, architecture-check)

## Dev Notes

### Dependencies on Earlier Epics (CRITICAL)

This story assumes the following models/APIs exist from Epics 2-4. If they don't exist yet, they must be created or stubbed first:

- **From Epic 2 (Template Governance):** `MMR`, `MMRVersion` models with template structure definitions
- **From Epic 3 (Batch Execution):** `Batch`, `BatchStep` models with execution state, field values, step completion status
- **From Epic 3 (Signatures):** `Signature` model binding signer, meaning, timestamp, and step reference
- **From Epic 4 (Audit & Corrections):** `AuditEvent` extension for batch actions, correction records with reason-for-change, integrity flags (changed_since_review, changed_since_signature)

Check `backend/apps/` for existing apps. As of Story 1.3, only `authz`, `sites`, and `audit` apps exist. The batch/execution/signature models will need to be created by prerequisite stories or stubbed with sufficient fidelity for the review summary to be meaningful.

### Canonical Batch Lifecycle States

The review summary operates on batches in any of these states:
- `in_progress`, `awaiting_pre_qa`, `in_pre_qa_review`, `awaiting_quality_review`, `in_quality_review`, `returned_for_correction`, `released`, `rejected`

### Canonical Step States

- `not_started`, `in_progress`, `complete`, `signed`

### Review-Relevant Flags (Derived or Stored)

- `missing_required_data` - step has unfilled required fields
- `missing_required_signature` - step requires signature but none recorded
- `changed_since_review` - correction made after supervisor review
- `changed_since_signature` - correction made after step was signed
- `review_required` - flag indicating re-review needed
- `has_open_exception` - linked exception/deviation is unresolved

### Traffic-Light Severity Model

| Severity | Conditions | Meaning |
|----------|-----------|---------|
| **green** | No missing required data, no missing required signatures, no pending re-review, no blocking exceptions | Ready for handoff |
| **amber** | Dossier navigable but has changes, notes, or non-blocking issues needing attention | Reviewable with caveats |
| **red** | Missing required data, missing required signatures, or blocking exceptions unresolved | Blocked for handoff |

### API Contract

**Endpoint:** `GET /api/v1/batches/{batch_id}/review-summary`

**Authentication:** Session-based (Django SessionAuthentication)
**Authorization:** User must have `production_reviewer` OR `quality_reviewer` role for the batch's site

**Response shape (200 OK):**
```json
{
  "batch_id": 42,
  "batch_reference": "LOT-2026-0042",
  "batch_status": "awaiting_pre_qa",
  "severity": "amber",
  "step_summary": {
    "total": 12,
    "not_started": 0,
    "in_progress": 1,
    "complete": 8,
    "signed": 3
  },
  "flags": {
    "missing_required_data": 1,
    "missing_required_signatures": 2,
    "changed_since_review": 1,
    "changed_since_signature": 0,
    "open_exceptions": 0
  },
  "checklist": {
    "expected_documents": 5,
    "present_documents": 4,
    "missing_documents": ["weighing-record"]
  },
  "flagged_steps": [
    {
      "step_id": 7,
      "step_reference": "Step 7 - Weighing",
      "step_status": "in_progress",
      "flags": ["missing_required_data"],
      "severity": "red"
    },
    {
      "step_id": 3,
      "step_reference": "Step 3 - Mixing",
      "step_status": "complete",
      "flags": ["missing_required_signature"],
      "severity": "red"
    },
    {
      "step_id": 5,
      "step_reference": "Step 5 - Filling",
      "step_status": "signed",
      "flags": ["changed_since_review"],
      "severity": "amber"
    }
  ]
}
```

**Error responses:** Problem-details format with stable machine-readable codes:
- `404` - Batch not found or user lacks reviewer role for this batch's site (fail-closed, no enumeration)
- `401` - Not authenticated

### Project Structure Notes

**New files to create:**
```
backend/apps/reviews/
  __init__.py
  apps.py                    # ReviewsConfig
  models.py                  # Empty initially - review summary is computed, not persisted
  api/
    __init__.py
    urls.py                  # Wire review-summary endpoint
    views.py                 # ReviewSummaryView
    serializers.py           # ReviewSummarySerializer, FlaggedStepSerializer
  domain/
    __init__.py
    review_summary.py        # Completeness evaluation, severity derivation
  selectors/
    __init__.py
    review_summary.py        # get_batch_review_summary() query composition
  tests/
    __init__.py
    test_review_summary_api.py     # API integration tests
    test_review_summary_domain.py  # Unit tests for domain logic
    test_review_summary_selectors.py  # Selector tests
  migrations/
    __init__.py
    0001_initial.py          # Empty initial migration
```

**Files to modify:**
- `config/settings/base.py` - Add `apps.reviews.apps.ReviewsConfig` to INSTALLED_APPS
- `backend/shared/api/urls.py` - Include `reviews` URL patterns (or add via batches URL namespace)

**URL mounting approach:** The review summary is accessed via `/api/v1/batches/{id}/review-summary`. Two options:
1. Mount under `apps/batches/api/urls.py` if a batches app exists
2. Mount under `apps/reviews/api/urls.py` with its own URL prefix

Prefer option 2 for domain isolation: `reviews` app owns its own routes.

### Architecture Compliance

- **Domain code CANNOT depend on API packages** - domain/ and selectors/ must not import from api/
- **API packages can call domain services and selectors** - views orchestrate between clients and backend
- **Shared module must NOT encode feature business rules** - use reviews/domain/ for review logic
- **No business-data cache in MVP** - database is the single source of truth
- **Audit trail immutability** - if review summary triggers audit events, use append-only pattern via `audit.domain.record_audit_event()`
- **Problem-details error format** - use DRF exception handling with stable machine-readable codes
- **Additive-first migrations** - no destructive schema changes

### Security Requirements

- **RBAC enforcement server-side:** Check `production_reviewer` or `quality_reviewer` role for the batch's site before returning data
- **Reuse `SiteScopedRolePermission`** from `backend/shared/permissions/site_roles.py` - configure `required_site_roles` on the view
- **Session authentication:** Use Django SessionAuthentication (already configured project-wide)
- **CSRF not required on GET endpoints** - read-only endpoint, no state mutation
- **No sensitive data in response:** Review summary contains operational data, not secrets
- **Fail-closed:** Do not leak batch existence via error messages to unauthorized users; return `404` for unauthorized batch access and `401` for unauthenticated requests.

### Library & Framework Requirements

| Library | Version | Usage |
|---------|---------|-------|
| Django | 5.2 LTS (>=5.2,<5.3) | Models, ORM, authentication |
| Django REST Framework | 3.16 (>=3.16,<3.17) | API views, serializers, permissions |
| drf-spectacular | 0.29 (>=0.29,<0.30) | OpenAPI schema generation |
| PostgreSQL | 17.x | Database queries for summary computation |
| pytest + pytest-django | (dev) | Testing |
| factory-boy | (dev) | Test fixture factories |

### Testing Requirements

**Test patterns to follow (from Story 1.3):**
- `@pytest.mark.django_db` on all DB tests
- `get_user_model()` for user creation
- `csrf_client()` helper for POST endpoints (not needed here - GET only)
- Explicit assertion of status codes, response shapes, and field values
- Test unauthorized access (no session, wrong role, wrong site)

**Minimum test scenarios:**
1. Authenticated reviewer gets 200 with correct summary shape
2. Unauthenticated user gets 401
3. User without reviewer role gets 404 (fail-closed, no enumeration)
4. Batch with all steps complete and signed returns green severity
5. Batch with missing required data returns red severity
6. Batch with missing signatures returns red severity
7. Batch with changed-since-review flags returns amber severity
8. Batch with no steps returns green (edge case - empty batch)
9. Batch with open exceptions returns amber or red depending on blocking status
10. Response includes flagged_steps with correct per-step flags

**Performance target:** Review summary endpoint must respond within 4 seconds for 95th percentile (NFR4).

### Code Conventions (from established patterns)

- `from __future__ import annotations` in all files
- Full type hints (mypy strict mode)
- `snake_case` for Python functions, variables, modules
- `PascalCase` for classes
- API JSON uses `snake_case`
- Dates as ISO 8601 strings with timezone
- `@extend_schema` on all API views for drf-spectacular
- Explicit request/response serializers (not inline dict returns)
- Problem-details exceptions from DRF for errors

### Scope Boundaries (DO NOT IMPLEMENT)

- Pre-QA review confirmation action (Story 5.2)
- Quality review surface with inspection capabilities (Story 5.3)
- Quality disposition decisions - release/reject/return (Story 5.4)
- Review event persistence or audit logging for viewing the summary (read-only, no side effects)
- Frontend components (ReviewExceptionList, DossierIntegritySummary) - backend only for this story
- Batch state transitions triggered by viewing the summary

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5 - Story 5.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Review-Relevant Flags and Derived States]
- [Source: _bmad-output/planning-artifacts/architecture.md#MVP Review Actions - GET review-summary]
- [Source: _bmad-output/planning-artifacts/architecture.md#Canonical Read Models for Review]
- [Source: _bmad-output/planning-artifacts/architecture.md#Backend App Internal Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#API Patterns and Endpoint Design]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Review by Exception]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Traffic-Light Severity Model]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 3 - Supervisor Pre-QA Review]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#ReviewExceptionList Component]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#DossierIntegritySummary Component]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Success Criteria #3 - 30-second review dashboard]
- [Source: CLAUDE.md#Security & Defensive Coding Rules]

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

- DB migration inconsistency (pre-existing): `admin.0001_initial` applied before `authz.0001_initial` — bypassed for `makemigrations` only
- Ruff import sorting auto-fixed in domain and test files
- mypy strict mode: changed `dict[str, object]` to `dict[str, Any]` for compatibility with Django ORM `.values()` return types
- URL pattern index shift: moved reviews URL include to end of `shared/api/urls.py` to preserve existing test that references `urlpatterns[2]`

### Completion Notes List

- Created `batches` app with stub models (Batch, BatchStep, StepSignature, DossierChecklistItem) since Epics 2-4 models don't exist yet. These stubs provide sufficient fidelity for the review summary selector to query.
- Implemented three-layer architecture: domain (pure logic) -> selectors (DB queries + domain composition) -> API (DRF views + serializers)
- Domain layer uses frozen dataclasses as read models (ReviewSummary, StepSummary, FlagCounts, ChecklistSummary, FlaggedStep)
- Traffic-light severity: red (missing data/signatures/blocking exceptions), amber (changes, review-required, non-blocking exceptions, incomplete steps), green (all clear)
- API endpoint now returns `401` for unauthenticated access and fail-closed `404` for unauthorized batch access
- Step signature admin is immutable: add/change/delete are disabled in Django admin
- 54 review-summary tests pass, including auth contract and blocking vs non-blocking exception scenarios
- Full quality gate passes locally after installing frontend dependencies; backend suite passed with `PYTEST_ADDOPTS=--reuse-db` after clearing a stale local PostgreSQL test session

### File List

**New files:**
- `backend/apps/batches/__init__.py`
- `backend/apps/batches/apps.py`
- `backend/apps/batches/models.py`
- `backend/apps/batches/admin.py`
- `backend/apps/batches/migrations/__init__.py`
- `backend/apps/batches/migrations/0001_initial.py`
- `backend/apps/reviews/__init__.py`
- `backend/apps/reviews/apps.py`
- `backend/apps/reviews/models.py`
- `backend/apps/reviews/admin.py`
- `backend/apps/reviews/api/__init__.py`
- `backend/apps/reviews/api/serializers.py`
- `backend/apps/reviews/api/views.py`
- `backend/apps/reviews/api/urls.py`
- `backend/apps/reviews/domain/__init__.py`
- `backend/apps/reviews/domain/review_summary.py`
- `backend/apps/reviews/selectors/__init__.py`
- `backend/apps/reviews/selectors/review_summary.py`
- `backend/apps/reviews/tests/__init__.py`
- `backend/apps/reviews/tests/test_review_summary_domain.py`
- `backend/apps/reviews/tests/test_review_summary_selectors.py`
- `backend/apps/reviews/tests/test_review_summary_api.py`
- `backend/apps/reviews/migrations/__init__.py`
- `backend/apps/reviews/migrations/0001_initial.py`

**Modified files:**
- `backend/config/settings/base.py` (added batches + reviews to INSTALLED_APPS)
- `backend/shared/api/urls.py` (added reviews URL include)

## Change Log

- 2026-03-13: Implemented Story 5.1 — Created reviews app with review summary endpoint (GET /api/v1/batches/{id}/review-summary), domain logic for completeness evaluation and traffic-light severity, and stub batches models for prerequisite dependencies. Added 44 tests covering domain logic, selector queries, and API integration.
- 2026-03-13: Addressed code-review findings — corrected auth/error semantics (`401` unauthenticated, fail-closed `404` unauthorized), distinguished blocking vs non-blocking exceptions in severity derivation, added review-required support, and made signature admin records immutable.
