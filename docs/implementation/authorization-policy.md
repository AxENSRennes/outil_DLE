# Authorization Policy Baseline

This document defines the initial site-aware authorization convention introduced in Story 1.2.

## Canonical Roles

Use these exact application role identifiers everywhere:

- `operator`
- `production_reviewer`
- `quality_reviewer`
- `internal_configurator`

These are stored in application code as `apps.authz.models.SiteRole`.

## Site Scoping Rule

- Roles are assigned per site, not globally.
- A user may hold different roles on different sites.
- The same `(user, site, role)` combination may exist only once.
- Authorization checks must treat the site as part of the access decision from the start.

The baseline site model lives in `apps.sites.models.Site` and currently carries:

- a stable `code`
- a human-readable `name`
- an `is_active` flag
- created/updated timestamps

## Enforcement Location

Authorization enforcement is backend-authoritative.

- Domain helpers live in [policies.py](/home/axel/DLE-SaaS/backend/apps/authz/domain/policies.py).
- Reusable DRF permission primitives live in [site_roles.py](/home/axel/DLE-SaaS/backend/shared/permissions/site_roles.py).
- The authenticated access-context read surface lives at `GET /api/v1/auth/context/`.
- A runtime authorization probe lives at `GET /api/v1/auth/sites/{site_code}/operator-access/` to prove server-side site-role denial on a shipped endpoint.

Frontend visibility is not access control. Later stories should reuse these helpers and permission classes instead of inventing feature-local role checks.

## Access-Context Contract

`GET /api/v1/auth/context/` returns:

- the authenticated user summary
- the authenticated user's site assignments only
- canonical role names grouped by site

This endpoint is informational only. Workstation identify/switch/lock flows and signature re-authentication now live in the dedicated workstation auth contract documented in [workstation-auth.md](/home/axel/DLE-SaaS/docs/implementation/workstation-auth.md).

## Workstation Authentication Contract

Story 1.3 extends the baseline with shared-workstation authentication guardrails while keeping Django sessions as the only browser auth authority.

Implemented action endpoints:

- `POST /api/v1/auth/workstation-identify/`
- `POST /api/v1/auth/workstation-lock/`
- `POST /api/v1/auth/signature-reauth/`

Rules:

- Workstation identification uses a dedicated hashed PIN credential stored on `authz.User`.
- A successful identify request creates or replaces the authenticated Django session without redirecting away from the current screen.
- `workstation-lock` removes the active authenticated authority entirely; protected endpoints return `not_authenticated` immediately afterward.
- `signature-reauth` re-verifies the active user with PIN and site-scoped role requirements before future signature-bearing actions.
- CSRF remains required on unsafe auth endpoints.
- Identify and signature re-auth requests are rate-limited and emit auditable failure events rather than failing silently.

Canonical auth-event types are:

- `identify`
- `switch_user`
- `lock_workstation`
- `lock_failed`
- `identify_failed`
- `signature_reauth_succeeded`
- `signature_reauth_failed`

## Custom User Model Cutover

Story 1.2 switches the project baseline to `AUTH_USER_MODEL = "authz.User"` while the platform is still in foundation mode.

- New environments should start from an empty database and apply the current migrations directly.
- Existing dev or UAT databases created before Story 1.2 need an explicit cutover before reuse.
- Follow [custom-user-model-cutover.md](/home/axel/DLE-SaaS/docs/implementation/custom-user-model-cutover.md) before pointing an already-initialized environment at this revision.
