- Use the Python virtual environment located at `/home/axel/wsl_venv` for any Python-related command, script, dependency installation, or test execution.

## Security & Defensive Coding Rules

### Fail-closed by default
- Any security-critical operation (logout, session clear, token revocation) MUST be in a `finally` block so it executes even if surrounding code (e.g. audit writes) raises.
- When implementing a fail-closed pattern on one function, audit all sibling functions that perform similar operations and apply it consistently.

### Pattern consistency
- When a security or architectural pattern is applied to one function, systematically check and apply it to all analogous functions in the same module.
- Before finishing a feature, review all new functions as a group — not just individually.

### Audit trail immutability
- Django admin classes for audit/log models MUST override `has_add_permission`, `has_change_permission`, and `has_delete_permission` to return `False`. Audit records are append-only.

### Credentials and secrets in admin
- Any model field that stores hashed or sensitive values (PINs, passwords, tokens) MUST be excluded from admin forms or marked as `readonly_fields`. Never allow plain-text editing of hashed fields.

### Trust boundaries on request data
- Never blindly trust client-supplied headers (e.g. `X-Forwarded-For`) for security decisions. Document trust assumptions when using such headers.
- If a value derived from an untrusted source is stored (e.g. in audit metadata), document that it is advisory/best-effort.

### General
- Run `make check` before considering any feature complete. All linters, type checks, tests, and security scans must pass.