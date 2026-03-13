# Story 2.2: Define Ordered Template Steps and Step-Level Guidance

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an internal configurator,
I want to define the ordered steps of a template and attach operational guidance to each step,
So that operators later execute a structured dossier flow instead of a flat uncontrolled form.

## Acceptance Criteria

1. **Given** a draft template version already exists
   **When** a configurator adds step definitions to that version
   **Then** the system stores an ordered list of execution steps for that template version
   **And** the order is explicit and stable for later execution use.

2. **Given** operators need contextual support while working
   **When** a configurator edits a template step
   **Then** they can associate that step with instructions, references, or supporting context
   **And** that guidance remains attached to the specific step definition.

3. **Given** template structure must remain governable
   **When** a configurator reorders, adds, or removes draft steps
   **Then** the system updates only the current draft version structure
   **And** no previously governed version is modified.

4. **Given** later stories will add fields and signature checkpoints
   **When** this story is completed
   **Then** step structure and guidance are available as a standalone capability
   **And** field schemas and signature definitions are still out of scope for this story.

5. **Given** later execution stories will rely on a predictable template sequence
   **When** this story is reviewed
   **Then** the step model is sufficient to drive future step-by-step execution ordering
   **And** no future story inside this epic is required to make the ordered step list itself valid.

## Tasks / Subtasks

- [x] Task 1: Create domain service `step_management.py` (AC: #1, #2, #3)
  - [x] 1.1 Create `backend/apps/mmr/domain/step_management.py`
  - [x] 1.2 Implement `add_step(version, step_data, actor)` — validate draft status, auto-init `schema_json` header on first step, append step key to `stepOrder`, add step definition to `steps` map with auto-injected defaults (`"fields": []`, `"signaturePolicy": {"required": false, "meaning": "performed_by"}`), record audit event
  - [x] 1.3 Implement `update_step(version, step_key, step_data, actor)` — validate draft status, validate step exists, merge updated properties, record audit event
  - [x] 1.4 Implement `remove_step(version, step_key, actor)` — validate draft status, remove from `stepOrder` and `steps`, record audit event
  - [x] 1.5 Implement `reorder_steps(version, step_order, actor)` — validate draft status, validate all keys exist and set matches, replace `stepOrder`, record audit event
  - [x] 1.6 Implement `get_steps(version)` — return step list ordered by `stepOrder`
  - [x] 1.7 Implement `get_step(version, step_key)` — return single step definition
  - [x] 1.8 Implement `_ensure_schema_initialized(version)` — auto-populate schema header from MMR/Product if `schema_json` is empty
  - [x] 1.9 All mutating operations use `select_for_update()` on MMRVersion to prevent concurrent edit conflicts
  - [x] 1.10 All mutating operations reject non-draft versions with `ValueError`
- [x] Task 2: Add audit event types (AC: #1, #2, #3)
  - [x] 2.1 Add to `AuditEventType` in `backend/apps/audit/models.py`: `MMR_VERSION_STEP_ADDED`, `MMR_VERSION_STEP_UPDATED`, `MMR_VERSION_STEP_REMOVED`, `MMR_VERSION_STEPS_REORDERED`
  - [x] 2.2 Create and apply migration for new event types
- [x] Task 3: Create API serializers for step operations (AC: #1, #2)
  - [x] 3.1 `StepCreateSerializer` — input: key, title, kind, instructions (optional), attachmentsPolicy (optional), required (optional), applicability (optional), repeatPolicy (optional), blockingPolicy (optional)
  - [x] 3.2 `StepUpdateSerializer` — same fields as create but all optional (partial update)
  - [x] 3.3 `StepReorderSerializer` — input: step_order (list of step keys)
  - [x] 3.4 `StepDetailSerializer` — output: all step properties including defaulted fields and signaturePolicy
  - [x] 3.5 `StepListSerializer` — output: key, title, kind, required (minimal for list)
  - [x] 3.6 Use typed nested serializers for `applicability`, `repeatPolicy`, `blockingPolicy`, `attachmentsPolicy` (never raw DictField)
- [x] Task 4: Create API views and URL routing (AC: #1, #2, #3)
  - [x] 4.1 `StepListCreateView` — GET list, POST add step at `/api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/`
  - [x] 4.2 `StepDetailView` — GET, PUT, DELETE at `/api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/{step_key}/`
  - [x] 4.3 `StepReorderView` — POST at `/api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/reorder/`
  - [x] 4.4 All views require `IsAuthenticated` + `SiteScopedRolePermission` with `INTERNAL_CONFIGURATOR`
  - [x] 4.5 All views resolve site from parent MMR object (use `allow_object_level_site_resolve = True` + `get_site_for_object`)
  - [x] 4.6 Register URL patterns in `backend/apps/mmr/api/urls.py`
  - [x] 4.7 Add `@extend_schema` decorators for OpenAPI docs
- [x] Task 5: Update existing version detail serializer (AC: #5)
  - [x] 5.1 Add `step_count` computed field to `MMRVersionDetailSerializer`
  - [x] 5.2 Add `has_steps` boolean computed field to `MMRVersionListSerializer`
- [x] Task 6: Write tests (AC: #1-#5)
  - [x] 6.1 Domain tests: `test_step_management.py` — add/update/remove/reorder happy paths, draft-only enforcement, duplicate key rejection, reorder set mismatch rejection, schema auto-initialization, concurrent safety, audit events
  - [x] 6.2 API tests: `test_step_api.py` — all endpoints with RBAC (configurator allowed, operator/unauthenticated denied), CSRF on POST/PUT/DELETE, validation errors, problem-details format, draft-only enforcement via API
  - [x] 6.3 Serializer tests: validate enum constraints on `kind`, nested policy serializer shapes
- [x] Task 7: Run `make check` and fix any issues

## Dev Notes

### Design Overview

Steps live inside `MMRVersion.schema_json` (JSONB), not as separate database rows. The schema structure is defined by `_bmad-output/implementation-artifacts/mmr-version-schema-minimal.json`. This story adds CRUD operations on the `stepOrder` array and `steps` object within that JSON document.

**Why JSONB, not relational tables?** The architecture mandates JSONB for "versioned template definitions, field schemas, conditional rules" [Source: architecture.md#Data-Architecture]. Steps are part of the versioned template definition — they get frozen into batch snapshots (story 2.5) as a complete JSON document. Relational step rows would complicate snapshotting and version immutability.

### Schema JSON Structure After This Story

When a configurator adds steps to a draft version, `schema_json` evolves from `{}` to:

```json
{
  "schemaVersion": "v1",
  "templateCode": "CHR-PARFUM-100ML-PILOT",
  "templateName": "Chateau-Renard - Parfum 100mL pilot",
  "product": {
    "productCode": "PARFUM-100ML",
    "productName": "Parfum 100mL",
    "family": "Parfum",
    "formatLabel": "100mL"
  },
  "stepOrder": ["fabrication_bulk", "weighing", "packaging"],
  "steps": {
    "fabrication_bulk": {
      "key": "fabrication_bulk",
      "title": "Dossier de fabrication bulk",
      "kind": "manufacturing",
      "instructions": "Saisir et verifier les informations bulk...",
      "required": true,
      "blockingPolicy": {
        "blocksExecutionProgress": false,
        "blocksStepCompletion": true,
        "blocksSignature": true,
        "blocksPreQaHandoff": true
      },
      "fields": [],
      "signaturePolicy": { "required": false, "meaning": "performed_by" }
    }
  }
}
```

**Key rules:**
- `stepOrder` is the source of truth for execution ordering (array of step keys)
- `steps` is a map of step_key → step definition
- Every step key in `stepOrder` MUST exist in `steps` and vice versa (invariant)
- `fields` defaults to `[]` — populated by story 2.3
- `signaturePolicy` defaults to `{"required": false, "meaning": "performed_by"}` — configured by story 2.3
- The schema header (`schemaVersion`, `templateCode`, `templateName`, `product`) is auto-populated from the parent MMR + Product models on first step add

### Schema Auto-Initialization Logic

When the first step is added to a version with empty `schema_json`:

```python
def _ensure_schema_initialized(version: MMRVersion) -> dict:
    """Initialize schema_json header from parent MMR and Product if empty."""
    schema = version.schema_json
    if schema and "schemaVersion" in schema:
        return schema  # Already initialized

    mmr = version.mmr
    product = mmr.product
    return {
        "schemaVersion": "v1",
        "templateCode": mmr.code,
        "templateName": mmr.name,
        "product": {
            "productCode": product.code,
            "productName": product.name,
            "family": product.family,
            "formatLabel": product.format_label,
        },
        "stepOrder": [],
        "steps": {},
    }
```

**Note:** An empty `stepOrder: []` is valid during the draft phase. The JSON schema's `minItems: 1` constraint on `stepOrder` is only enforced at activation time (Story 2.4). During draft editing, partial/incomplete schema_json is expected.

### Step Properties Scope

**IN scope for this story (step-level):**
| Property | Type | Required | Description |
|---|---|---|---|
| `key` | string (1-100) | yes | Unique step identifier (snake_case slug) |
| `title` | string (1-255) | yes | Human-readable step name |
| `kind` | enum | yes | Step type (see valid values below) |
| `instructions` | string (max 10000) | no | Operational guidance text (FR4) |
| `attachmentsPolicy` | object | no | Supported attachment types (FR4) |
| `required` | boolean | no | Default true; whether step is required |
| `applicability` | object | no | Conditional applicability rules |
| `repeatPolicy` | object | no | Repeat cardinality (single, per_shift, etc.) |
| `blockingPolicy` | object | no | What this step blocks if incomplete |

**Valid `kind` values:**
`preparation`, `material_confirmation`, `weighing`, `manufacturing`, `pre_qa_review`, `in_process_control`, `bulk_handover`, `packaging`, `finished_product_control`, `review`

**OUT of scope (Story 2.3):**
- `fields` array → always `[]` in this story
- `signaturePolicy` configuration → always default `{"required": false, "meaning": "performed_by"}`
- `calculations` array (root-level)
- `releaseRules` object (root-level)

**OUT of scope (other stories):**
- `batchDefaults`, `contextDimensions` (root-level schema properties — deferred)
- Version activation/retirement (Story 2.4)
- Batch instantiation (Story 2.5)

### Nested Policy Serializer Shapes

**AttachmentsPolicySerializer:**
```python
class AttachmentsPolicySerializer(serializers.Serializer):
    supports_attachments = serializers.BooleanField(required=False, default=False)
    attachment_kinds = serializers.ListField(
        child=serializers.ChoiceField(choices=["checklist", "worksheet", "label_scan", "photo", "other"]),
        required=False, default=list,
    )
```

**ApplicabilitySerializer:**
```python
class ApplicabilitySerializer(serializers.Serializer):
    site_codes = serializers.ListField(child=serializers.CharField(max_length=100), required=False)
    line_codes = serializers.ListField(child=serializers.CharField(max_length=100), required=False)
    machine_codes = serializers.ListField(child=serializers.CharField(max_length=100), required=False)
    format_families = serializers.ListField(child=serializers.CharField(max_length=100), required=False)
    glitter_mode = serializers.ChoiceField(choices=["with_glitter", "without_glitter", "any"], required=False)
    when_not_applicable = serializers.ChoiceField(choices=["hidden", "mark_na"], required=False)
```

**RepeatPolicySerializer:**
```python
class RepeatPolicySerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["single", "per_shift", "per_team", "per_box", "per_event"], required=False)
    min_records = serializers.IntegerField(min_value=0, required=False)
    max_records = serializers.IntegerField(min_value=1, required=False)
```

**BlockingPolicySerializer:**
```python
class BlockingPolicySerializer(serializers.Serializer):
    blocks_execution_progress = serializers.BooleanField(required=False, default=False)
    blocks_step_completion = serializers.BooleanField(required=False, default=False)
    blocks_signature = serializers.BooleanField(required=False, default=False)
    blocks_pre_qa_handoff = serializers.BooleanField(required=False, default=False)
```

**CRITICAL: JSON field naming convention.** The `schema_json` stores camelCase keys (matching the JSON schema definition: `stepOrder`, `templateCode`, `signaturePolicy`, etc.). API request/response payloads use `snake_case` per CLAUDE.md. The serializer layer MUST translate between these:
- API input `snake_case` → domain service → stored as `camelCase` in schema_json
- schema_json `camelCase` → domain service → API output `snake_case`

Use a helper function to convert between the two:
```python
def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])

def to_snake_case(camel_str: str) -> str:
    import re
    return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_str).lower()
```

### Domain Service Design

**File:** `backend/apps/mmr/domain/step_management.py`

All mutating operations follow the same pattern:
1. Acquire row lock: `MMRVersion.objects.select_for_update().get(pk=version.pk)`
2. Validate `version.status == MMRVersionStatus.DRAFT` → `ValueError` if not
3. Ensure schema is initialized (auto-populate from MMR/Product if empty)
4. Perform the step mutation on `schema_json`
5. Save the version with `version.save(update_fields=["schema_json", "updated_at"])`
6. Record audit event with `record_audit_event()`

**Function signatures:**

```python
def add_step(*, version: MMRVersion, step_data: dict, actor: Any) -> dict:
    """Add step to draft version. step_data has snake_case keys from serializer.
    Auto-injects 'fields': [] and 'signaturePolicy': {required: false, meaning: performed_by}
    since these are out of scope for this story but required by the JSON schema."""

def update_step(*, version: MMRVersion, step_key: str, step_data: dict, actor: Any) -> dict:
    """Update existing step. step_data is partial (only changed fields)."""

def remove_step(*, version: MMRVersion, step_key: str, actor: Any) -> None:
    """Remove step from draft version."""

def reorder_steps(*, version: MMRVersion, step_order: list[str], actor: Any) -> list[str]:
    """Replace stepOrder. Must contain exactly the same set of keys."""

def get_steps(*, version: MMRVersion) -> list[dict]:
    """Return steps ordered by stepOrder. Output uses snake_case keys."""

def get_step(*, version: MMRVersion, step_key: str) -> dict:
    """Return single step. Raises ValueError if not found. Output uses snake_case keys."""
```

**Business invariants to enforce:**
- Step `key` must be unique within the version (reject duplicates in `add_step`)
- Step `key` must match `^[a-z][a-z0-9_]*$` pattern (snake_case identifier)
- `stepOrder` must be a permutation of `steps.keys()` at all times (consistency invariant)
- Only draft versions can be modified (reject active/retired with clear error message)
- `kind` must be one of the valid enum values from the JSON schema

### API Endpoint Design

**Endpoints:**
```
POST   /api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/            → Add step
GET    /api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/            → List steps (ordered)
GET    /api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/{step_key}/ → Step detail
PUT    /api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/{step_key}/ → Update step
DELETE /api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/{step_key}/ → Remove step
POST   /api/v1/mmrs/{mmr_id}/versions/{version_id}/steps/reorder/    → Reorder steps
```

**View implementation pattern (follow existing views in `backend/apps/mmr/api/views.py`):**

```python
class StepListCreateView(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated, SiteScopedRolePermission)
    required_site_roles = (SiteRole.INTERNAL_CONFIGURATOR,)
    allow_object_level_site_resolve = True

    def get_site_for_object(self, obj):
        return obj.mmr.site  # obj is MMRVersion

    def _get_version(self, mmr_id: int, version_id: int) -> MMRVersion:
        version = MMRVersion.objects.select_related("mmr", "mmr__site", "mmr__product").filter(
            pk=version_id, mmr_id=mmr_id
        ).first()
        if not version:
            raise NotFound(...)
        self.check_object_permissions(self.request, version)
        return version
```

**Error responses (problem-details format):**
- 400: Invalid step data (validation errors)
- 403: Insufficient role / wrong site
- 404: MMR, version, or step not found
- 409: Duplicate step key, or non-draft version modification attempt

Use 409 for domain rule violations (not-draft, duplicate key) to distinguish from validation errors (400).

**Request/response examples:**

Create step request (POST):
```json
{
  "key": "fabrication_bulk",
  "title": "Dossier de fabrication bulk",
  "kind": "manufacturing",
  "instructions": "Saisir et verifier les informations bulk...",
  "blocking_policy": {
    "blocks_step_completion": true,
    "blocks_signature": true,
    "blocks_pre_qa_handoff": true
  }
}
```

Step detail response:
```json
{
  "key": "fabrication_bulk",
  "title": "Dossier de fabrication bulk",
  "kind": "manufacturing",
  "instructions": "Saisir et verifier les informations bulk...",
  "required": true,
  "attachments_policy": null,
  "applicability": null,
  "repeat_policy": null,
  "blocking_policy": {
    "blocks_execution_progress": false,
    "blocks_step_completion": true,
    "blocks_signature": true,
    "blocks_pre_qa_handoff": true
  },
  "signature_policy": {
    "required": false,
    "meaning": "performed_by"
  },
  "fields": []
}
```

Step list response:
```json
[
  { "key": "fabrication_bulk", "title": "Dossier de fabrication bulk", "kind": "manufacturing", "required": true },
  { "key": "weighing", "title": "Fichier de pesee", "kind": "weighing", "required": true }
]
```

Reorder request (POST):
```json
{
  "step_order": ["weighing", "fabrication_bulk", "packaging"]
}
```

### URL Registration

Add to `backend/apps/mmr/api/urls.py` (extend existing patterns):

```python
# Existing patterns for MMR and Version endpoints...

# Step endpoints (nested under version)
path("<int:mmr_id>/versions/<int:version_id>/steps/", StepListCreateView.as_view(), name="step-list-create"),
path("<int:mmr_id>/versions/<int:version_id>/steps/reorder/", StepReorderView.as_view(), name="step-reorder"),
path("<int:mmr_id>/versions/<int:version_id>/steps/<str:step_key>/", StepDetailView.as_view(), name="step-detail"),
```

**URL ordering matters:** The `reorder/` path must come before `<str:step_key>/` to avoid "reorder" being captured as a step key.

### Audit Events

Add to `AuditEventType` in `backend/apps/audit/models.py`:
```python
MMR_VERSION_STEP_ADDED = "mmr_version_step_added", "MMR Version Step Added"
MMR_VERSION_STEP_UPDATED = "mmr_version_step_updated", "MMR Version Step Updated"
MMR_VERSION_STEP_REMOVED = "mmr_version_step_removed", "MMR Version Step Removed"
MMR_VERSION_STEPS_REORDERED = "mmr_version_steps_reordered", "MMR Version Steps Reordered"
```

**Audit metadata pattern:**
```python
record_audit_event(
    AuditEventType.MMR_VERSION_STEP_ADDED,
    actor=actor,
    site=version.mmr.site,
    metadata={
        "mmr_id": version.mmr.pk,
        "mmr_code": version.mmr.code,
        "version_id": version.pk,
        "version_number": version.version_number,
        "step_key": step_key,
    },
)
```

Follow the existing pattern in `backend/apps/mmr/domain/version_lifecycle.py` for audit event calls.

### Key Scope Boundaries

**IN scope for this story:**
- Step CRUD operations (add, update, remove) on draft versions only
- Step reordering within a draft version
- Step-level guidance: `instructions` (text) and `attachmentsPolicy` (attachment types)
- Step metadata: `kind`, `required`, `applicability`, `repeatPolicy`, `blockingPolicy`
- Schema auto-initialization from parent MMR/Product
- Audit events for all step mutations
- API endpoints with RBAC (internal_configurator only)
- `step_count` and `has_steps` on version serializers
- Draft-only enforcement (reject mutations on active/retired versions)

**OUT of scope (later stories):**
- Step field definitions (`fields` array) — Story 2.3
- Signature policy configuration — Story 2.3
- Root-level schema properties (`calculations`, `releaseRules`, `batchDefaults`, `contextDimensions`) — deferred or Story 2.3
- Version activation/retirement — Story 2.4
- Batch instantiation from template snapshot — Story 2.5
- Full JSON schema validation of complete `schema_json` — Story 2.4 (at activation time)
- Frontend template governance UI — future epic

### Project Structure Notes

**New files to create:**
```
backend/apps/mmr/domain/step_management.py     # Step CRUD domain services
backend/apps/mmr/tests/test_step_management.py  # Domain tests for step operations
backend/apps/mmr/tests/test_step_api.py         # API tests for step endpoints
```

**Files to modify:**
- `backend/apps/mmr/api/serializers.py` — Add step serializers + nested policy serializers + version serializer updates
- `backend/apps/mmr/api/views.py` — Add StepListCreateView, StepDetailView, StepReorderView
- `backend/apps/mmr/api/urls.py` — Register step URL patterns
- `backend/apps/audit/models.py` — Add 4 new AuditEventType entries
- `backend/apps/audit/migrations/` — New migration for audit event types

**Files NOT to modify (no changes needed):**
- `backend/apps/mmr/models.py` — No model changes; steps live in existing `schema_json` JSONB field
- `backend/config/settings/base.py` — No settings changes needed
- `backend/shared/api/urls.py` — MMR routes already mounted

### Testing Requirements

**Domain tests (`test_step_management.py`):**
- `add_step()`: adds step to empty schema_json, auto-initializes schema header
- `add_step()`: adds second step, appends to existing stepOrder
- `add_step()`: duplicate key raises `ValueError`
- `add_step()`: invalid kind value raises `ValueError`
- `add_step()`: non-draft version raises `ValueError`
- `add_step()`: records `MMR_VERSION_STEP_ADDED` audit event with correct metadata
- `update_step()`: updates title, instructions, blockingPolicy on existing step
- `update_step()`: partial update — only changed fields are modified
- `update_step()`: nonexistent step key raises `ValueError`
- `update_step()`: non-draft version raises `ValueError`
- `update_step()`: records `MMR_VERSION_STEP_UPDATED` audit event
- `remove_step()`: removes step from both `stepOrder` and `steps`
- `remove_step()`: nonexistent step key raises `ValueError`
- `remove_step()`: non-draft version raises `ValueError`
- `remove_step()`: records `MMR_VERSION_STEP_REMOVED` audit event
- `reorder_steps()`: reorders stepOrder with valid permutation
- `reorder_steps()`: mismatched set (extra/missing keys) raises `ValueError`
- `reorder_steps()`: non-draft version raises `ValueError`
- `reorder_steps()`: records `MMR_VERSION_STEPS_REORDERED` audit event
- `get_steps()`: returns steps in stepOrder order
- `get_step()`: returns single step by key
- `get_step()`: nonexistent step raises `ValueError`
- Schema immutability: adding step to version A does NOT affect version B's schema_json

**API tests (`test_step_api.py`):**
- POST `/steps/` as configurator → 201 with step detail
- POST `/steps/` as operator → 403
- POST `/steps/` unauthenticated → 403
- POST `/steps/` with CSRF token enforcement
- POST `/steps/` with invalid kind → 400 validation error
- POST `/steps/` with duplicate key → 409
- POST `/steps/` on non-draft version → 409
- GET `/steps/` returns ordered step list
- GET `/steps/{key}/` returns step detail with all properties
- GET `/steps/{key}/` with nonexistent key → 404
- PUT `/steps/{key}/` partial update → 200 with updated step
- PUT `/steps/{key}/` with CSRF token enforcement
- PUT `/steps/{key}/` on non-draft version → 409
- DELETE `/steps/{key}/` → 204
- DELETE `/steps/{key}/` with CSRF token enforcement
- DELETE `/steps/{key}/` on non-draft version → 409
- POST `/steps/reorder/` with valid order → 200
- POST `/steps/reorder/` with mismatched keys → 400
- POST `/steps/reorder/` with CSRF token enforcement
- Cross-site isolation: configurator on site A cannot manage steps on site B versions
- Problem-details error format on all error responses

**Test fixtures (extend existing in `test_api.py` or create shared helpers):**
```python
@pytest.fixture()
def draft_version(mmr, configurator):
    return MMRVersion.objects.create(
        mmr=mmr, version_number=1, status=MMRVersionStatus.DRAFT,
        created_by=configurator, schema_json={},
    )

@pytest.fixture()
def active_version(mmr, configurator):
    return MMRVersion.objects.create(
        mmr=mmr, version_number=2, status=MMRVersionStatus.ACTIVE,
        created_by=configurator, schema_json={},
    )

@pytest.fixture()
def sample_step_data():
    return {
        "key": "fabrication_bulk",
        "title": "Dossier de fabrication bulk",
        "kind": "manufacturing",
        "instructions": "Saisir et verifier les informations bulk.",
    }
```

**Test patterns to follow:**
- Use `@pytest.mark.django_db` decorator
- Use CSRF-enabled client from `authz/tests/helpers.py` (`csrf_client`, `post_json`)
- Follow assertion patterns from `backend/apps/mmr/tests/test_api.py` [Source: story 2.1]
- Test both correct-role AND wrong-role AND wrong-site paths

### Previous Story Intelligence

**From Story 2.1 (MMR Baseline):**
- `MMRVersion.schema_json` defaults to `dict` (empty `{}`) — this is the field we populate
- Domain services use `select_for_update()` for atomic operations — follow same pattern
- API views inherit from `APIView` (not ViewSets), use `SessionAuthentication` only
- `SiteScopedRolePermission` with `allow_object_level_site_resolve = True` for nested resources
- Problem-details error format: `{"type": "...", "title": "...", "detail": "..."}`
- Audit events use `record_audit_event()` from `backend/apps/audit/services.py`
- Admin uses `has_delete_permission = False` pattern
- Existing models use raw `created_at`/`updated_at` fields (no abstract base class)
- CSRF enforced on all POST endpoints
- 122 tests passing after story 2.1 — ensure zero regressions

**From Story 2.1 code review feedback:**
- RBAC leak fixed: version list was not checking site permissions → ensure step endpoints also resolve site from parent MMR
- Audit events wrapped in transactions → follow same pattern
- IntegrityError catch narrowed to specific constraint names → apply same discipline

**From Story 1.2/1.3 patterns:**
- `SiteRole.INTERNAL_CONFIGURATOR` is the role enum
- CSRF token obtained from login response, passed as `X-CSRFToken` header
- Test helpers: `csrf_client(user)` and `post_json(client, url, data, csrf_token)`

### Git Intelligence

Recent commits relevant to this story:
- `8b86e03` fix(mmr): enforce product.site == site invariant in create_mmr domain service
- `5f40a43` Use tuples in frozen dataclasses and expose missing serializer fields
- `8176147` fix(mmr): harden admin readonly fields, narrow IntegrityError catch, add Product verbose_name
- `b4539a4` fix(mmr): patch RBAC leak, wrap audit in transactions, add missing tests

Key patterns from commits: transaction wrapping for audit events, narrowed exception handling, hardened admin readonly, RBAC enforcement on all endpoints. Apply the same discipline to step management.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.2] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR2] — FR2: Structure a template into ordered execution steps
- [Source: _bmad-output/planning-artifacts/prd.md#FR4] — FR4: Associate instructions, references, and supporting context with a template step
- [Source: _bmad-output/implementation-artifacts/mmr-version-schema-minimal.json] — JSON schema for schema_json step structure
- [Source: _bmad-output/implementation-artifacts/mmr-version-example.json] — Complete example with 9 steps
- [Source: _bmad-output/planning-artifacts/architecture.md#Data-Architecture] — Hybrid relational + JSONB modeling strategy
- [Source: _bmad-output/planning-artifacts/architecture.md#API-Design] — REST under /api/v1, snake_case, problem-details errors
- [Source: _bmad-output/planning-artifacts/architecture.md#Code-Structure] — api/domain/selectors pattern
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md] — Step instructions shown in execution context
- [Source: _bmad-output/implementation-artifacts/2-1-create-the-mmr-and-draft-version-lifecycle-baseline.md] — Previous story patterns and learnings
- [Source: backend/apps/mmr/domain/version_lifecycle.py] — Existing domain service with select_for_update pattern
- [Source: backend/apps/mmr/api/views.py] — Existing API view patterns with RBAC
- [Source: backend/apps/mmr/api/serializers.py] — Existing serializer patterns
- [Source: backend/apps/audit/services.py] — record_audit_event() usage
- [Source: CLAUDE.md] — No generic DictField, security rules, API conventions, naming conventions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

- Created domain service `step_management.py` with full CRUD for steps within `MMRVersion.schema_json` (JSONB)
- Implemented snake_case ↔ camelCase conversion between API layer and schema_json storage
- Schema auto-initialization from parent MMR/Product on first step add
- All mutating operations use `select_for_update()` with `transaction.atomic()` for concurrency safety
- Draft-only enforcement on all mutations (reject active/retired with ValueError → 409)
- 4 new audit event types for step lifecycle tracking
- 6 REST endpoints with RBAC (INTERNAL_CONFIGURATOR only), CSRF enforcement, site-scoped permissions
- Typed nested serializers for all policy objects (no raw DictField per CLAUDE.md)
- `step_count` and `has_steps` computed fields on version serializers
- 55 new tests (30 domain + 25 API), 233 total passing, zero regressions
- `make check` green: ruff, mypy, bandit, pip-audit, architecture checks all pass

### Change Log

- 2026-03-13: Story 2.2 implementation complete — all 7 tasks done, all ACs satisfied

### File List

- backend/apps/mmr/domain/step_management.py (new)
- backend/apps/mmr/api/serializers.py (modified)
- backend/apps/mmr/api/views.py (modified)
- backend/apps/mmr/api/urls.py (modified)
- backend/apps/audit/models.py (modified)
- backend/apps/audit/migrations/0004_add_step_audit_event_types.py (new)
- backend/apps/mmr/tests/test_step_management.py (new)
- backend/apps/mmr/tests/test_step_api.py (new)
