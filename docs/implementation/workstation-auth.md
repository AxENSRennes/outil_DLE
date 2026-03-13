# Workstation Authentication and Signature Guardrails

This note documents the backend contract introduced in Story 1.3 for shared-workstation identification, lock, signature step-up authorization, and canonical auth-event auditing.

## Scope

This implementation provides backend primitives only:

- fast workstation identify using a dedicated user PIN
- explicit switch-user behavior on re-identify
- workstation lock that clears session authority
- signature step-up authorization for a site and required role set
- canonical audit events for auth-sensitive workstation actions

This implementation does not yet provide:

- operator workstation UI
- inactivity countdown UI
- batch route persistence in auth session state
- signature record persistence
- batch-step linkage or execution workflow state transitions

## Credential Model

`apps.authz.models.User` now carries a dedicated `workstation_pin` hash.

- The PIN is stored with Django password hashing utilities.
- Raw PIN values are never persisted.
- General Django/admin password authentication remains unchanged.

## API Endpoints

### `POST /api/v1/auth/workstation-identify/`

Request:

```json
{
  "username": "alice.operator",
  "pin": "2468"
}
```

Behavior:

- verifies the workstation PIN against the targeted active user
- creates a real Django session for that user
- if another user is active, replaces that authority and emits `switch_user`
- returns the active user and site-role context without redirect semantics

Success response shape:

```json
{
  "status": "identified",
  "event": "identify",
  "previous_user": null,
  "user": {
    "id": 1,
    "username": "alice.operator",
    "first_name": "Alice",
    "last_name": "Operator"
  },
  "site_assignments": []
}
```

### `POST /api/v1/auth/workstation-lock/`

Behavior:

- requires an authenticated session
- records a `lock_workstation` audit event
- calls Django logout to remove the active authenticated authority

Success response:

```json
{
  "status": "locked"
}
```

### `POST /api/v1/auth/signature-reauth/`

Request:

```json
{
  "site_code": "paris-line-1",
  "required_roles": ["operator"],
  "pin": "2468"
}
```

Behavior:

- requires an already authenticated Django session
- re-verifies the active user with workstation PIN
- validates the user holds at least one required site-scoped role for the supplied site
- returns authorized signer metadata without creating a signature record

Success response shape:

```json
{
  "status": "authorized",
  "site": {
    "id": 1,
    "code": "paris-line-1",
    "name": "Paris Line 1"
  },
  "signer": {
    "id": 1,
    "username": "alice.operator",
    "first_name": "Alice",
    "last_name": "Operator"
  },
  "authorized_roles": ["operator"]
}
```

## Security Guardrails

- Django session cookies remain the only browser auth authority.
- CSRF is enforced on all workstation auth POST endpoints.
- Identify and signature re-auth endpoints have dedicated DRF throttle scopes.
- Failure paths emit audit events for invalid credentials, missing role authorization, and rate-limited requests.
- Audit metadata is sanitized to avoid persisting raw PINs or other replayable secrets.

## Audit Event Taxonomy

Canonical event types in `apps.audit.models.AuditEventType`:

- `identify`
- `switch_user`
- `lock_workstation`
- `identify_failed`
- `signature_reauth_succeeded`
- `signature_reauth_failed`

Persisted audit attributes:

- actor when known
- timestamp via `occurred_at`
- event type
- site when known
- minimal structured metadata useful for troubleshooting

## Test Coverage

The backend test suite now covers:

- successful workstation identify and session establishment
- switch-user via re-identify
- workstation lock and immediate protected-endpoint denial
- signature re-auth success for valid site-role context
- signature re-auth denial for wrong role, wrong site, and bad PIN
- CSRF enforcement on auth-sensitive POST endpoints
- dedicated throttling on identify and signature re-auth
- audit persistence without raw PIN leakage
