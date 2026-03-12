# Story 1.2: Establish Site-Aware Roles and Access Policy

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a product engineering team member,
I want a baseline site-aware identity and authorization model,
so that every later feature can rely on consistent role-based access without redesigning the core domain.

## Acceptance Criteria

1. Given the platform foundation is already available, when this story is completed, then the backend contains the minimal domain structures needed for users, operational sites, and role assignments, and those structures support at least the MVP roles `Operator`, `Production Reviewer`, `Quality Reviewer`, and `Internal Configurator`.
2. Given the MVP must control access by operational responsibility, when a user is associated with one or more roles, then the system can determine which actions and data are permitted for that user, and unauthorized access attempts are denied by backend policy rather than frontend visibility alone.
3. Given the product must remain compatible with future organization and site expansion, when the initial authorization model is defined, then site context is part of the core access model from the start, and the design leaves room for later organization-scoped governance without changing the meaning of existing batch, template, and review records.
4. Given multiple epics will be developed in parallel, when feature teams start building template, execution, review, or export capabilities, then they can depend on a single canonical role and site access convention, and they do not need to invent feature-local permission rules.
5. Given this story should remain narrowly scoped, when it is implemented, then it delivers the domain model, baseline authorization checks, and documented role-policy conventions only, and it does not yet implement full workstation switching or signature ceremony behavior.

## Tasks / Subtasks

- [x] Create the first real authorization modules under `backend/apps/` without breaking the Story 1.1 foundation (AC: 1, 4, 5)
  - [x] Add `backend/apps/authz/` and `backend/apps/sites/` with the standard module shape used by the architecture: `api/`, `domain/`, `selectors/`, `tests/`, `apps.py`, `models.py`, `admin.py`, and `migrations/__init__.py`.
  - [x] Register both apps in `backend/config/settings/base.py`.
  - [x] Keep all new API routes under `/api/v1/`.
  - [x] Do not create unrelated future apps (`mmr`, `batches`, `signatures`, `reviews`, `exports`, `exceptions`, `audit`, `references`, `integrations`) in this story.

- [x] Introduce a swappable user model now, before local app migrations multiply (AC: 1, 3, 4)
  - [x] Implement `authz.User` as the project user model, starting from `AbstractUser` unless a stronger constraint is discovered during implementation.
  - [x] Set `AUTH_USER_MODEL = "authz.User"` in Django settings.
  - [x] Replace any direct references to `django.contrib.auth.models.User` with `settings.AUTH_USER_MODEL` or `get_user_model()`.
  - [x] Keep authentication session-based; do not introduce JWT, external IdP, badge auth, or PIN login in this story.

- [x] Model the minimum site-aware access structures needed for later epics (AC: 1, 2, 3, 4)
  - [x] Add a `Site` model with stable identity fields suitable for future linkage from batches, templates, and permissions.
  - [x] Add a site-scoped role assignment model linking `user`, `site`, and `role`.
  - [x] Represent the four MVP roles as canonical application roles: `operator`, `production_reviewer`, `quality_reviewer`, `internal_configurator`.
  - [x] Enforce uniqueness so the same user cannot receive the same role twice for the same site.
  - [x] Keep the schema additive and MVP-sized; do not introduce a premature `Organization` model unless implementation proves it is required.

- [x] Implement reusable backend authorization policy primitives instead of feature-local checks (AC: 2, 3, 4, 5)
  - [x] Add policy helpers in `backend/apps/authz/domain/` and/or `backend/shared/permissions/` that answer questions such as "does this user have role X on site Y?" and "which sites can this user act in?".
  - [x] Add DRF permission classes or equivalent backend guardrails that can be reused by later views.
  - [x] Ensure the policy layer is server-authoritative; frontend visibility must never be treated as access control.
  - [x] If custom DRF views perform object-specific actions, call `check_object_permissions()` explicitly so object-level enforcement is not skipped by accident.

- [x] Expose a minimal authenticated access-context surface for later stories to consume (AC: 2, 4, 5)
  - [x] Add a small authenticated endpoint such as `GET /api/v1/auth/context/` that returns the authenticated user summary plus site-role assignments in a canonical shape for later frontend work.
  - [x] Keep this endpoint informational; do not implement workstation identify, switch-user, lock-workstation, or signature re-authentication APIs yet.
  - [x] Return canonical role names and site identifiers so future features do not invent alternate role labels or payload shapes.

- [x] Document the authorization convention and cover it with tests (AC: 1, 2, 3, 4, 5)
  - [x] Add a short implementation doc describing the canonical role matrix, site scoping rule, and where enforcement lives.
  - [x] Add model tests for user/site/role assignment invariants.
  - [x] Add API and permission tests covering authenticated success, unauthenticated denial, wrong-role denial, and wrong-site denial.
  - [x] Verify the quality suite with the existing repo commands, using `/home/axel/wsl_venv/bin/python` for Python steps.

## Dev Notes

### Story Intent

This story establishes the first real identity and authorization backbone for the backend. Its job is to make site-aware RBAC a shared platform capability that later stories can extend safely.

It is intentionally not the shared-workstation authentication story. Do not fold user switching, PIN re-authentication, signature ceremony, or batch-specific workflow logic into this slice.

### Story Foundation

- Epic 1 exists to provide the platform spine for every later epic.
- Story 1.2 is the first story that should create real backend domain apps beyond the foundation shell.
- The acceptance criteria explicitly limit this story to domain structures, baseline authorization checks, and documented role-policy conventions.
- The architecture already reserves `backend/apps/authz/`, `backend/apps/sites/`, and `backend/shared/permissions/` for this concern.

### Technical Requirements

- Use `/home/axel/wsl_venv/bin/python` for Django management commands, migrations, tests, and any Python package work.
- Keep Django session authentication as the authoritative web authentication mechanism.
- Keep all application APIs under `/api/v1/`.
- Make the user model swappable now. Delaying the custom user model will make later migration work significantly harder.
- Use a first-class site-scoped assignment model for RBAC. Do not rely on Django `Group` membership alone because the required access model is site-aware, not global.
- Define one canonical set of MVP roles and reuse those exact names everywhere:
  - `operator`
  - `production_reviewer`
  - `quality_reviewer`
  - `internal_configurator`
- Keep backend enforcement authoritative. UI hiding is not authorization.
- Design the schema so later stories can attach `site` to batches, templates, and review flows without redefining access semantics.
- Leave room for future organization scoping, but do not invent a multi-tenant system in this story.
- Do not implement:
  - workstation identify / switch / lock APIs
  - PIN verification flows
  - signature ceremony flows
  - batch, template, review, release, or export permissions beyond the baseline role-policy layer

### Architecture Compliance

- Follow the split-stack baseline from Story 1.1; this story is backend-led and should not restructure frontend foundations.
- Place role and session concerns in `backend/apps/authz/` and site structures in `backend/apps/sites/`.
- Put reusable authorization helpers in `backend/shared/permissions/` if they are truly cross-cutting and business-agnostic.
- Keep app boundaries clean:
  - `api/` exposes serializers, views, and route wiring only.
  - `domain/` owns authorization rules and business decisions.
  - `selectors/` owns read-model queries and query composition.
- Respect `tools/check_backend_architecture.py`:
  - no unexpected top-level backend directories
  - no domain-layer imports from API packages
  - no shared backend code depending on API modules
- Use additive migrations only. Do not make destructive schema changes in the same rollout.
- Preserve the existing problem-details exception handling and schema generation patterns introduced in Story 1.1.

### Library / Framework Requirements

- Backend framework baseline remains Django 5.2 LTS, already pinned in [pyproject.toml](/home/axel/DLE-SaaS/pyproject.toml).
- API framework baseline remains Django REST framework 3.16.x.
- Keep session-based auth and CSRF protection compatible with same-origin browser usage; do not switch to token-first auth.
- Use Django's recommended custom-user approach by subclassing `AbstractUser` unless implementation uncovers a hard reason not to.
- Do not add third-party authorization frameworks such as `django-guardian`, `rules`, or policy engines in this story unless a concrete blocker appears. The documented requirements are satisfied by a first-party site-role assignment model plus reusable service/permission helpers.

### Data Modeling Guardrails

- Recommended minimum entities:
  - `authz.User`
  - `sites.Site`
  - `authz.SiteRoleAssignment` or equivalent site-scoped membership model
- Recommended role representation:
  - Django `TextChoices` or equivalent canonical enum values in application code
- Recommended minimum `Site` fields:
  - stable human name
  - stable code or slug
  - active flag
  - created/updated timestamps if they fit current project conventions
- Recommended minimum assignment fields:
  - user FK
  - site FK
  - role enum
  - active flag if needed
  - unique constraint across `(user, site, role)`
- Do not model permissions as free-form strings in the database for this story.
- Do not create a broad `Organization` hierarchy yet; future compatibility is enough here.

### API Guidance

- If you add `GET /api/v1/auth/context/`, keep the response narrow and stable. It should help later frontend stories answer:
  - who is authenticated
  - which site memberships exist
  - which canonical roles the user holds per site
- Keep write-side auth flows out of scope for Story 1.2.
- If you add protected placeholder endpoints to prove authorization behavior, keep them internal to this story and avoid inventing business endpoints for later epics.

### File Structure Requirements

- Backend settings and wiring likely to change:
  - [backend/config/settings/base.py](/home/axel/DLE-SaaS/backend/config/settings/base.py)
  - [backend/config/urls.py](/home/axel/DLE-SaaS/backend/config/urls.py)
- Expected new backend modules:
  - `backend/apps/authz/`
  - `backend/apps/sites/`
  - `backend/shared/permissions/` if needed for generic permission helpers
- Expected authz files:
  - `backend/apps/authz/apps.py`
  - `backend/apps/authz/models.py`
  - `backend/apps/authz/admin.py`
  - `backend/apps/authz/api/urls.py`
  - `backend/apps/authz/api/views.py`
  - `backend/apps/authz/api/serializers.py`
  - `backend/apps/authz/domain/`
  - `backend/apps/authz/selectors/`
  - `backend/apps/authz/tests/`
  - `backend/apps/authz/migrations/__init__.py`
- Expected sites files:
  - `backend/apps/sites/apps.py`
  - `backend/apps/sites/models.py`
  - `backend/apps/sites/admin.py`
  - `backend/apps/sites/tests/`
  - `backend/apps/sites/migrations/__init__.py`
- Documentation target:
  - `docs/implementation/authorization-policy.md` or a similarly scoped implementation note

### Testing Requirements

- Backend model tests:
  - custom user model loads correctly
  - site-role assignment uniqueness is enforced
  - canonical roles are validated
- Backend permission tests:
  - unauthenticated requests are denied where required
  - authenticated users with the correct role and site are allowed
  - authenticated users with the wrong role are denied
  - authenticated users with access to one site are denied for another site
- Endpoint tests:
  - `GET /api/v1/auth/context/` returns the expected role/site payload for an authenticated user
  - the endpoint does not leak assignments outside the authenticated user
- Migration sanity:
  - verify Django can build the schema from scratch with the custom user model in place
- Quality commands:
  - `make lint`
  - `make typecheck`
  - `make test`
  - `make architecture-check`
  - Prefer `make check` before closing the story if runtime and dependencies are available

### Previous Story Intelligence

- Story 1.1 established the split-stack baseline, settings layout, `/api/v1` namespace, problem-details exception handler, and the root quality commands. Extend those patterns; do not rework them.
- Story 1.1 deliberately avoided creating domain apps prematurely. Story 1.2 is the first justified place to introduce `authz` and `sites`.
- Story 1.1 already proved that repo conventions matter:
  - preserve env-driven configuration
  - preserve architecture checks
  - preserve the shared API wiring pattern under `backend/shared/api/`
- Reuse the existing Django project and test setup rather than creating parallel bootstrap code.

### Git Intelligence Summary

- Recent commits show the project just came out of the foundation phase:
  - `2cd6799` implemented Story 1.1 foundation
  - `6cc7a79` fixed review findings in the foundation
  - `b48315f` hardened non-dev deployment baselines
- Practical implication:
  - favor incremental changes over refactors
  - follow the patterns already accepted in review
  - keep this story tightly scoped to authz/sites foundations

### Latest Technical Information

- Django's current supported-versions page lists the 5.2 line as the active LTS branch, and the project is already pinned to `>=5.2,<5.3`. Stay on Django 5.2 for this story instead of introducing a framework upgrade mid-foundation. [Source: https://www.djangoproject.com/download/]
- Django's auth customization docs recommend defining a custom user model at the start of a project and wiring `AUTH_USER_MODEL` before migrations become entrenched. That guidance applies here because the repo has only just started creating real backend domain models. [Source: https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#substituting-a-custom-user-model]
- DRF `SessionAuthentication` remains compatible with same-origin AJAX clients and requires valid CSRF tokens for unsafe requests. That matches the architecture choice of Django server-managed sessions on shared workstations. [Source: https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication]
- DRF permissions run before the main view logic, and object-level permissions are only enforced automatically in framework paths that call them. If a custom view handles objects manually, call `check_object_permissions()` yourself. [Source: https://www.django-rest-framework.org/api-guide/permissions/]
- The architecture still defers workstation identify, switch-user, lock, and signature re-authentication to the next story. Do not pre-build those APIs here just because the later endpoint names are already documented.

### Project Context Reference

No `project-context.md` file was present in the repository when this story was created.

Use these source artifacts instead:

- [epics.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/epics.md)
- [architecture.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/architecture.md)
- [prd.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/prd.md)
- [ux-design-specification.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/ux-design-specification.md)
- [architecture-decisions.md](/home/axel/DLE-SaaS/docs/decisions/architecture-decisions.md)
- [Makefile](/home/axel/DLE-SaaS/Makefile)
- [tools/check_backend_architecture.py](/home/axel/DLE-SaaS/tools/check_backend_architecture.py)
- [1-1-initialize-the-split-stack-foundation.md](/home/axel/DLE-SaaS/_bmad-output/implementation-artifacts/1-1-initialize-the-split-stack-foundation.md)

### Project Structure Notes

- The architecture artifact shows a fuller future backend tree than the current repository contains today. Right now the repository still has the Story 1.1 minimal shape plus `backend/apps/__init__.py`.
- Story 1.2 should be the first story to introduce real feature apps under `backend/apps/`, but only for `authz` and `sites`.
- Avoid a common failure mode: creating placeholder directories for later epics just because the architecture tree lists them.
- The frontend architecture already reserves `frontend/src/features/auth/` for future UI work, but this story does not need to build a real frontend auth surface unless a very small consumer of `auth/context` is necessary.

### References

- [epics.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/epics.md) - Epic 1, Story 1.2 scope and acceptance criteria
- [architecture.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/architecture.md) - session auth, site-scoped RBAC, app boundaries, endpoint conventions, future `authz` and `sites` modules
- [prd.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/prd.md) - RBAC matrix, site-aware growth constraints, MVP role definitions, security requirements
- [ux-design-specification.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/ux-design-specification.md) - shared-workstation identity expectations and explicit confirmation that richer auth flows belong to later stories
- [architecture-decisions.md](/home/axel/DLE-SaaS/docs/decisions/architecture-decisions.md) - stack freeze and domain explicitness decisions
- [Makefile](/home/axel/DLE-SaaS/Makefile) - canonical local quality commands
- [tools/check_backend_architecture.py](/home/axel/DLE-SaaS/tools/check_backend_architecture.py) - backend boundary enforcement rules
- [1-1-initialize-the-split-stack-foundation.md](/home/axel/DLE-SaaS/_bmad-output/implementation-artifacts/1-1-initialize-the-split-stack-foundation.md) - previous story learnings and established repo patterns
- https://www.djangoproject.com/download/ - Django supported versions and LTS guidance
- https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#substituting-a-custom-user-model - custom user model guidance
- https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication - DRF session authentication behavior
- https://www.django-rest-framework.org/api-guide/permissions/ - DRF permission and object-permission guidance

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Implementation Plan

- Introduce first-class `sites` and `authz` Django apps with additive initial migrations only.
- Swap the project to `authz.User` immediately so later feature apps do not inherit Django's default user model.
- Keep site-aware RBAC logic reusable by splitting read models into selectors, decision logic into domain policies, and DRF guardrails into `backend/shared/permissions/`.
- Expose only one informational authenticated surface in this story: `GET /api/v1/auth/context/`.
- Validate against the repo quality suite using the running Compose PostgreSQL instance exposed on `127.0.0.1:65432`.

### Debug Log References

- Story key resolved from `sprint-status.yaml` as `1-2-establish-site-aware-roles-and-access-policy`.
- Story 1.1 was loaded and analyzed for implementation patterns, review fixes, and quality expectations.
- Architecture, PRD, and UX artifacts were re-analyzed specifically for site-aware RBAC, session authentication, workstation identity scope boundaries, and future role-based surfaces.
- Official Django and DRF documentation was consulted on 2026-03-12 for current custom-user and session-permission guidance.
- No `project-context.md` file was present in the repository at story-creation time.
- `/home/axel/wsl_venv/bin/python backend/manage.py makemigrations sites authz` generated additive initial migrations for the new backend apps.
- Targeted backend RBAC tests passed with `POSTGRES_HOST=127.0.0.1` and `POSTGRES_PORT=65432` against the running Compose PostgreSQL container.
- `make security` passed after extending the Bandit exclusions to cover app-local pytest directories.
- `make check` passed with the same PostgreSQL environment overrides; `react-doctor` completed with one pre-existing frontend warning for an unused `ButtonProps` type in `frontend/src/shared/ui/button.tsx`.

### Completion Notes List

- Added `authz.User`, `sites.Site`, and `authz.SiteRoleAssignment` with canonical MVP roles and a uniqueness constraint across `(user, site, role)`.
- Registered the new apps in Django settings, switched `AUTH_USER_MODEL` to `authz.User`, and generated initial migrations without introducing unrelated feature apps.
- Added reusable authorization helpers in `backend/apps/authz/domain/policies.py` and `backend/shared/permissions/site_roles.py` so later endpoints can enforce site-scoped roles consistently.
- Exposed `GET /api/v1/auth/context/` under `/api/v1/auth/` with an authenticated user summary and grouped site-role assignments in a canonical payload shape.
- Documented the baseline authorization convention in `docs/implementation/authorization-policy.md`.
- Added model, API, and permission tests covering swappable user configuration, duplicate-role prevention, canonical-role validation, authenticated context payloads, unauthenticated denial, wrong-role denial, and wrong-site denial.
- Verified the full repo quality suite with `make check` using `/home/axel/wsl_venv/bin/python` for Python tooling and the Compose PostgreSQL container exposed on `127.0.0.1:65432`.
- Locked DRF to session authentication only, added a shipped site-role probe endpoint, expanded the permission primitive for object-level site resolution, and documented the custom-user cutover path for pre-Story-1.2 environments.

### File List

- `_bmad-output/implementation-artifacts/1-2-establish-site-aware-roles-and-access-policy.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `Makefile`
- `backend/apps/authz/__init__.py`
- `backend/apps/authz/admin.py`
- `backend/apps/authz/api/__init__.py`
- `backend/apps/authz/api/serializers.py`
- `backend/apps/authz/api/urls.py`
- `backend/apps/authz/api/views.py`
- `backend/apps/authz/apps.py`
- `backend/apps/authz/domain/__init__.py`
- `backend/apps/authz/domain/policies.py`
- `backend/apps/authz/migrations/0001_initial.py`
- `backend/apps/authz/migrations/__init__.py`
- `backend/apps/authz/models.py`
- `backend/apps/authz/selectors/__init__.py`
- `backend/apps/authz/selectors/access_context.py`
- `backend/apps/authz/tests/__init__.py`
- `backend/apps/authz/tests/test_api.py`
- `backend/apps/authz/tests/test_models.py`
- `backend/apps/authz/tests/test_permissions.py`
- `backend/apps/sites/__init__.py`
- `backend/apps/sites/admin.py`
- `backend/apps/sites/api/__init__.py`
- `backend/apps/sites/apps.py`
- `backend/apps/sites/domain/__init__.py`
- `backend/apps/sites/migrations/0001_initial.py`
- `backend/apps/sites/migrations/__init__.py`
- `backend/apps/sites/models.py`
- `backend/apps/sites/selectors/__init__.py`
- `backend/apps/sites/tests/__init__.py`
- `backend/apps/sites/tests/test_models.py`
- `backend/config/settings/base.py`
- `backend/tests/test_settings_base.py`
- `backend/shared/api/urls.py`
- `backend/shared/permissions/__init__.py`
- `backend/shared/permissions/site_roles.py`
- `docs/implementation/README.md`
- `docs/implementation/authorization-policy.md`
- `docs/implementation/custom-user-model-cutover.md`
- `pyproject.toml`

### Senior Developer Review (AI)

**Reviewer:** Axel
**Date:** 2026-03-12
**Outcome:** Approved after fixes

#### Summary

- Story context, architecture, and Epic 1 Story 1.2 requirements were reviewed.
- No uncommitted or staged git changes were present during review, so validation used the story file list and committed source.
- Verified with:
  - `POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=65432 /home/axel/wsl_venv/bin/python -m pytest backend/apps/authz/tests backend/apps/sites/tests`
  - `make lint-python`
  - `make typecheck-python`
  - `make architecture-check-backend`

#### Findings

1. **[High] The API still accepts non-session authentication even though the story requires a session-only baseline.**
   - `REST_FRAMEWORK` sets the schema and exception handler only, so Django REST framework falls back to its default authentication classes instead of an explicit session-only configuration. That leaves `BasicAuthentication` enabled for current and future endpoints, which bypasses the shared-workstation/session contract this story is supposed to freeze.
   - Evidence:
     - [backend/config/settings/base.py](/home/axel/DLE-SaaS/backend/config/settings/base.py#L119)
     - [backend/apps/authz/api/views.py](/home/axel/DLE-SaaS/backend/apps/authz/api/views.py#L15)

2. **[High] AC 2 is only proven in a test-only view; no production route actually enforces site-role authorization yet.**
   - The shipped auth endpoint uses `IsAuthenticated` only. `SiteScopedRolePermission` is never wired into any runtime URL/view pair, so the application still has no real endpoint where wrong-role or wrong-site access is denied by backend policy. The current tests prove the helper in isolation, not the delivered app behavior claimed in the story.
   - Evidence:
     - [backend/apps/authz/api/views.py](/home/axel/DLE-SaaS/backend/apps/authz/api/views.py#L15)
     - [backend/shared/api/urls.py](/home/axel/DLE-SaaS/backend/shared/api/urls.py#L11)
     - [backend/apps/authz/tests/test_permissions.py](/home/axel/DLE-SaaS/backend/apps/authz/tests/test_permissions.py#L17)

3. **[Medium] The reusable permission primitive is not reusable enough for the object-scoped endpoints later epics will build.**
   - `SiteScopedRolePermission` can authorize only when a `site_code` URL kwarg is present. It has no `has_object_permission()` path and no hook for deriving site context from a batch, template, review, or any other domain object. Later teams will have to add custom glue per endpoint or skip object-level checks, which is exactly the feature-local divergence this story is meant to prevent.
   - Evidence:
     - [backend/shared/permissions/site_roles.py](/home/axel/DLE-SaaS/backend/shared/permissions/site_roles.py#L14)

4. **[Medium] Switching to `AUTH_USER_MODEL = "authz.User"` after Story 1.1 leaves the upgrade path for already-migrated environments undefined.**
   - This story adds the custom user model in `authz` and changes the project setting, but there is no migration or documented procedure for environments that already ran the foundation with the previous user table. Django's own guidance is that changing the user model after database tables already exist is manual and complex. As implemented, existing admin or local accounts from an earlier migrated environment would not be migrated into `authz_user`.
   - Evidence:
     - [backend/config/settings/base.py](/home/axel/DLE-SaaS/backend/config/settings/base.py#L117)
     - [backend/apps/authz/migrations/0001_initial.py](/home/axel/DLE-SaaS/backend/apps/authz/migrations/0001_initial.py#L21)

#### Developer Follow-up

- 2026-03-12: Set DRF `DEFAULT_AUTHENTICATION_CLASSES` to `SessionAuthentication` only and added a regression test rejecting Basic auth on `GET /api/v1/auth/context/`.
- 2026-03-12: Added shipped runtime enforcement at `GET /api/v1/auth/sites/{site_code}/operator-access/` with API tests covering allowed access, wrong-role denial, and wrong-site denial.
- 2026-03-12: Expanded `SiteScopedRolePermission` with request-level and object-level site resolution hooks so later stories can reuse the same primitive against object-scoped resources.
- 2026-03-12: Added a documented cutover runbook for environments initialized before the switch to `authz.User`.
- 2026-03-12: Re-ran targeted backend verification after fixes and accepted the story for completion.
- 2026-03-12: Re-ran `make check` successfully after the review fixes; `react-doctor` still reports one pre-existing frontend warning for an unused `ButtonProps` type in `frontend/src/shared/ui/button.tsx`.

### Change Log

- 2026-03-12: Implemented Story 1.2 site-aware RBAC foundations, added the authenticated access-context endpoint, documented the authorization convention, expanded backend tests, and passed `make check`.
- 2026-03-12: Senior developer review completed. Outcome: Changes Requested. Story returned to `in-progress` pending authentication baseline and runtime authorization fixes.
- 2026-03-12: Addressed senior review findings by enforcing session-only DRF auth, shipping a runtime role-protected auth probe endpoint, extending site-role permission reuse for object-scoped resources, documenting the custom-user cutover path, and re-running targeted backend checks.
- 2026-03-12: Story marked `done` after review findings were fixed and targeted verification passed.
- 2026-03-12: Full `make check` quality suite passed after the review fixes; only the pre-existing `react-doctor` warning for unused `ButtonProps` remains.
