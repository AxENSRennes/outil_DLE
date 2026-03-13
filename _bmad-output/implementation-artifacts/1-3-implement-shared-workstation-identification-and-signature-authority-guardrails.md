# Story 1.3: Implement Shared-Workstation Identification and Signature Authority Guardrails

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator or reviewer working on a shared production workstation,
I want the system to identify the active user securely and enforce signature authority rules,
so that work attribution remains correct and only authorized users can perform regulated signature actions.

## Acceptance Criteria

1. Given a shared workstation is used by multiple people across shifts, when a user identifies on the workstation, then the backend establishes the active authenticated session for that user, and the system preserves the current workstation context without requiring full application re-entry.
2. Given one user may leave and another may take over the same workstation, when the active user switches or the workstation is locked, then the prior authenticated authority is removed from the active session, and a later user must identify again before performing authenticated actions.
3. Given only authorized users may sign regulated actions, when a signature-protected action is requested, then the system verifies that the active user holds a role permitted for that signature context, and unauthorized signature attempts are rejected server-side.
4. Given the platform must preserve a trustworthy audit trail from the start, when identification, switch-user, lock, failed identification, or signature-authorization events occur, then those events are recorded with actor, timestamp, and event type, and they are available for later review and troubleshooting.
5. Given this story is part of the platform spine rather than full workflow execution, when it is implemented, then it provides the shared-workstation session and signature-guardrail backend behavior plus minimal API support, and it does not yet require full operator execution UI, step signing UI, or batch-specific workflow logic.

## Tasks / Subtasks

- [x] Implement shared-workstation identification on top of the existing Django session and site-aware authz baseline (AC: 1, 2, 5)
  - [x] Add a dedicated workstation credential path for `authz.User`. Recommended inference from the UX and architecture artifacts: use a dedicated hashed PIN credential or equivalent short-secret model for workstation and signature re-authentication rather than overloading site-role assignments or storing raw PIN values.
  - [x] Add `POST /api/v1/auth/workstation-identify/` that verifies the workstation credential, establishes the active Django session, and returns the active user plus site-role context without redirecting away from the current screen.
  - [x] Treat identify-while-another-user-is-active as switch-user behavior: replace prior session authority, emit an explicit switch event, and return enough response context for the frontend to stay on the current batch route later.
  - [x] Keep general Django/admin authentication intact. Do not replace the whole project with a PIN-only authentication backend.

- [x] Implement workstation lock semantics that remove prior authority cleanly (AC: 2, 5)
  - [x] Add `POST /api/v1/auth/workstation-lock/` that clears the active authenticated authority from the session and leaves no protected actions available until re-identification.
  - [x] Ensure `GET /api/v1/auth/context/` and any future protected workstation actions reflect the locked state immediately after lock.
  - [x] Provide backend-ready lock behavior only. Do not build inactivity countdown UI, batch resume UI, or operator execution screens in this story.

- [x] Add reusable signature step-up authorization guardrails for later execution stories (AC: 3, 5)
  - [x] Add a reusable authz service that verifies whether the active user may perform a signature-protected action for a given site and required role set.
  - [x] Ship one minimal signature guardrail endpoint. Recommended shape: `POST /api/v1/auth/signature-reauth/` or an equivalent action endpoint that re-verifies the active user with PIN plus site/context and returns authorized signer metadata without creating a signature record.
  - [x] Reject wrong-role and wrong-site signature authorization requests server-side.
  - [x] Keep actual `Signature` persistence, batch-step linkage, signature manifests, and execution-step state changes out of scope for this story. Those belong to Story 3.5 and later review stories.

- [x] Introduce canonical audit instrumentation for workstation auth events (AC: 4)
  - [x] Add a narrow `backend/apps/audit/` foundation or an equivalent canonical audit module that can persist `identify`, `switch_user`, `lock_workstation`, `identify_failed`, `signature_reauth_succeeded`, and `signature_reauth_failed`.
  - [x] Capture actor when known, timestamp, event type, site context when known, and minimal structured metadata useful for troubleshooting.
  - [x] Never persist raw PIN values, clear-text credentials, or replayable secrets in audit metadata.
  - [x] Keep the model additive and MVP-sized. Do not attempt the full batch-linked audit model from Story 4.1 yet.

- [x] Document and test the workstation auth contract end to end (AC: 1, 2, 3, 4, 5)
  - [x] Extend the `/api/v1/auth/` API contract and serializers for the new action endpoints.
  - [x] Document the workstation identify/switch/lock behavior, the signature re-auth guardrail flow, and the auth-event taxonomy in `docs/implementation/`.
  - [x] Add targeted backend tests for successful identify, failed identify, switch-user via re-identify, lock, locked-session denial, signature re-auth success, wrong-role denial, wrong-site denial, failed re-auth audit capture, and no raw PIN leakage in persisted audit metadata.
  - [x] Run the repo quality gates with `/home/axel/wsl_venv/bin/python` and prefer `make check` before closing the story.

## Dev Notes

### Story Intent

This story introduces the shared-workstation security behavior that the rest of the product depends on: identify the current operator or reviewer quickly, clear authority cleanly on lock or user switch, and enforce signature authority before regulated actions occur.

It is still a platform slice, not the execution workflow itself. The implementation should deliver session, re-auth, and audit primitives that later stories can call, without pre-building batch execution, step signing, or review UI.

### Story Foundation

- Epic 1 exists to provide the platform spine before batch, signature, and review workflows expand.
- Story 1.2 already established the custom `authz.User`, site-scoped role assignments, session-only DRF authentication, and reusable site-role permission primitives.
- Story 1.3 should extend that foundation rather than invent a second auth model.
- This story unblocks later execution and traceability work, especially:
  - Story 3.5 for real execution-signature actions
  - Story 4.1 for broader batch-linked audit events
- Keep scope tight:
  - add workstation identify, switch, lock, signature re-auth guardrails, and canonical auth-event capture
  - do not add batch-aware signing, execution step state changes, review states, or operator UI

### Technical Requirements

- Use `/home/axel/wsl_venv/bin/python` for Django management commands, tests, and package operations.
- Keep Django server-managed sessions as the authoritative browser auth mechanism.
- Preserve the Story 1.2 session-only DRF baseline. Do not add JWT, external IdP, badge middleware, or a parallel token system.
- Implement identify by establishing a real Django session for the active user, not by faking identity in frontend state.
- Implement lock by removing authenticated session authority completely. Do not leave the prior user active in cookies, server session state, or any cached auth context.
- Inference from the UX and architecture artifacts: use a dedicated workstation PIN credential or equivalent short-secret flow for identify and signature re-authentication rather than reusing a full admin password flow on the production line.
- Keep the workstation credential stored as a secure hash using Django-compatible password hashing utilities or an equivalent server-side hashing approach. Never store raw PINs.
- Keep the active site and role model from Story 1.2 authoritative. Signature authority checks must compose with site-scoped roles; frontend visibility is not enough.
- Rate-limit identify and signature-sensitive endpoints independently from general page traffic.
- Pair rate limiting with auditable failed-attempt events. Do not silently drop or ignore failed auth attempts.
- Preserve workstation context by avoiding redirect-based auth flows. The backend should return structured API responses that let the future frontend remain on the current route.
- Do not persist batch route, step state, or draft form state in the auth session for this story. Later execution stories own batch context and auto-save behavior.
- Do not create signature records in this story. The goal here is reusable signature authority and re-auth guardrails, not the final batch-signature business event.

### Architecture Compliance

- Keep auth/session concerns in `backend/apps/authz/`.
- Prefer a new `backend/apps/audit/` app for canonical auth-event storage because the architecture already reserves audit as a first-class backend domain.
- Reuse `backend/shared/permissions/site_roles.py` and `apps.authz.domain` helpers instead of inventing feature-local permission logic.
- Keep all new APIs under `/api/v1/auth/`.
- Follow the action-oriented API pattern from the architecture artifact. Use explicit endpoints such as identify, lock, and signature re-auth instead of generic PATCH mutations on session state.
- Respect existing modular-monolith boundaries:
  - `api/` for serializers, views, route wiring, and request/response contracts
  - `domain/` for workstation auth decisions, credential verification, and event recording orchestration
  - `selectors/` for read-model queries only
- Preserve problem-details error responses and drf-spectacular schema generation patterns already in the repo.
- Use additive migrations only. Any future batch-linked audit expansion must remain compatible with this first auth-event foundation.

### Library / Framework Requirements

- Django stays on the 5.2 LTS line already pinned in [pyproject.toml](/home/axel/DLE-SaaS/pyproject.toml). Do not introduce a framework upgrade while implementing this story.
- Django's auth flow should remain the session authority. Use the standard login/session/logout primitives rather than a custom cookie scheme.
- Django REST framework remains on the 3.16 line with `SessionAuthentication`.
- Unsafe session-authenticated requests require CSRF protection. Treat the identify and signature re-auth actions as login-sensitive POST endpoints and enforce CSRF rather than trying to bypass it.
- DRF throttling can help express endpoint-specific rate policies, but official DRF guidance is that throttling is not a full brute-force security control. Pair throttles with explicit audit events and server-side credential checks.
- Keep drf-spectacular as the OpenAPI generator and document the new auth action endpoints there.
- Do not add a heavyweight third-party auth or policy framework unless a concrete implementation blocker appears.

### File Structure Requirements

- Existing backend auth wiring to extend:
  - [backend/apps/authz/api/urls.py](/home/axel/DLE-SaaS/backend/apps/authz/api/urls.py)
  - [backend/apps/authz/api/views.py](/home/axel/DLE-SaaS/backend/apps/authz/api/views.py)
  - [backend/apps/authz/api/serializers.py](/home/axel/DLE-SaaS/backend/apps/authz/api/serializers.py)
  - [backend/apps/authz/domain/policies.py](/home/axel/DLE-SaaS/backend/apps/authz/domain/policies.py)
  - [backend/shared/permissions/site_roles.py](/home/axel/DLE-SaaS/backend/shared/permissions/site_roles.py)
  - [backend/shared/api/urls.py](/home/axel/DLE-SaaS/backend/shared/api/urls.py)
- Recommended new backend modules:
  - `backend/apps/authz/domain/workstation.py` or an equivalent session-orchestration module
  - `backend/apps/authz/tests/test_workstation_api.py`
  - `backend/apps/authz/tests/test_signature_reauth.py`
  - `backend/apps/audit/` for canonical auth-event persistence
- Recommended new audit files:
  - `backend/apps/audit/apps.py`
  - `backend/apps/audit/models.py`
  - `backend/apps/audit/admin.py`
  - `backend/apps/audit/migrations/__init__.py`
  - `backend/apps/audit/tests/`
- Documentation target:
  - `docs/implementation/authorization-policy.md`
  - a new workstation-focused implementation note if the current authorization document becomes too broad

### Testing Requirements

- Backend API tests:
  - successful workstation identify establishes an authenticated session
  - identify while another user is active behaves as switch-user and removes prior authority
  - workstation lock clears the authenticated session
  - locked or anonymous sessions cannot use protected auth/context endpoints
  - signature re-auth succeeds only for an authenticated user with a valid fresh credential and permitted site role
  - signature re-auth denies wrong-role, wrong-site, and bad-PIN attempts
- Backend audit tests:
  - `identify`, `switch_user`, `lock_workstation`, `identify_failed`, `signature_reauth_succeeded`, and `signature_reauth_failed` are persisted with the required event data
  - audit metadata never stores raw PIN values or equivalent secrets
- Security behavior tests:
  - CSRF remains enforced on unsafe session-auth endpoints
  - rate limits are applied to identify and signature-sensitive endpoints
  - failed auth attempts remain attributable enough for troubleshooting even when no actor is authenticated
- Regression tests:
  - existing `GET /api/v1/auth/context/` behavior still works for a valid session
  - existing site-role permission helpers still behave correctly after workstation/session changes
- Quality commands:
  - `make lint`
  - `make typecheck`
  - `make test`
  - `make architecture-check`
  - Prefer `make check` before closing the story

### Previous Story Intelligence

- Story 1.2 already shipped the custom user model, site-scoped role assignments, and the `/api/v1/auth/context/` informational read surface.
- Story 1.2 also froze the session-only DRF baseline, which is exactly what this story should extend for workstation identify and lock.
- The current code already contains reusable site-role authorization primitives in [site_roles.py](/home/axel/DLE-SaaS/backend/shared/permissions/site_roles.py); reuse and extend those instead of adding parallel role checks.
- Story 1.2 review feedback highlighted two important habits that still matter here:
  - ship real runtime-enforced auth behavior, not only helper classes or test-only views
  - make object or site resolution explicit and test negative paths thoroughly
- The current authorization implementation note explicitly says workstation identify, PIN checks, and signature re-authentication are not implemented yet. Story 1.3 is the first correct place to add them.

### Git Intelligence Summary

- Recent commits are still tightly focused on Story 1.2 hardening:
  - `f81418d` merged the site-aware roles and access-policy story
  - `89f992e` hardened DRF default API permissions
  - `83c9e7e` and `771bf23` fixed subtle permission-resolution edge cases
- Practical implication:
  - favor incremental extension of the authz layer over refactoring the project skeleton
  - keep endpoint behavior explicit and heavily tested
  - preserve the existing permission helper patterns and avoid clever fallback logic that is hard to reason about
- The current backend app tree still contains only `authz` and `sites`. This story should stay just as disciplined and avoid prematurely creating batch, signature, or review modules.

### Latest Technical Information

- Django's supported-versions page lists Django 5.2 as the current LTS line, with 5.2.12 released on 2026-03-04. The repo is already pinned to `>=5.2,<5.3`, so stay on Django 5.2 for this story instead of upgrading the framework mid-foundation. [Source: https://www.djangoproject.com/download/]
- Django's auth docs describe `authenticate()` for credential verification, `login()` for attaching the authenticated user to the session, and `logout()` for removing the authenticated user's ID from the request and flushing session data. That maps directly to identify and lock behavior in this story. [Source: https://docs.djangoproject.com/en/5.2/topics/auth/default/]
- Django also exposes `user_logged_in`, `user_logged_out`, and `user_login_failed` auth signals. They can help trigger audit hooks, but this story should still record explicit business-level auth events rather than relying on framework signals alone for canonical audit semantics. [Source: https://docs.djangoproject.com/en/5.2/ref/contrib/auth/#topics-auth-signals]
- DRF's official authentication docs confirm that `SessionAuthentication` is appropriate for same-origin AJAX clients using Django sessions and that login views should always have CSRF validation applied. That matters for `POST /api/v1/auth/workstation-identify/` and any signature re-auth POST action. [Source: https://www.django-rest-framework.org/api-guide/authentication/]
- DRF's throttling docs explicitly warn that application-level throttling should not be considered a security measure or brute-force defense. Use it here as a baseline operational guardrail only, paired with audit visibility and explicit server-side credential checks. [Source: https://www.django-rest-framework.org/api-guide/throttling/]
- drf-spectacular's official documentation still supports the repo's Django 5.2 and DRF 3.16 baseline. Keep the new workstation auth endpoints in the same generated OpenAPI contract rather than documenting them ad hoc. [Source: https://drf-spectacular.readthedocs.io/en/latest/readme.html]

### Project Context Reference

No `project-context.md` file was present in the repository when this story was created.

Use these source artifacts instead:

- [epics.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/epics.md)
- [architecture.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/architecture.md)
- [prd.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/prd.md)
- [ux-design-specification.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/ux-design-specification.md)
- [authorization-policy.md](/home/axel/DLE-SaaS/docs/implementation/authorization-policy.md)
- [architecture-decisions.md](/home/axel/DLE-SaaS/docs/decisions/architecture-decisions.md)
- [Makefile](/home/axel/DLE-SaaS/Makefile)
- [1-2-establish-site-aware-roles-and-access-policy.md](/home/axel/DLE-SaaS/_bmad-output/implementation-artifacts/1-2-establish-site-aware-roles-and-access-policy.md)

### Project Structure Notes

- The backend currently has only two feature apps under `backend/apps/`: `authz` and `sites`.
- The frontend currently has only `frontend/src/features/foundation/`; there is no real auth feature module yet.
- That current structure reinforces the intended scope for Story 1.3:
  - backend-first auth/session and audit behavior is required now
  - a real operator workstation UI is not required yet
- `/api/v1/auth/` currently exposes:
  - `GET /api/v1/auth/context/`
  - `GET /api/v1/auth/sites/{site_code}/operator-access/`
- Story 1.3 should extend that same auth namespace instead of introducing a parallel API surface elsewhere.
- The architecture artifact reserves future `signatures` and `audit` apps, but only audit is justified in this story. Do not create `batches`, `signatures`, `reviews`, `exports`, or other later-epic modules prematurely.

### References

- [epics.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/epics.md) - Epic 1 Story 1.3 scope, acceptance criteria, and forward dependencies
- [architecture.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/architecture.md) - shared-workstation session model, auth action contracts, audit instrumentation, and backend boundaries
- [prd.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/prd.md) - security, reliability, auditability, and workstation constraints
- [ux-design-specification.md](/home/axel/DLE-SaaS/_bmad-output/planning-artifacts/ux-design-specification.md) - lot-kiosk pattern, fast user switching, inline signature re-authentication, and anti-patterns
- [authorization-policy.md](/home/axel/DLE-SaaS/docs/implementation/authorization-policy.md) - current authz baseline and explicit out-of-scope note for workstation flows
- [architecture-decisions.md](/home/axel/DLE-SaaS/docs/decisions/architecture-decisions.md) - shared-workstation session model and explicit auth-event expectations
- [Makefile](/home/axel/DLE-SaaS/Makefile) - canonical local verification commands
- [pyproject.toml](/home/axel/DLE-SaaS/pyproject.toml) - pinned Django, DRF, and drf-spectacular lines
- [backend/apps/authz/models.py](/home/axel/DLE-SaaS/backend/apps/authz/models.py) - current user and site-role assignment model
- [backend/apps/authz/api/views.py](/home/axel/DLE-SaaS/backend/apps/authz/api/views.py) - existing auth endpoint patterns
- [backend/shared/permissions/site_roles.py](/home/axel/DLE-SaaS/backend/shared/permissions/site_roles.py) - reusable site-role permission primitive
- [1-2-establish-site-aware-roles-and-access-policy.md](/home/axel/DLE-SaaS/_bmad-output/implementation-artifacts/1-2-establish-site-aware-roles-and-access-policy.md) - previous story learnings and accepted conventions
- https://www.djangoproject.com/download/ - Django supported versions and current 5.2 LTS release information
- https://docs.djangoproject.com/en/5.2/topics/auth/default/ - Django session login/logout/authentication behavior
- https://docs.djangoproject.com/en/5.2/ref/contrib/auth/#topics-auth-signals - Django auth signals for login/logout/failed login hooks
- https://www.django-rest-framework.org/api-guide/authentication/ - DRF session authentication and CSRF guidance
- https://www.django-rest-framework.org/api-guide/throttling/ - DRF throttling limitations and usage guidance
- https://drf-spectacular.readthedocs.io/en/latest/readme.html - OpenAPI generation support for the current stack

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story key resolved as `1-3-implement-shared-workstation-identification-and-signature-authority-guardrails` from [sprint-status.yaml](/home/axel/DLE-SaaS/_bmad-output/implementation-artifacts/sprint-status.yaml).
- Story 1.2 was loaded and analyzed as the immediate implementation predecessor.
- The epics, architecture, PRD, UX specification, authz implementation note, current backend authz code, and recent git history were re-analyzed specifically for shared-workstation auth, signature authority, and audit-event requirements.
- Official Django, DRF, and drf-spectacular documentation was consulted on 2026-03-13 for current session auth, CSRF, throttling, signal, and version-line guidance.
- No `project-context.md` file was present in the repository at story-creation time.
- Added a dedicated hashed `workstation_pin` credential path on `authz.User` plus additive migrations for `authz` and the new `audit` app.
- Added `POST /api/v1/auth/workstation-identify/`, `POST /api/v1/auth/workstation-lock/`, and `POST /api/v1/auth/signature-reauth/` with CSRF enforcement, session-backed auth behavior, and problem-details error responses.
- Added audited DRF throttle scopes for workstation identify and signature re-auth attempts, including rate-limit failure event capture.
- Added backend tests for workstation identify, switch-user, lock, signature re-auth success/failure, CSRF enforcement, rate limiting, hashed PIN verification, and audit metadata sanitation.
- Executed `make lint`, `make typecheck`, `make test`, `make architecture-check`, and `make check` successfully on 2026-03-13. `make check` reported one non-blocking React Doctor warning for an unused frontend type `ButtonProps`.

### Implementation Plan

- Extend `apps.authz` rather than introducing a parallel authentication stack.
- Use Django session login/logout primitives for identify and lock so the browser session remains authoritative.
- Keep signature authorization reusable and site-scoped by composing workstation PIN re-auth with existing site-role assignments.
- Introduce a narrow `apps.audit` persistence layer with sanitized metadata and explicit auth-event taxonomy.
- Cover the behavior with API-first tests and small unit tests for the reusable hashed PIN and audit sanitation helpers.

### Completion Notes List

- Implemented shared-workstation identify, switch-user, and lock flows on top of the existing Django session baseline without replacing normal admin/password authentication.
- Added signature step-up authorization via `POST /api/v1/auth/signature-reauth/`, enforcing site-scoped required roles and rejecting bad-PIN, wrong-role, and wrong-site requests server-side.
- Added canonical `apps.audit` event persistence for `identify`, `switch_user`, `lock_workstation`, `identify_failed`, `signature_reauth_succeeded`, and `signature_reauth_failed`.
- Added dedicated throttling plus auditable rate-limit failures for identify and signature re-auth endpoints.
- Documented the workstation auth contract and updated the authorization baseline note for future implementation stories.
- Verified the change set with targeted backend tests, full repo tests, lint, typecheck, architecture checks, security checks, and `make check`.

### File List

- _bmad-output/implementation-artifacts/1-3-implement-shared-workstation-identification-and-signature-authority-guardrails.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- backend/apps/audit/__init__.py
- backend/apps/audit/admin.py
- backend/apps/audit/apps.py
- backend/apps/audit/migrations/0001_initial.py
- backend/apps/audit/migrations/__init__.py
- backend/apps/audit/models.py
- backend/apps/audit/services.py
- backend/apps/audit/tests/__init__.py
- backend/apps/audit/tests/test_services.py
- backend/apps/authz/api/serializers.py
- backend/apps/authz/api/throttles.py
- backend/apps/authz/api/urls.py
- backend/apps/authz/api/views.py
- backend/apps/authz/domain/workstation.py
- backend/apps/authz/migrations/0002_user_workstation_pin.py
- backend/apps/authz/models.py
- backend/apps/authz/tests/helpers.py
- backend/apps/authz/tests/test_models.py
- backend/apps/authz/tests/test_signature_reauth.py
- backend/apps/authz/tests/test_workstation_api.py
- backend/config/settings/base.py
- docs/implementation/authorization-policy.md
- docs/implementation/workstation-auth.md

### Change Log

- 2026-03-13: Implemented shared-workstation identify/switch/lock flows, signature re-auth guardrails, canonical auth-event auditing, additive migrations, backend and security tests, and workstation auth documentation. Promoted story status to `review`.
- 2026-03-13: Code review fixes — added PIN min-length validation (4 chars), rejected empty PIN in model method, replaced hardcoded role choices with SiteRole.choices, narrowed exception catch in throttle, added client IP to audit metadata for failed auth events, extracted shared test helpers, added tests for lock CSRF/anonymous denial/self-identify edge case.
- 2026-03-13: Applied final review fixes for atomic identify/audit behavior, audited unknown-site signature failures, enforced model-level minimum workstation PIN length, added missing signature-failure IP metadata, and expanded regression coverage.

### Senior Developer Review (AI)

**Reviewer:** Axel  
**Date:** 2026-03-13  
**Outcome:** Approved after fixes

#### Summary

- Reviewed the committed Story 1.3 implementation directly; there were no staged or unstaged application source diffs to validate against git at review time.
- Fixed four review findings in the authz/audit flow and added regressions for the previously uncovered failure paths.
- Re-verified with:
  - `/home/axel/wsl_venv/bin/python -m pytest backend/apps/authz/tests/test_models.py backend/apps/authz/tests/test_workstation_api.py backend/apps/authz/tests/test_signature_reauth.py backend/apps/audit/tests/test_services.py`
  - `/home/axel/wsl_venv/bin/python -m ruff check backend/apps/authz/models.py backend/apps/authz/domain/workstation.py backend/apps/authz/api/views.py backend/apps/authz/tests/test_models.py backend/apps/authz/tests/test_workstation_api.py backend/apps/authz/tests/test_signature_reauth.py`

#### Findings

1. **[High] Identify needed to fail closed if audit persistence failed.**
   Fixed by rolling the request back to an unauthenticated state when the audit write raises after workstation identify.

2. **[High] Signature re-auth failures for unknown sites were not audited.**
   Fixed by recording `signature_reauth_failed` before re-raising `site_not_found`.

3. **[Medium] Minimum workstation PIN length was enforced only at the API serializer layer.**
   Fixed by enforcing the same minimum length in the `User.set_workstation_pin()` model helper.

4. **[Medium] Signature re-auth failure events were missing client IP metadata.**
   Fixed by attaching `ip_address` to invalid-credential, missing-role, and site-not-found signature failure events.
