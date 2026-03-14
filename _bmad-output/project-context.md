---
project_name: 'DLE-SaaS'
user_name: 'Axel'
date: '2026-03-13'
sections_completed:
  - technology_stack
  - language_rules
  - framework_rules
  - testing_rules
  - code_quality_style
  - workflow_rules
  - critical_rules
status: 'complete'
rule_count: 55
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Core Stack

- **Backend:** Django 5.2 LTS, Django REST Framework 3.16, drf-spectacular 0.29, Gunicorn 23 — Python 3.11+
- **Database:** PostgreSQL 17.x (not 18 — maturity/risk balance for regulated MVP)
- **Frontend:** React 19.1, TypeScript 5.8, Vite 7.3
- **Styling:** Tailwind CSS 4.2 + shadcn/ui + Radix UI (mandatory design-system baseline)
- **State/Forms:** TanStack Query v5 (server state), React Hook Form 7 + Zod 4 (forms), React Router 7 (routing)
- **Deployment:** Docker Compose (canonical runtime definition), single-region, separated dev/uat/prod

### Version Constraints

- PostgreSQL 17.x chosen over 18 for stability in regulated context — do not upgrade without explicit decision
- Django 5.2 is the LTS line — stay on this major version
- Python target is 3.11+ (`ruff target-version = "py311"`)
- Browser targets: Chrome 70+, Firefox 68+, Edge 79+ — enforced via `@vitejs/plugin-legacy`
- Desktop-only MVP: 1280x800 minimum, 1920x1080 standard — no mobile/tablet support

### Quality Tooling

- **Python lint/format:** ruff 0.11+ (replaces black + isort + multiple linters)
- **Python types:** mypy 1.10+ with django-stubs 5.0+
- **Python tests:** pytest 8.3+ with pytest-django 4.8+, factory-boy 3.3+ for fixtures
- **Frontend lint:** ESLint 9 with typescript-eslint, react-hooks, react-refresh plugins
- **Frontend types:** `tsc --noEmit` (strict mode enabled)
- **Frontend tests:** Vitest 3.0+ with jsdom, Testing Library (React 16.3+, user-event 14.6+, jest-dom 6.9+)
- **Architecture enforcement:** dependency-cruiser 17.3+ (frontend), `tools/check_backend_architecture.py` (backend)
- **Security:** bandit 1.7+ (Python security lint), pip-audit 2.8+ (dependency vulnerabilities), gitleaks (secret scanning)
- **React audit:** react-doctor (correctness, architecture, dead code, performance)
- **Quality gate:** `make check` runs all of the above — must pass before any feature is considered complete

## Critical Implementation Rules

### Language-Specific Rules

#### Python (Backend)

- ruff enforces line-length 100, double quotes, space indentation
- ruff lint selection: `B, E, F, I, RUF, SIM, UP` — bugs, pyflakes, isort, simplification, syntax upgrades
- mypy is strict: `disallow_untyped_defs`, `disallow_incomplete_defs`, `no_implicit_optional`, `check_untyped_defs` — relaxed only in test files
- Naming: modules/functions/variables `snake_case`, classes `PascalCase`
- Timestamp fields always end in `_at`: `created_at`, `updated_at`, `signed_at`
- Boolean fields always start with `is_`: `is_active`, `is_required`, `is_deleted`
- Foreign keys use `<entity>_id`: `batch_id`, `mmr_version_id`, `site_id`
- Table names use `snake_case` plural: `batches`, `batch_steps`, `review_events`
- Migrations must be additive expand/contract only — never destructive schema changes in the same deployment window (3x8 plant constraint)

#### TypeScript (Frontend)

- TypeScript strict mode is enabled — do not weaken compiler options
- Target ES2022, module ESNext, moduleResolution Bundler
- Path alias: `@/*` resolves to `./src/*` — always use it instead of relative paths
- Variables/functions: `camelCase`; types/interfaces/schemas: `PascalCase`; React components: `PascalCase`
- File naming: `kebab-case` for non-component modules, `PascalCase` for React component files
- API JSON payloads use `snake_case` (aligned with Django/DRF) — no camelCase translation at the API boundary
- Dates/datetimes use ISO 8601 strings with timezone
- Use explicit `null` for absent data — empty string is never a substitute for missing regulated data

### Framework-Specific Rules

#### Django / DRF (Backend)

- Modular monolith: each domain in `backend/apps/<domain>/` with sub-packages `api/`, `domain/`, `selectors/`, `tests/`
- Regulated business rules live in `domain/` — never in DRF serializers or API views
- `domain/` must not depend on `api/`; `api/` may call `domain/` and `selectors/`
- `backend/shared/` provides generic technical primitives — must not encode feature business rules
- Workflow transitions are explicit backend actions — no arbitrary PATCH on status fields
- Canonical MVP actions: `save_step_draft`, `complete_step`, `sign_step`, `request_correction`, `submit_for_pre_qa`, `confirm_pre_qa_review`, `mark_change_reviewed`, `return_for_correction`, `start_quality_review`, `release_batch`, `reject_batch`
- API errors use problem-details JSON format with stable machine-readable codes and user-safe messages
- OpenAPI generated via drf-spectacular as the canonical API contract
- Django session cookies are the only browser auth authority — no JWT/token auth
- All endpoints under `/api/v1` with explicit versioning

#### React (Frontend)

- Feature-domain organization: `features/execution/`, `features/pre-qa-review/`, `features/quality-review/`, `features/auth/`, `features/template-governance/`, `features/signatures/`, etc.
- shadcn/ui is mandatory: install via `npx shadcn@latest add <component>` from `frontend/` — components land in `@/shared/ui`
- Domain-specific components compose shadcn/ui primitives — never duplicate their functionality
- TanStack Query v5 for all server state — no Redux, Zustand, or global state store in MVP
- Local UI state stays in React primitives (`useState`, `useReducer`) — no unnecessary sharing
- React Hook Form 7 + Zod 4 for complex regulated forms with re-render control
- Features must not deep-import each other — cross-feature coordination through `app/` wiring or shared contracts
- `frontend/src/shared/` must remain dependency-light
- Route-level code splitting; no SSR (authenticated SPA, not a public content site)
- Validation UX: "reward early, punish late" — validate on blur, not on keystroke; defer empty-required errors until completion attempt
- Progressive auto-save with mandatory visible feedback (saving/saved/failed)
- Keyboard-first: all critical operator and reviewer actions must be keyboard-accessible
- Explicit loading/error states for every mutation (save, sign, submit-for-review, release) — never auto-retry sensitive writes without user intent

### Testing Rules

#### Backend

- pytest with `--strict-markers`, `--disable-warnings`, `--maxfail=1`
- `DJANGO_SETTINGS_MODULE = "config.settings.dev"` for test runs
- Tests co-located in each Django app: `backend/apps/<domain>/tests/` — separate modules for API, domain, and integration coverage where needed
- Cross-app and contract tests live in `backend/tests/` (integration/, contract/)
- factory-boy for readable fixtures — no JSON fixtures or hard-coded data in tests
- `disallow_untyped_defs` relaxed in test files; S101 (assert) ignored in test files
- Branch coverage enabled, source scoped to `backend/`

#### Frontend

- Vitest with jsdom environment, globals enabled
- Tests co-located with feature or component: `src/**/*.test.ts`, `src/**/*.test.tsx`
- Testing Library for component tests — user-event for interaction simulation
- Global test setup in `frontend/src/test/setup.ts`
- Wider UI integration tests in `frontend/src/tests/integration/`

#### Critical Testing Rules

- Every behavior change must include or update tests in the same domain area
- Security tests must verify: CSRF enforcement, throttling, audit persistence without PIN leakage, role/site denial
- Workflow transitions must be tested through backend action endpoints — never via direct model mutation
- Signature, review, and release paths require especially thorough failure-case coverage

### Code Quality & Style Rules

#### Project Organization

- Backend organized by business domain first (`apps/authz/`, `apps/batches/`, `apps/mmr/`, `apps/signatures/`, `apps/reviews/`, `apps/audit/`, etc.), then by technical layer (`api/`, `domain/`, `selectors/`)
- Frontend organized in 3 layers: `app/` (composition, routing, providers, layouts), `shared/` (primitives, API client, types, utils), `features/` (workflow-specific UI)
- Never use synonyms for the same domain concept — always use canonical names: `batch`, `batchStep`, `signatureMeaning`, `reviewEvent`, `changed_since_review`
- Internal domain events use past-tense business naming: `batch_started`, `step_signed`, `review_returned`

#### API Response Conventions

- Collections return direct resource lists or paginated DRF structures — no custom wrappers
- Single resources return the representation directly
- Errors use problem-details JSON with stable machine-readable codes
- Validation errors must be structurally predictable and field-addressable
- Workflow state must be exposed explicitly in responses — never force clients to infer state from raw audit history

#### API Naming

- REST resources use plural nouns: `/api/v1/batches`, `/api/v1/mmr-versions`
- Path segments use kebab-case where needed in URLs
- Query parameters use `snake_case`: `site_id`, `status`, `changed_since_review`

#### Quality Commands

- `make lint` — ruff + ESLint
- `make format` — ruff --fix + ruff format
- `make typecheck` — mypy + tsc --noEmit
- `make test` — pytest + vitest
- `make security` — bandit + pip-audit + gitleaks
- `make architecture-check` — backend + frontend boundary enforcement
- `make doctor` — react-doctor
- `make check` — runs the full suite; **must pass before any feature is considered complete**

### Development Workflow Rules

#### Git & Repository

- Feature branches: `feat/story-<epic>-<story>-<description>`
- Conventional Commits: `feat(scope):`, `fix(scope):`, `style:`, etc.
- PRs via GitHub with automated review
- CI via GitHub Actions (`quality.yml`) — runs lint, typecheck, tests, security

#### Deployment

- Docker Compose is the canonical deployment definition — application must remain runnable via plain Compose
- Separated environments: dev, uat, prod with explicit configuration separation
- Secrets must not live in the repository
- Conservative CI/CD: lint/tests → migration checks → container build → UAT promotion → production
- Releases must be rollback-ready — 3x8 plant operations with limited maintenance windows
- Expand/contract migrations only — no destructive schema changes in the same deployment window

#### Local Development

- Python venv: `/home/axel/wsl_venv` — all Python commands must use this environment
- Backend and frontend run independently in local dev
- All quality commands executed via `make` from the repo root
- Architecture boundaries enforced by automated tooling (dependency-cruiser + check_backend_architecture.py)

### Critical Don't-Miss Rules

#### Security — Fail-Closed

- Any security-critical operation (logout, session clear, token revocation) MUST be in a `finally` block — executes even if surrounding code (e.g. audit writes) raises
- When a fail-closed pattern is applied to one function, audit all sibling functions performing similar operations and apply consistently
- Before finishing a feature, review all new functions as a group — not just individually

#### Audit Trail — Immutability

- Django admin classes for audit/log models MUST override `has_add_permission`, `has_change_permission`, `has_delete_permission` to return `False`
- Audit records are append-only — never modified or deleted
- Never persist raw PINs in audit metadata — sanitize before storage

#### Credentials in Admin

- Any model field storing hashed or sensitive values (PINs, passwords, tokens) MUST be excluded from admin forms or marked as `readonly_fields`
- Never allow plain-text editing of hashed fields

#### Trust Boundaries

- Never blindly trust client-supplied headers (e.g. `X-Forwarded-For`) for security decisions
- Document trust assumptions when using such headers
- If a value from an untrusted source is stored, document that it is advisory/best-effort

#### Workflow & Domain Integrity

- Backend is the source of truth for all regulated workflow state — frontend never reconstructs review states from raw audit history
- Frontend state names must match backend exactly: `in_progress`, `awaiting_pre_qa`, `complete`, `signed`, `changed_since_review`, etc.
- Signatures are business events, not UI widgets — each signature stores: signer identity, server timestamp, signature meaning, related batch step, signed-state reference
- Step-up re-authentication is mandatory before any signature action, even when session is active
- Review flags (`changed_since_review`, `changed_since_signature`, `review_required`) are stored/derived in backend — never inferred only from audit trail in frontend
- Batch instances freeze a template snapshot at creation — later template changes must never mutate in-progress records

#### Shared Workstation Model

- PIN-based workstation identification via `POST /api/v1/auth/workstation-identify/`
- Explicit lock via `POST /api/v1/auth/workstation-lock/` — clears authenticated authority entirely
- Signature re-auth via `POST /api/v1/auth/signature-reauth/` — re-verifies active user with PIN and site-scoped role
- Identify and signature re-auth endpoints have dedicated throttle scopes
- Failed PIN attempts and identity actions must emit audit events
- `switch_user` replaces the prior authenticated session without losing batch context
- Persist draft field values on blur so user switches lose at most one field interaction

#### Anti-Patterns to Avoid

- Mixing `camelCase` and `snake_case` in API payloads
- Putting signature business rules inside React components
- Returning `{ success: true, data: ... }` on one endpoint and raw JSON on another
- Using generic names (`item`, `record`, `data`) when the domain object is `batch` or `review_event`
- Inventing parallel abstractions for workflow state, signatures, or review semantics
- Arbitrary PATCH on status fields — always use dedicated action endpoints
- Hiding review-relevant state changes in audit logs instead of exposing them explicitly in API responses

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Preserve canonical domain terms across backend, API, and frontend

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack or patterns change
- Review periodically for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-03-13
