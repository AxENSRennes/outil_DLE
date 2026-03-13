# Story 2.1: Create the MMR and Draft Version Lifecycle Baseline

Status: review

## Story

As an internal configurator,
I want to create a master manufacturing record and open a draft version for it,
So that template work starts in a governed structure instead of ad hoc documents or uncontrolled edits.

## Acceptance Criteria

1. **Given** a configurator needs to prepare a new dossier workflow
   **When** they create a new MMR
   **Then** the system stores a master template record with its core identifying information
   **And** that record can own multiple governed versions over time.

2. **Given** template changes must be controlled from the start
   **When** a configurator creates a working version for an MMR
   **Then** the system creates that version in a draft state
   **And** the version is clearly linked to its parent MMR.

3. **Given** approved history must never be overwritten
   **When** a configurator starts a new version for an existing MMR
   **Then** the system creates a separate version record rather than mutating a prior governed version
   **And** earlier versions remain historically intact.

4. **Given** later stories will add step definitions, fields, and activation behavior
   **When** this story is implemented
   **Then** the draft version lifecycle is available as a minimal governed backbone
   **And** no step structure, field schema, or activation workflow is required yet.

5. **Given** multiple epics and stories will later depend on trusted template identity
   **When** this story is completed
   **Then** template and version identifiers are stable and usable by later stories
   **And** they establish the canonical foundation for activation and batch instantiation.

## Tasks / Subtasks

- [x] Task 1: Create Product model in `backend/apps/sites/` (AC: #1)
  - [x] 1.1 Add `Product` model: site FK (PROTECT), name, code, family, format_label, is_active, timestamps
  - [x] 1.2 Add unique constraint `(site, code)` at DB level
  - [x] 1.3 Add `ProductAdmin` with `has_delete_permission=False`, search_fields, list_filter
  - [x] 1.4 Create migration (additive only)
- [x] Task 2: Create MMR model and app structure in `backend/apps/mmr/` (AC: #1, #5)
  - [x] 2.1 Create app skeleton: `__init__.py`, `apps.py`, `models.py`, `admin.py`, `api/`, `domain/`, `selectors/`, `tests/`
  - [x] 2.2 Add `MMR` model: site FK (PROTECT), product FK (PROTECT), name, code, description, is_active, timestamps
  - [x] 2.3 Add unique constraint `(site, code)` at DB level
  - [x] 2.4 Register app in `INSTALLED_APPS`
  - [x] 2.5 Create migration
- [x] Task 3: Create MMRVersion model with draft lifecycle (AC: #2, #3, #4)
  - [x] 3.1 Add `MMRVersionStatus` TextChoices: `draft`, `active`, `retired`
  - [x] 3.2 Add `MMRVersion` model: mmr FK (PROTECT), version_number, status (default=draft), schema_json (default=dict), change_summary, created_by FK (PROTECT), activated_by FK (nullable, PROTECT), activated_at (nullable), timestamps
  - [x] 3.3 Add unique constraint `(mmr, version_number)` at DB level
  - [x] 3.4 Add ordering by `-version_number`
  - [x] 3.5 Create migration
- [x] Task 4: Create domain services in `backend/apps/mmr/domain/` (AC: #1, #2, #3)
  - [x] 4.1 `mmr_service.py`: `create_mmr()` — validates uniqueness, creates MMR, records audit event
  - [x] 4.2 `version_lifecycle.py`: `create_draft_version()` — auto-increments version_number from highest existing, creates version in draft status, records audit event
  - [x] 4.3 Ensure new version creation never mutates prior versions (immutability guarantee)
- [x] Task 5: Create API endpoints in `backend/apps/mmr/api/` (AC: #1, #2, #3)
  - [x] 5.1 Serializers: `MMRCreateSerializer`, `MMRDetailSerializer`, `MMRListSerializer`, `MMRVersionCreateSerializer`, `MMRVersionDetailSerializer`, `MMRVersionListSerializer`
  - [x] 5.2 Views: `MMRListCreateView`, `MMRDetailView`, `MMRVersionListCreateView`, `MMRVersionDetailView` — nested under MMR
  - [x] 5.3 Permissions: restrict to `internal_configurator` role using `SiteScopedRolePermission`
  - [x] 5.4 Register routes under `/api/v1/mmrs/` and `/api/v1/mmrs/{mmr_id}/versions/`
  - [x] 5.5 Add `@extend_schema` decorators for OpenAPI docs
- [x] Task 6: Create Django admin (AC: #1, #2)
  - [x] 6.1 `MMRAdmin`: list_display, search_fields, list_filter, `has_delete_permission=False`
  - [x] 6.2 `MMRVersionAdmin`: list_display, search_fields, list_filter, `has_delete_permission=False`, `readonly_fields` for activated_by/activated_at (not editable), schema_json as readonly
- [x] Task 7: Audit event integration (AC: #1, #2, #3)
  - [x] 7.1 Add new `AuditEventType` entries: `MMR_CREATED`, `MMR_VERSION_CREATED`
  - [x] 7.2 Call `record_audit_event()` in domain services with actor, site, metadata
- [x] Task 8: Write tests (AC: #1-#5)
  - [x] 8.1 Model tests: creation, uniqueness constraints, FK protection, version auto-increment
  - [x] 8.2 Domain tests: `create_mmr()` happy path + duplicate code rejection, `create_draft_version()` happy path + auto-increment + immutability of prior versions
  - [x] 8.3 API tests: CRUD operations, RBAC enforcement (configurator allowed, operator denied), site-scoping, unauthenticated denial
  - [x] 8.4 Admin tests: read-only protections verified
  - [x] 8.5 Audit tests: events recorded with correct metadata for MMR and version creation
- [x] Task 9: Run `make check` and fix any issues

## Dev Notes

### Domain Model Design

**Product** (in `backend/apps/sites/models.py` — site-scoped entity):
```python
class Product(TimestampedModel):
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    family = models.CharField(max_length=255, blank=True)
    format_label = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    # UniqueConstraint(fields=["site", "code"], name="uniq_product_code_per_site")
```

**MMR** (in `backend/apps/mmr/models.py`):
```python
class MMR(TimestampedModel):
    site = models.ForeignKey("sites.Site", on_delete=models.PROTECT, related_name="mmrs")
    product = models.ForeignKey("sites.Product", on_delete=models.PROTECT, related_name="mmrs")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    # UniqueConstraint(fields=["site", "code"], name="uniq_mmr_code_per_site")
```

**MMRVersion** (in `backend/apps/mmr/models.py`):
```python
class MMRVersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"      # Used by story 2.4
    RETIRED = "retired", "Retired"   # Used by story 2.4

class MMRVersion(TimestampedModel):
    mmr = models.ForeignKey(MMR, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=MMRVersionStatus.choices, default=MMRVersionStatus.DRAFT)
    schema_json = models.JSONField(default=dict, blank=True)  # Populated in stories 2.2/2.3
    change_summary = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_mmr_versions")
    activated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="activated_mmr_versions", null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    # UniqueConstraint(fields=["mmr", "version_number"], name="uniq_mmr_version_number")
    # ordering = ["-version_number"]
```

Reference model: `_bmad-output/implementation-artifacts/django_models_v1.py`
Reference schema: `_bmad-output/implementation-artifacts/mmr-version-schema-minimal.json`
Reference example: `_bmad-output/implementation-artifacts/mmr-version-example.json`

### Key Scope Boundaries

**IN scope for this story:**
- MMR CRUD (create, read, list)
- MMRVersion creation in draft state
- Auto-increment version_number per MMR
- Product model as dependency
- RBAC: internal_configurator only
- Audit events for creation actions
- API endpoints + Django admin
- Immutability guarantee: creating a new version never mutates prior versions

**OUT of scope (later stories):**
- Step definitions within a version (Story 2.2)
- Field schemas and signature checkpoints (Story 2.3)
- Version activation/retirement lifecycle transitions (Story 2.4)
- Batch instantiation from active version (Story 2.5)
- `schema_json` content validation against the JSON schema — for this story, `schema_json` defaults to `{}` and is populated by later stories
- MMR update/delete operations (update is allowed for name/description only; delete is intentionally blocked)
- Frontend template governance UI (backend-only for this baseline)

### Version Number Auto-Increment Logic

When creating a new draft version for an MMR:
1. Query `MMRVersion.objects.filter(mmr=mmr).aggregate(Max("version_number"))`
2. New version_number = max + 1 (or 1 if no versions exist)
3. Create with `status=draft`
4. This must be atomic to prevent race conditions (use `select_for_update` on MMR)

### Immutability Invariant

The domain service MUST guarantee:
- `create_draft_version()` creates a NEW row; it never updates an existing version's status, content, or metadata
- All prior versions remain unchanged after creating a new version
- Test this explicitly: create version 1, create version 2, assert version 1 is unchanged

### TimestampedModel Base Class

The reference models define a `TimestampedModel` abstract base. Check if it already exists in `backend/shared/database/` or create it there:
```python
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
```
Reuse this for Product, MMR, and MMRVersion. Also check if existing models (Site, SiteRoleAssignment, AuditEvent) already have timestamps — if they use raw fields instead of a base class, adopt the same pattern for consistency.

### Project Structure Notes

**New files to create:**
```
backend/apps/mmr/
├── __init__.py
├── apps.py              # MmrConfig
├── models.py            # MMR, MMRVersion, MMRVersionStatus
├── admin.py             # MMRAdmin, MMRVersionAdmin
├── api/
│   ├── __init__.py
│   ├── serializers.py   # Request/response serializers
│   ├── views.py         # ViewSets for MMR and MMRVersion
│   └── urls.py          # URL patterns
├── domain/
│   ├── __init__.py
│   ├── mmr_service.py   # create_mmr()
│   └── version_lifecycle.py  # create_draft_version()
├── selectors/
│   ├── __init__.py
│   └── mmr_queries.py   # List/detail read queries
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_domain.py
│   ├── test_api.py
│   └── helpers.py       # Test fixtures/helpers
└── migrations/
    └── __init__.py
```

**Files to modify:**
- `backend/apps/sites/models.py` — Add `Product` model
- `backend/apps/sites/admin.py` — Add `ProductAdmin`
- `backend/apps/audit/models.py` — Add new `AuditEventType` entries
- `backend/config/settings/base.py` — Add `"apps.mmr"` to `INSTALLED_APPS`
- `backend/shared/api/urls.py` — Mount MMR API routes

**Alignment with architecture:**
- App location matches architecture spec: `backend/apps/mmr/` [Source: architecture.md#Code-Structure]
- Internal structure follows `api/`, `domain/`, `selectors/`, `tests/` pattern [Source: architecture.md#Backend-Organization]
- Domain logic stays in `domain/`, not in serializers or views [Source: architecture.md#Service-Boundaries]

### API Design

**Endpoints:**
```
POST   /api/v1/mmrs/                        → Create MMR
GET    /api/v1/mmrs/                         → List MMRs (site-filtered)
GET    /api/v1/mmrs/{id}/                    → MMR detail with version summary
POST   /api/v1/mmrs/{id}/versions/           → Create new draft version
GET    /api/v1/mmrs/{id}/versions/           → List versions for MMR
GET    /api/v1/mmrs/{id}/versions/{vid}/     → Version detail
```

**Request/response conventions:**
- JSON payload fields use `snake_case` [Source: architecture.md#API-Naming]
- Problem-details error format for errors [Source: architecture.md#Error-Handling]
- Use `@extend_schema` for OpenAPI generation via drf-spectacular [Source: architecture.md#Documentation]
- CSRF protection on all POST endpoints [Source: story 1.2 learnings]
- Session authentication only (no Basic auth) [Source: story 1.2 learnings]

**Example create MMR request:**
```json
{
  "site_id": 1,
  "product_id": 1,
  "name": "Chateau-Renard - Parfum 100mL pilot",
  "code": "CHR-PARFUM-100ML-PILOT",
  "description": "Template pilote..."
}
```

**Example create version request:**
```json
{
  "change_summary": "Initial draft version"
}
```
The `version_number` is auto-assigned; `created_by` comes from `request.user`; `status` is always `draft`.

### RBAC Requirements

- Only users with `internal_configurator` role on the relevant site can create/view MMR and versions
- Use `SiteScopedRolePermission` from `backend/shared/permissions/site_roles.py` [Source: story 1.2]
- Site is resolved from:
  - Request body `site_id` on MMR creation
  - Object's `site` FK on retrieve/list (object-level permission)
- Operators, production reviewers, quality reviewers: DENIED for all MMR endpoints
- Unauthenticated users: DENIED

### Admin Requirements (CLAUDE.md Rules)

- `MMRAdmin`: `has_delete_permission` returns `False`
- `MMRVersionAdmin`: `has_delete_permission` returns `False`; `schema_json` in `readonly_fields`; `activated_by` and `activated_at` in `readonly_fields` (not editable from admin — activation is a domain action)
- `ProductAdmin`: `has_delete_permission` returns `False`
- Follow pattern from existing `SiteAdmin`, `AuditEventAdmin` [Source: backend/apps/sites/admin.py, backend/apps/audit/admin.py]

### Audit Events

Add to `AuditEventType` in `backend/apps/audit/models.py`:
```python
MMR_CREATED = "mmr_created", "MMR Created"
MMR_VERSION_CREATED = "mmr_version_created", "MMR Version Created"
```

Call `record_audit_event()` with:
- `actor`: request.user
- `site`: MMR's site
- `event_type`: appropriate type
- `metadata`: `{"mmr_code": ..., "mmr_name": ...}` or `{"mmr_code": ..., "version_number": ...}`

Follow the sanitization pattern from `backend/apps/audit/services.py` [Source: story 1.3].

### Testing Requirements

**Model tests (`test_models.py`):**
- Product creation with site FK
- Product uniqueness constraint `(site, code)` raises IntegrityError
- MMR creation with site + product FKs
- MMR uniqueness constraint `(site, code)` raises IntegrityError
- MMRVersion creation with mmr FK in draft status
- MMRVersion uniqueness constraint `(mmr, version_number)` raises IntegrityError
- FK PROTECT: deleting site/product/mmr/user with related records raises ProtectedError

**Domain tests (`test_domain.py`):**
- `create_mmr()`: creates MMR with correct fields, returns MMR instance
- `create_mmr()`: duplicate code on same site raises validation error
- `create_draft_version()`: first version gets version_number=1
- `create_draft_version()`: subsequent version auto-increments from max
- `create_draft_version()`: new version does NOT mutate prior versions (immutability test)
- `create_draft_version()`: status is always `draft`
- `create_draft_version()`: `created_by` is set to the acting user

**API tests (`test_api.py`):**
- POST `/api/v1/mmrs/` as configurator: 201 with correct response
- POST `/api/v1/mmrs/` as operator: 403 denied
- POST `/api/v1/mmrs/` unauthenticated: 403 denied
- GET `/api/v1/mmrs/` returns only MMRs for user's site
- POST `/api/v1/mmrs/{id}/versions/` creates draft version with auto-incremented number
- GET `/api/v1/mmrs/{id}/versions/` returns versions ordered by `-version_number`
- CSRF enforcement on POST endpoints
- Problem-details error format on validation errors

**Test patterns to follow:**
- Use `@pytest.mark.django_db` decorator
- Use CSRF-enabled client from `authz/tests/helpers.py`
- Create test fixtures directly with model `.objects.create()` (no factory-boy unless already installed)
- Follow patterns from `backend/apps/authz/tests/` [Source: story 1.2, 1.3]

### Previous Story Intelligence

**From Story 1.1 (Foundation):**
- Virtual environment: always use `/home/axel/wsl_venv/bin/python`
- PostgreSQL 17.x running on `127.0.0.1:65432` via Docker Compose
- API namespace: `/api/v1/` — mount new routes in `backend/shared/api/urls.py`
- Problem-details exception handler already configured in DRF settings

**From Story 1.2 (Roles & Access):**
- `SiteScopedRolePermission` supports object-level permission via `has_object_permission()`
- DRF locked to `SessionAuthentication` only — do NOT add BasicAuth
- Explicit CSRF protection on all POST endpoints
- `SiteRole.INTERNAL_CONFIGURATOR` is the role enum value to check
- Test both correct-role AND wrong-role paths

**From Story 1.3 (Workstation Auth):**
- Audit event recording via `record_audit_event()` in `backend/apps/audit/services.py`
- Metadata sanitization: never store secrets in audit metadata
- FK PROTECT on all audit-related foreign keys
- Admin immutability pattern: override `has_add/change/delete_permission`
- Fail-closed pattern: if audit write fails, consider rollback (applies to critical security ops; for MMR creation this is less critical but keep the pattern in mind)

**Review feedback patterns to avoid:**
- Don't forget CSRF on POST endpoints (caught in story 1.2 review)
- Don't rely on DRF defaults for auth classes (caught in story 1.2 review)
- Enforce constraints at model AND DB level (caught in story 1.3 review)
- Test all RBAC paths including wrong-role and wrong-site (caught in story 1.2 review)

### Git Intelligence

Recent commits show Epic 1 is complete with hardened auth patterns:
- `bde7acc` Merge PR #5: workstation auth
- `a980fe1` Harden audit event typing and lock throttling
- `c70f8d2` Harden FK, admin delete, CSRF and add lock fail-closed test
- `600433f` Protect FK integrity and add IP to success events

Key patterns from commits: FK PROTECT, admin delete prevention, CSRF enforcement, audit event typing, IP metadata in audit events. Apply these same patterns to MMR models.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-2] — Epic 2 story definitions and acceptance criteria
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical-Stack] — Django 5.2, DRF, PostgreSQL 17.x, drf-spectacular 0.29
- [Source: _bmad-output/planning-artifacts/architecture.md#Database-Design] — Hybrid relational + JSONB, naming conventions, migration strategy
- [Source: _bmad-output/planning-artifacts/architecture.md#API-Design] — REST under /api/v1, snake_case, problem-details errors
- [Source: _bmad-output/planning-artifacts/architecture.md#Code-Structure] — backend/apps/mmr/ placement, api/domain/selectors pattern
- [Source: _bmad-output/planning-artifacts/architecture.md#Authorization] — Site-scoped RBAC, SiteScopedRolePermission
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey-5] — Configurator template management flow
- [Source: _bmad-output/implementation-artifacts/django_models_v1.py] — Reference model definitions for MMR, MMRVersion, Product
- [Source: _bmad-output/implementation-artifacts/mmr-version-schema-minimal.json] — JSON schema for MMRVersion.schema_json content
- [Source: _bmad-output/implementation-artifacts/mmr-version-example.json] — Example MMR version JSON payload
- [Source: _bmad-output/planning-artifacts/prd.md#FR1-FR8] — Template governance functional requirements
- [Source: backend/apps/authz/] — Existing RBAC patterns, permission classes, test helpers
- [Source: backend/apps/audit/services.py] — Audit event recording service
- [Source: backend/apps/sites/models.py] — Existing Site model to extend with Product
- [Source: CLAUDE.md] — Security rules: fail-closed, audit immutability, admin protections, trust boundaries

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

- Dev DB has inconsistent migration history (admin.0001_initial applied before authz.0001_initial). This is a pre-existing issue from Epic 1 and does not affect test execution (pytest creates a fresh test DB).
- Frontend `make check` targets fail due to missing `node_modules` (pre-existing, not related to this story which is backend-only).

### Completion Notes List

- Product model added to `backend/apps/sites/` with site FK (PROTECT), unique constraint `(site, code)`, and ProductAdmin with delete prevention.
- MMR app created at `backend/apps/mmr/` following `api/domain/selectors/tests` structure per architecture spec.
- MMR model with site + product FKs (PROTECT), unique constraint `(site, code)`.
- MMRVersion model with `MMRVersionStatus` (draft/active/retired), unique `(mmr, version_number)`, ordering `-version_number`, all FK fields using PROTECT.
- Domain services: `create_mmr()` validates uniqueness (raises ValueError on duplicate), `create_draft_version()` uses `select_for_update` for atomic auto-increment.
- Immutability guarantee tested: creating a new version never mutates prior versions.
- API views use `APIView` (not ViewSets) with `SiteScopedRolePermission`, CSRF on POST, `@extend_schema` for OpenAPI.
- Site-scoped RBAC: only `internal_configurator` can access MMR endpoints. Operators and unauthenticated users are denied (403).
- Cross-site isolation: configurator cannot create MMR on sites where they lack the role.
- Admin: MMRAdmin and MMRVersionAdmin with `has_delete_permission=False`, schema_json/activated_by/activated_at as readonly.
- Audit events: `MMR_CREATED` and `MMR_VERSION_CREATED` recorded with sanitized metadata.
- Existing models use raw `created_at`/`updated_at` fields (no abstract base class). Followed same pattern for consistency.
- All backend quality gates pass: ruff lint, mypy, 119 tests (0 regressions), bandit, pip-audit, architecture checks.

### Change Log

- 2026-03-13: Implemented Story 2.1 - MMR and draft version lifecycle baseline. All 9 tasks completed. 119 tests passing (52 new).

### File List

**New files:**
- backend/apps/mmr/__init__.py
- backend/apps/mmr/apps.py
- backend/apps/mmr/models.py
- backend/apps/mmr/admin.py
- backend/apps/mmr/api/__init__.py
- backend/apps/mmr/api/serializers.py
- backend/apps/mmr/api/views.py
- backend/apps/mmr/api/urls.py
- backend/apps/mmr/domain/__init__.py
- backend/apps/mmr/domain/mmr_service.py
- backend/apps/mmr/domain/version_lifecycle.py
- backend/apps/mmr/selectors/__init__.py
- backend/apps/mmr/tests/__init__.py
- backend/apps/mmr/tests/test_models.py
- backend/apps/mmr/tests/test_domain.py
- backend/apps/mmr/tests/test_api.py
- backend/apps/mmr/tests/test_admin.py
- backend/apps/mmr/migrations/__init__.py
- backend/apps/mmr/migrations/0001_initial_mmr_models.py
- backend/apps/sites/migrations/0002_add_product_model.py

**Modified files:**
- backend/apps/sites/models.py (added Product model)
- backend/apps/sites/admin.py (added ProductAdmin)
- backend/apps/sites/tests/test_models.py (added Product model tests)
- backend/apps/audit/models.py (added MMR_CREATED, MMR_VERSION_CREATED event types)
- backend/config/settings/base.py (added apps.mmr to INSTALLED_APPS)
- backend/shared/api/urls.py (mounted MMR API routes)
