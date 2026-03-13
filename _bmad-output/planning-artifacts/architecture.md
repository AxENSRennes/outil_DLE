---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
  - 7
  - 8
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/prd-validation-report.md
  - docs/decisions/transcript-product-decisions.md
  - docs/decisions/architecture-decisions.md
workflowType: 'architecture'
project_name: 'DLE-SaaS'
user_name: 'Axel'
date: '2026-03-07T02:27:26+01:00'
lastStep: 8
status: 'complete'
completedAt: '2026-03-07T03:23:50+01:00'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The project defines 51 functional requirements across six architectural capability groups. The first group covers template governance, including MMR creation, versioning, activation, and batch instantiation from a governed template version. The second group covers batch execution, including step-based data entry, progressive save, completion gating, contributor attribution, and execution signatures in a shared-workstation context.

The third group focuses on trust semantics: audit trail preservation, controlled corrections, reason-for-change capture, explicit re-review triggering, and visibility of changed states after review or signature. The fourth group defines distinct review workflows for production pre-QA review and quality review, including dossier completeness assessment, issue visibility, review disposition, and release-readiness representation. The fifth group establishes role-based governance boundaries across operators, production reviewers, quality reviewers, and internal configurators, with future compatibility for site and organization scoping. The sixth group covers dossier output, governed calculations, contextual references, structured attachments, conditional dossier composition, repeated controls, checklist completeness, cross-document consistency validation, and integration readiness without requiring ERP or WMS coupling in MVP.

**Non-Functional Requirements:**
The non-functional requirements place strong pressure on architectural correctness rather than scale-out complexity. Performance targets require responsive step navigation, save behavior, and review screens under pilot load. Security requirements require attributable actions, strict RBAC enforcement, signature integrity, protected regulated data, and control over template activation and administrative changes. Reliability requirements include recovery consistency, daily backup expectations, documented degraded-mode operations, and restoration of in-progress execution and review state after restart or failure. Accessibility and usability requirements emphasize keyboard operability, narrow execution flows, clear validation feedback, and usability on shared industrial workstations. Integration requirements require versioned contracts around core dossier objects and exports while keeping the MVP operationally independent from live enterprise integrations.

**Scale & Complexity:**
This project is a high-complexity regulated workflow application rather than a high-scale consumer platform. Its complexity comes from trust, governance, auditability, review-state semantics, and regulated record integrity. The system must support multiple business roles, template lifecycle control, immutable batch instantiation semantics, progressive execution, structured review flows, dossier exports, and future site-aware expansion.

- Primary domain: Full-stack web application for regulated electronic batch record workflow
- Complexity level: High
- Estimated architectural components: 9-11

### Technical Constraints & Dependencies

The MVP must remain independent from mandatory ERP and WMS integrations. The architecture must preserve portability and avoid dependence on heavy enterprise infrastructure. Shared-workstation operation is a hard constraint, requiring continuity, attribution, and signature integrity across multiple contributors. The plant operates in a 3x8 model, which adds operational deployment constraints: limited maintenance windows, stronger rollback expectations, careful release communication across shifts, and a need for degraded-mode continuity if an update causes disruption during active production. Batch instances must preserve a frozen template snapshot so later template changes do not mutate in-progress records. Critical calculations derived from Excel logic must be governed on the backend. Review-relevant states must be explicit in the user experience and data model rather than buried in audit logs. The product must also support a documented degraded operating mode for continuity during outage or infrastructure failure.

### Cross-Cutting Concerns Identified

The major cross-cutting concerns are audit trail integrity, signature semantics, role-based authorization, versioned template governance, batch snapshot immutability, review-state transitions after change, reason-for-change traceability, dossier export consistency, site-aware domain scoping, operational resilience, and release-management discipline for a 3x8 production environment. These concerns affect nearly every bounded area of the system and will need explicit architectural treatment before implementation details are finalized.

## Starter Template Evaluation

### Primary Technology Domain

Split full-stack web application based on project requirements analysis.

The project needs a dedicated backend for regulated domain logic, signatures, auditability, review-state transitions, and governed calculations, plus a separate frontend optimized for operator execution and review workflows. This makes a split backend/frontend foundation more suitable than a single full-stack meta-framework.

### Starter Options Considered

**Option 1: Official split-stack foundation (Django + Vite React TypeScript)**
This option uses the official Django project bootstrap for the backend and the official Vite React TypeScript template for the frontend. It keeps backend and frontend concerns clearly separated, matches the existing documented stack preference, and introduces minimal premature framework opinion.

**Option 2: Next.js via create-next-app**
This is a current and well-maintained starter with strong defaults. However, it biases the architecture toward a unified React server framework, App Router conventions, Tailwind by default, and a tighter coupling between UI and backend delivery. That conflicts with the current preference for Django as the primary domain backend and would blur the API boundary too early.

**Option 3: Cookiecutter Django plus separate frontend**
This provides a more batteries-included backend starting point. However, it brings more up-front decisions than this project currently needs, including broader infrastructure and server-rendering assumptions. For a regulated MVP where domain clarity matters more than scaffolding breadth, it is more opinionated than necessary.

### Selected Starter: Official Split-Stack Foundation

**Rationale for Selection:**
This starter aligns with the architecture direction already documented for the project: Django 5.2 LTS backend, DRF-based API layer, React + TypeScript + Vite frontend, PostgreSQL, and Docker Compose portability. It preserves a clean boundary between regulated business logic and user-interface concerns, supports separate operator and review surfaces, and avoids accidental commitment to a monolithic frontend framework. It also keeps the first implementation story focused on domain spine and API design rather than on unwinding boilerplate decisions from a more opinionated meta-framework.

**Initialization Command:**

```bash
/home/axel/wsl_venv/bin/python -m django startproject config backend
npm create vite@latest frontend -- --template react-ts
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
Python backend on the Django 5.2 LTS line, and a TypeScript frontend scaffolded from the official Vite React template. This keeps the backend on a long-support framework line while giving the frontend strict typing from day one.

**Styling Solution:**
Standardize the frontend on Tailwind CSS 4 with shadcn/ui components built on Radix UI primitives. This converts the UX design-system decision into an implementation constraint and gives the project keyboard-safe primitives, controlled component ownership, and a sober industrial baseline without introducing a larger app framework.

**Build Tooling:**
Django provides the standard management-command project structure for backend initialization. Vite provides the frontend development server, bundling pipeline, and production build tooling. On the frontend, the baseline also includes PostCSS via Tailwind, Autoprefixer, and `@vitejs/plugin-legacy` targeting `es2015` so the supported desktop-browser matrix from UX remains technically enforced.

**Testing Framework:**
Use Django's standard test framework and pytest-compatible tooling on the backend, and Vitest on the frontend with `axe-core` for component accessibility checks. Run Lighthouse CI accessibility checks in the quality pipeline for supported operator and reviewer surfaces.

**Code Organization:**
The starter establishes a clean two-application structure: `backend/` for regulated domain logic and API implementation, and `frontend/` for the execution and review user interfaces. Within the frontend, the canonical organization is `app/`, `shared/`, and `features/`: shared primitives such as shadcn/ui live under `frontend/src/shared/ui/`, while domain composites remain inside their owning feature modules.

**Development Experience:**
The foundation gives a fast local workflow with Django autoreload on the backend and Vite hot-module reloading on the frontend. It minimizes generated complexity and makes the first implementation story straightforward to reason about.

**Note:** Project initialization using this command should be the first implementation story. DRF, drf-spectacular, PostgreSQL configuration, Docker Compose wiring, and project-wide testing/tooling should be added immediately after scaffold creation as part of the initial platform story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- PostgreSQL 17.x as the authoritative system of record
- Hybrid relational + JSONB data model
- Expand/contract migration strategy for 3x8-compatible releases
- Django session-based authentication with step-up re-authentication for signatures
- Site-scoped RBAC enforced in backend domain services
- REST API with explicit versioning under `/api/v1`
- Problem-details error format and OpenAPI-first contract publication
- React Router 7 + TanStack Query v5 + React Hook Form 7 + Zod 4 on the frontend
- Tailwind CSS 4 + shadcn/ui + Radix UI as the mandatory frontend component baseline
- Shared-workstation session model with PIN-based identification, lock, switch-user, and signature re-authentication
- Canonical workflow states, derived review severities, and explicit transition actions owned by backend services
- MVP action contracts for auto-save, signatures, corrections, pre-QA review, quality disposition, and dossier integrity summaries
- Backend dossier-composition service for conditional forms, repeated controls, checklist completeness, and cross-document rule evaluation
- Single-region Docker Compose deployment baseline with strict rollback discipline

**Important Decisions (Shape Architecture):**
- No business-critical cache in MVP; database remains the single source of truth
- No microservices or message bus in MVP; modular monolith with async jobs only where operationally necessary
- No global client-state library initially; server state via TanStack Query, local workflow state via React primitives
- Structured logging, health checks, audit instrumentation, and release gates as first-class operational concerns

**Deferred Decisions (Post-MVP):**
- Redis as a dedicated infrastructure dependency
- WebSockets / real-time collaborative editing
- GraphQL
- Offline-first synchronization
- Multi-tenant runtime isolation model
- Workflow engine adoption
- Search infrastructure beyond PostgreSQL capabilities

### Data Architecture

**Primary Database: PostgreSQL 17.x**
Use PostgreSQL 17 on the current supported minor line as the primary transactional datastore. PostgreSQL 18 is the current major release, but PostgreSQL 17 offers a better maturity/risk balance for a regulated MVP while remaining supported for several years.

**Modeling Strategy:**
Adopt a hybrid relational + JSONB model:
- relational tables for `MMR`, `MMRVersion`, `Batch`, `BatchStep`, `Signature`, `ReviewEvent`, `ReleaseEvent`, `Exception`, `AuditEvent`, attachments, users, roles, sites
- `jsonb` for versioned template definitions, field schemas, conditional rules, step payload details, and frozen batch snapshots

**Validation Strategy:**
Validation is layered:
- frontend validation for immediate UX feedback using Zod 4 and React Hook Form 7
- DRF serializer validation for request-shape and field-level API guarantees
- domain-service validation for business invariants such as signing semantics, review-state transitions, snapshot immutability, and release gating

**Migration Strategy:**
Use additive-first expand/contract migrations only:
- add new structures before switching reads/writes
- backfill explicitly
- remove deprecated columns only in later releases
- avoid destructive schema changes in the same deployment window
This is required for low-risk operation in a 3x8 plant with limited maintenance windows.

**Caching Strategy:**
Do not introduce a business-data cache in MVP. The database remains the single source of truth for regulated workflow state. Any future cache must be non-authoritative and limited to technical concerns such as throttling, ephemeral task coordination, or low-risk read acceleration.

### Authentication & Security

**Authentication Method:**
Use Django authentication with secure, server-managed session cookies for the web app. This fits a browser-based internal product and reduces token-handling complexity on shared workstations.

**Signature Security Pattern:**
Require step-up re-authentication for electronic signature actions, even when the session is active. Signature events must bind:
- authenticated user
- server timestamp
- signature meaning
- related batch step or review action
- signed-state reference

**Authorization Pattern:**
Implement role- and site-scoped authorization in backend services, not only in the UI. Core roles remain:
- Operator
- Production Reviewer
- Quality Reviewer
- Internal Configurator/Admin

**API Security Strategy:**
Use same-origin API access with HttpOnly secure cookies, CSRF protection, strict CORS policy, audit logging on auth/signature events, and rate limiting on authentication and signature-sensitive endpoints. RBAC checks must be enforced server-side on every state-changing action.

**Encryption Approach:**
Use TLS in transit, encrypted volumes/backups at the infrastructure layer, and strong secret separation for credentials and keys. Do not introduce field-level encryption for core dossier business data in MVP unless a specific compliance need emerges, because it would reduce queryability and complicate review workflows.

### API & Communication Patterns

**API Style:**
Use REST as the primary application contract. It matches the split-stack architecture, DRF strengths, explicit workflow resources, and OpenAPI generation requirements.

**Versioning:**
Publish the application API under `/api/v1` and preserve backward compatibility within the MVP line.

**Documentation Approach:**
Use drf-spectacular 0.29 to generate and publish OpenAPI documentation as the canonical API contract for frontend and future integrations.

**Error Handling Standard:**
Adopt a consistent problem-details JSON format for API errors, with stable machine-readable codes and explicit user-safe messages.

**Service Communication:**
Keep all core workflow logic inside the modular monolith. Internal communication happens through Python modules and service boundaries, not network calls. Async jobs may be introduced later for exports, notifications, or other non-interactive work.

### Frontend Architecture

**Routing:**
Use React Router 7 for client-side routing across the main application surfaces:
- operator execution
- pre-QA review
- quality review
- configuration/admin

**Server State:**
Use TanStack Query v5 for API fetching, caching, invalidation, and optimistic update handling where safe.

**Form Architecture:**
Use React Hook Form 7 with Zod 4 schemas for complex step forms. This is a strong fit for large regulated forms where re-render control and typed validation matter.

**Client State Strategy:**
Do not introduce Redux, Zustand, or another global state store in MVP by default. Keep local UI state in React primitives and reserve shared app state for routing, auth session context, and query cache concerns.

**Component Organization:**
Organize the frontend by domain feature areas rather than by technical layer alone. Shared UI primitives should remain separate from batch-execution, review, signature, and template-governance feature modules.

**Performance Strategy:**
Use route-level code splitting, query prefetching only where it improves review workflows, and explicit loading/error states. Avoid SSR complexity because the application is an authenticated operational SPA, not a public content product.

**Design System & Styling Baseline:**
Use Tailwind CSS 4 for styling tokens and layout utilities, shadcn/ui for owned UI primitives, and Radix UI for dialog, sheet, dropdown, and focus-management behavior. The canonical placement is:
- `frontend/src/shared/ui/` for shadcn/ui primitives and token-aware wrappers
- `frontend/src/features/execution/components/` for operator composites such as `StepExecutor`, `StepSidebar`, `IdentityBanner`, and `SaveIndicator`
- `frontend/src/features/pre-qa-review/components/` and `frontend/src/features/quality-review/components/` for review composites such as `ReviewExceptionList`, `DossierIntegritySummary`, and `ChangeHistoryBlock`

**Browser & Accessibility Baseline:**
Target desktop browsers only for MVP, with explicit support for Chrome 70+, Firefox 68+, and Edge 79+ on 1280x800 and 1920x1080 workstations. Keep keyboard-first behavior, focus management, `aria-live` save feedback, and redundant color/icon/text state coding as non-optional frontend architecture requirements rather than UX suggestions. The frontend implementation must also support the workstation-speed expectations defined in the UX artifact for operator identification, inline signature re-authentication, and rapid resume on shared workstations.

### Shared Workstation Operating Model

**Session Model:**
Use Django's authenticated session cookie as the authoritative identity session for browser access. On a shared workstation, `Identify` replaces the current authenticated user session with the operator's session while preserving the current batch route and server-safe draft state in the UI.

**Identification Pattern:**
Use a short PIN flow for workstation identification and step-up signature re-authentication:
- `identify` authenticates the active user for the workstation session
- `switch_user` terminates the prior authenticated session and prompts a new PIN without losing the active batch context
- `lock_workstation` clears the active authenticated identity after inactivity or explicit lock while keeping the screen on the batch context
- `signature_reauth` re-verifies the already identified user immediately before any signature-bearing action

The UX artifact remains the source of truth for the exact timing expectations of these flows; the architecture must support them without introducing extra redirects, full-login round-trips, or batch-context loss during user switching and signing.

**Operational Rules:**
- Persist draft field values on blur so user switches lose at most one field interaction
- Keep current route and selected batch context client-side; never keep the prior user's authenticated authority alive after a switch
- Record audit events for `identify`, `switch_user`, `lock_workstation`, failed PIN attempts, and signature re-authentication
- Rate limit PIN and signature re-authentication endpoints independently from general page traffic

### Workflow State Model & Transitions

**Canonical Batch Lifecycle States:**
- `in_progress`
- `awaiting_pre_qa`
- `in_pre_qa_review`
- `awaiting_quality_review`
- `in_quality_review`
- `returned_for_correction`
- `released`
- `rejected`

**Canonical Step States:**
- `not_started`
- `in_progress`
- `complete`
- `signed`

**Review-Relevant Flags and Derived States:**
- `missing_required_data`
- `missing_required_signature`
- `changed_since_review`
- `changed_since_signature`
- `review_required`
- `has_open_exception`

These flags may coexist with lifecycle states. They are stored or derived in backend read models and must never be inferred only from raw audit history in the frontend.

**Derived Review Severity Summary:**
- `green`: no missing data, no missing signatures, no pending re-review, no blocking exceptions
- `amber`: dossier is navigable but requires reviewer attention because of changes, notes, or non-blocking issues
- `red`: dossier is blocked for handoff or release because required data, required signatures, or blocking exceptions remain unresolved

**Transition Rules:**
All regulated workflow changes occur through explicit backend actions. The canonical action set for MVP is:
- `save_step_draft`
- `complete_step`
- `sign_step`
- `request_correction`
- `submit_for_pre_qa`
- `confirm_pre_qa_review`
- `mark_change_reviewed`
- `return_for_correction`
- `start_quality_review`
- `release_batch`
- `reject_batch`

Direct arbitrary PATCH semantics on batch status, review status, or signature state are forbidden.

### MVP Public Contracts

**Contract Style:**
Keep the public API REST-first under `/api/v1`, with problem-details errors and stable machine-readable codes. The first OpenAPI publication must cover action-style endpoints in addition to CRUD resources because the workflow is action-driven.

**Required MVP Actions and Read Models:**
- `POST /api/v1/auth/workstation-identify`
  Payload: `pin`
  Returns: authenticated user summary for the `IdentityBanner` and active role/site context
- `POST /api/v1/auth/workstation-lock`
  Payload: none
  Returns: locked workstation state with no active user identity
- `POST /api/v1/batch-steps/{id}/draft`
  Payload: partial step field values
  Returns: canonical step read model including validation state and `saved_at`
- `POST /api/v1/batch-steps/{id}/complete`
  Payload: optional completion note
  Returns: canonical step state plus next-step hint if available
- `POST /api/v1/batch-steps/{id}/sign`
  Payload: `signature_meaning`, `pin`
  Returns: signature manifest with signer, role, meaning, timestamp, and resulting step state
- `POST /api/v1/batch-steps/{id}/corrections`
  Payload: corrected values plus `reason_for_change`
  Returns: correction receipt with `correction_id`, `step_id`, `corrected_at`, `corrected_by`, and the applied old/new values
- `GET /api/v1/batches/{id}/execution`
  Returns: batch execution read model including sidebar steps, active-step detail, current identity context, and save status metadata
- `GET /api/v1/batches/{id}/review-summary`
  Returns: dossier completeness checklist, traffic-light severity, missing-signature counts, change counters, and open exceptions
- `POST /api/v1/batches/{id}/pre-qa-review/confirm`
  Payload: optional review note
  Returns: updated batch lifecycle state and persistent review note summary
- `POST /api/v1/batches/{id}/review-items/{item_id}/mark-reviewed`
  Payload: optional reviewer note
  Returns: updated item review status and refreshed summary counters
- `POST /api/v1/batches/{id}/quality-disposition`
  Payload: `decision` in `release|return_for_correction|reject`, optional note, and `pin` when the decision is a release signature
  Returns: updated dossier integrity summary and batch lifecycle state

**Canonical Read Models:**
The frontend should rely on centrally defined response types for:
- `StepStatus`
- `ChangeHistoryEntry`
- `ReviewSeveritySummary`
- `ChecklistCompleteness`
- `DossierIntegritySummary`

### Dossier Composition & Export Strategy

**Composition Service:**
Implement a backend-owned dossier composition service that resolves the expected dossier structure from batch context such as line, format family, and paillette presence. This service is responsible for:
- choosing required sub-documents
- generating repeated in-process and box-level control records
- computing the expected document checklist for review
- evaluating cross-document consistency rules

The frontend consumes the composed dossier structure and completeness outputs; it does not own business rule evaluation for required forms or cross-document checks.

**Export Strategy:**
Keep MVP dossier export synchronous in the request/response path for the representative batch flow. Backend export services generate the current dossier snapshot and associated integrity summary without introducing a queue dependency in v1. Async execution remains deferred until export volume or archival integrations require it.

### Infrastructure & Deployment

**Hosting Strategy:**
Deploy the MVP as a single-region environment with Docker Compose as the source of truth. A platform wrapper may be used operationally, but plain Compose must remain the canonical deployment definition.

**Environment Strategy:**
Maintain separate `dev`, `uat`, and `prod` environments with explicit configuration separation. Secrets must not live in the repository.

**CI/CD Approach:**
Use a conservative CI/CD pipeline with:
- linting and tests
- schema migration checks
- container build validation
- explicit promotion to UAT before production
- rollback-ready releases

**Observability:**
Adopt structured application logs, audit-event instrumentation, readiness/liveness checks, and error monitoring from the first platform story. Release health must be visible quickly because the plant operates continuously.

**Scaling Strategy:**
For MVP, optimize for correctness and operability rather than distributed scale:
- one primary PostgreSQL instance
- stateless app containers
- vertical scaling first
- horizontal scaling only after proven need

### Decision Impact Analysis

**Implementation Sequence:**
1. Initialize split-stack project structure
2. Establish PostgreSQL-backed Django platform and settings model
3. Implement core domain entities and migration discipline
4. Implement authentication, RBAC, and signature security flow
5. Publish first OpenAPI contract and frontend API client conventions
6. Build frontend routing, query layer, and step-form foundation
7. Add audit instrumentation, health checks, and release controls
8. Deliver first end-to-end batch execution and review slice

**Cross-Component Dependencies:**
- The hybrid data model depends on the migration strategy and API shape staying stable
- Session auth and signature re-authentication shape both frontend UX and backend audit design
- REST resource boundaries influence frontend feature modules and review surfaces
- 3x8 operational constraints directly affect migration design, release sequencing, rollback strategy, and observability requirements
- Deferring Redis, microservices, and offline mode keeps the MVP architecture simpler and lowers operational risk

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
5 major areas where AI agents could make incompatible choices:
- naming conventions
- project structure
- API/data formats
- workflow/state communication
- process handling for errors, loading, and validation

### Naming Patterns

**Database Naming Conventions:**
- Table names use `snake_case` plural nouns: `batches`, `batch_steps`, `review_events`
- Primary keys use `id`
- Foreign keys use `<entity>_id`: `batch_id`, `mmr_version_id`, `site_id`
- Timestamp columns use `_at`: `created_at`, `updated_at`, `signed_at`
- Boolean fields read as state flags: `is_active`, `is_required`, `is_deleted`
- Indexes and constraints use descriptive `snake_case` names, prefixed by type where useful: `idx_batches_site_id`, `uq_mmr_versions_mmr_id_version`

**API Naming Conventions:**
- REST resources use plural nouns: `/api/v1/batches`, `/api/v1/mmr-versions`
- Path segments use kebab-case only when needed in URLs, but resource names stay readable and stable
- Path parameters use IDs in the route and `snake_case` in backend naming
- Query parameters use `snake_case`: `site_id`, `status`, `changed_since_review`
- JSON payload fields use `snake_case` across the API to stay aligned with Django/DRF and reduce translation ambiguity

**Code Naming Conventions:**
- Python modules, packages, functions, and variables use `snake_case`
- Python classes use `PascalCase`
- React components use `PascalCase`
- TypeScript variables and functions use `camelCase`
- TypeScript types, interfaces, and schemas use `PascalCase`
- Frontend file names use kebab-case for non-component modules and `PascalCase` for React component files
- Avoid synonyms for the same domain concept: always use canonical names such as `batch`, `batchStep`, `signatureMeaning`, `reviewEvent`

### Structure Patterns

**Project Organization:**
- Organize both backend and frontend primarily by domain feature, not only by technical layer
- Backend domain modules should keep API, services, selectors/query logic, and tests close to the relevant business area
- Frontend features should be separated by workflow area: execution, pre-qa-review, quality-review, template-governance, auth
- Shared primitives go in clearly marked shared modules and must stay dependency-light

**File Structure Patterns:**
- Backend tests live close to their Django apps, with separate modules for API, domain, and integration coverage where needed
- Frontend tests are co-located with the feature or component they validate
- API schemas and contracts have a single authoritative location
- Documentation for cross-cutting rules lives in architecture or project-context artifacts, not hidden in code comments only
- Environment files follow explicit environment naming and are never used as an ad hoc configuration dump

### Format Patterns

**API Response Formats:**
- Successful collection responses return direct resource lists or paginated DRF structures, not custom wrappers unless there is a strong reason
- Successful single-resource responses return the resource representation directly
- Error responses use a standard problem-details style shape with stable machine-readable codes
- Validation errors remain structurally predictable and field-addressable
- Audit-relevant endpoints must expose workflow state explicitly, not force clients to infer it from raw change history

**Data Exchange Formats:**
- API JSON uses `snake_case`
- Dates and datetimes use ISO 8601 strings with timezone
- Booleans use `true` / `false`
- Null is used explicitly when data is absent; empty string is not a substitute for missing regulated data
- Enumerated workflow states must use canonical string values defined centrally

### Communication Patterns

**Event System Patterns:**
- Internal domain events use past-tense business naming such as `batch_started`, `step_signed`, `review_returned`
- Event payloads carry identifiers, actor, timestamp, and minimal business context
- Event naming stays domain-oriented, not UI-oriented
- No external event bus is required in MVP; these patterns primarily govern internal service boundaries and audit instrumentation

**State Management Patterns:**
- Backend is the source of truth for regulated workflow state
- Frontend server state is managed through TanStack Query
- Frontend local UI state stays local unless truly shared
- Workflow transitions must be expressed as explicit backend actions, not implicit field mutations
- Review and signature state changes always flow through dedicated service methods or endpoints

### Process Patterns

**Error Handling Patterns:**
- Distinguish user-facing business errors from technical failures
- Business-rule failures return stable codes and clear operator/reviewer-safe messages
- Unexpected failures are logged with structured context and surfaced to users in generic safe language
- Do not leak stack traces or infrastructure details to clients
- Signature, review, and release actions must have especially consistent failure handling

**Loading State Patterns:**
- Use local loading indicators for local actions and route/feature-level loading for major screen transitions
- Avoid global blocking spinners unless the whole screen is truly unavailable
- Mutation states must be explicit for save, sign, submit-for-review, return-for-correction, and release actions
- Retry behavior must be deliberate; never auto-retry sensitive write actions like signatures without explicit user intent

### Enforcement Guidelines

**All AI Agents MUST:**
- preserve canonical domain terms and state names across backend, API, and frontend
- keep regulated business rules in backend domain services, not only in serializers or UI code
- use the agreed JSON, naming, and error-response conventions consistently
- avoid inventing parallel abstractions for workflow state, signatures, or review semantics
- add or update tests in the same domain area as the changed behavior

**Pattern Enforcement:**
- Verify naming and structure through code review and lint/test checks
- Use `tools/check_backend_architecture.py` to enforce backend placement and import boundaries
- Use `frontend/dependency-cruiser.cjs` and `npm --prefix frontend run architecture-check` to enforce frontend import boundaries
- Treat deviations from canonical workflow naming or API shape as architectural issues
- Record intentional pattern changes in architecture artifacts before broad adoption

### Pattern Examples

**Good Examples:**
- `POST /api/v1/batches/{id}/signatures`
- `BatchService.return_for_correction(...)`
- `frontend/src/features/pre-qa-review/api/get-batch-review.ts`
- `changed_since_review` as a canonical API field and domain concept
- `signed_at` as a timestamp field name across persistence and API layers

**Anti-Patterns:**
- Mixing `camelCase` and `snake_case` randomly in API payloads
- Putting signature business rules inside React components
- Returning `{ success: true, data: ... }` on one endpoint and raw JSON on another without a rule
- Using generic names like `item`, `record`, or `data` where the domain object is actually `batch` or `review_event`
- Letting frontend-only state names diverge from backend workflow state names

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
DLE-SaaS/
├── README.md
├── Makefile
├── pyproject.toml
├── .gitignore
├── .github/
│   └── workflows/
│       └── quality.yml
├── docs/
│   ├── README.md
│   ├── decisions/
│   └── implementation/
├── tools/
│   └── check_backend_architecture.py
├── backend/
│   ├── README.md
│   ├── manage.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   ├── uat.py
│   │   │   └── prod.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   └── api.py
│   ├── apps/
│   │   ├── authz/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── sites/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── mmr/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── batches/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── signatures/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── reviews/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── releases/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── exceptions/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── audit/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   ├── exports/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   └── tests/
│   │   ├── references/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── selectors/
│   │   │   └── tests/
│   │   └── integrations/
│   │       ├── api/
│   │       ├── domain/
│   │       ├── selectors/
│   │       └── tests/
│   ├── shared/
│   │   ├── auth/
│   │   ├── database/
│   │   ├── errors/
│   │   ├── events/
│   │   ├── logging/
│   │   ├── pagination/
│   │   ├── permissions/
│   │   ├── time/
│   │   └── types/
│   ├── scripts/
│   │   └── seed_demo_data.py
│   ├── templates/
│   ├── static/
│   └── tests/
│       ├── conftest.py
│       ├── integration/
│       └── contract/
├── frontend/
│   ├── README.md
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── eslint.config.js
│   ├── vitest.config.ts
│   ├── dependency-cruiser.cjs
│   ├── index.html
│   ├── public/
│   │   └── assets/
│   └── src/
│       ├── main.tsx
│       ├── app/
│       │   ├── router.tsx
│       │   ├── providers/
│       │   ├── layouts/
│       │   └── styles/
│       ├── shared/
│       │   ├── api/
│       │   ├── config/
│       │   ├── lib/
│       │   ├── types/
│       │   ├── ui/
│       │   └── utils/
│       ├── features/
│       │   ├── auth/
│       │   ├── execution/
│       │   ├── pre-qa-review/
│       │   ├── quality-review/
│       │   ├── template-governance/
│       │   ├── signatures/
│       │   ├── exceptions/
│       │   └── dossier-exports/
│       └── tests/
│           ├── integration/
│           └── fixtures/
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── compose/
│   ├── compose.dev.yml
│   ├── compose.uat.yml
│   └── compose.prod.yml
└── .env.example
```

### Architectural Boundaries

**API Boundaries:**
- All external application endpoints live under `/api/v1`
- Django app `api/` packages expose serializers, views, routers, and request/response contracts only
- Authentication, site access, review permissions, and signature authorization are enforced server-side before domain transitions execute
- OpenAPI generation is centralized from the DRF layer and published as the canonical contract

**Component Boundaries:**
- `frontend/src/app` owns composition, routing, providers, and top-level layout only
- `frontend/src/shared` contains dependency-light primitives and common utilities
- `frontend/src/features/*` owns workflow-specific UI, API hooks, schemas, and tests
- Features do not deep-import each other directly; cross-feature coordination happens through app wiring or shared contracts

**Service Boundaries:**
- `backend/apps/*/domain` owns business rules and workflow transitions
- `backend/apps/*/api` can call domain services and selectors, but domain code cannot depend on API packages
- `backend/apps/*/selectors` owns optimized reads and query composition
- `backend/shared` provides generic technical primitives and must not encode feature business rules

**Data Boundaries:**
- PostgreSQL is the system of record for all regulated workflow state
- Relational entities own identity, status, attribution, and review/signature history
- JSONB is limited to configurable template/step schema and frozen snapshot payloads
- No cache is authoritative in MVP
- External integrations must depend on published contracts, not on direct table coupling

### Requirements to Structure Mapping

**Feature/FR Mapping:**
- Template governance FRs live in `backend/apps/mmr/` and `frontend/src/features/template-governance/`
- Batch execution FRs live in `backend/apps/batches/` and `frontend/src/features/execution/`
- Signature and traceability FRs live in `backend/apps/signatures/`, `backend/apps/audit/`, and `frontend/src/features/signatures/`
- Pre-QA and quality review FRs live in `backend/apps/reviews/`, `backend/apps/releases/`, `frontend/src/features/pre-qa-review/`, and `frontend/src/features/quality-review/`
- Exception/deviation handling FRs live in `backend/apps/exceptions/` and `frontend/src/features/exceptions/`
- Export and dossier output FRs live in `backend/apps/exports/` and `frontend/src/features/dossier-exports/`
- Site/RBAC/auth FRs live in `backend/apps/authz/`, `backend/apps/sites/`, and `frontend/src/features/auth/`

**Cross-Cutting Concerns:**
- Authentication/session concerns live in `backend/apps/authz/` and `backend/shared/auth/`
- Permissions and policy enforcement live in `backend/shared/permissions/`
- Error contract and problem-details formatting live in `backend/shared/errors/` and `frontend/src/shared/api/`
- Logging and audit instrumentation live in `backend/shared/logging/` and `backend/apps/audit/`
- Frontend API client setup and query conventions live in `frontend/src/shared/api/`

### Integration Points

**Internal Communication:**
- Frontend features communicate with the backend only through typed API clients and query/mutation hooks
- Backend app APIs call domain services and selectors inside the modular monolith
- Domain events are internal and business-oriented, used for auditability and future async work

**External Integrations:**
- ERP/WMS integration remains deferred and must enter through `backend/apps/integrations/`
- Export/archive integration enters through `backend/apps/exports/`
- Reference data such as equipment or labels enters through `backend/apps/references/`

**Data Flow:**
- User action in frontend feature -> typed API call -> DRF endpoint -> domain service -> persistence/audit -> API response -> query invalidation/update in frontend
- Signature and review actions always pass through explicit backend transitions, never through raw model mutation from the UI

### File Organization Patterns

**Configuration Files:**
- Root-level files define shared repo tooling, CI, and environment templates
- Backend runtime configuration lives in `backend/config/settings/`
- Frontend build and lint config lives in `frontend/`
- Container and deployment manifests live under `docker/` and `compose/`

**Source Organization:**
- Backend source is organized by domain app first, then by API/domain/selectors
- Frontend source is organized by application shell, shared modules, then features
- Shared code must remain generic and dependency-light

**Test Organization:**
- Backend app-local tests cover domain, API, and selector behavior close to the owning module
- Cross-app and contract tests live in `backend/tests/`
- Frontend feature tests stay close to features; wider UI integration tests live in `frontend/src/tests/integration/`

**Asset Organization:**
- Static public assets live in `frontend/public/assets/`
- Backend static/template assets stay backend-local and are reserved for Django operational needs only
- Regulated dossier exports are generated by backend export services, not stored as ad hoc frontend assets

### Development Workflow Integration

**Development Server Structure:**
- Local development runs backend and frontend independently with Compose supporting infrastructure as needed
- Quality gates are executed from the repo root via `make`
- Architecture boundaries are enforced through `tools/check_backend_architecture.py` and `frontend/dependency-cruiser.cjs`

**Build Process Structure:**
- Backend build concerns are isolated from frontend bundling concerns
- Frontend build emits static assets only; business rules remain backend-owned
- The structure supports additive migrations and low-risk rollout discipline for 3x8 operations

**Deployment Structure:**
- Compose files define environment-specific deployment topology
- Stateless app containers and one primary PostgreSQL instance support the MVP operating model
- The directory structure keeps deployment, application code, and documentation responsibilities clearly separated

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
The architecture is internally coherent. The selected split-stack foundation, the modular monolith backend, the React SPA frontend, the PostgreSQL-centered data model, and the deployment approach all reinforce each other. There are no contradictory framework, runtime, or structure decisions. The architecture also aligns with the product constraint that the system must remain narrow, portable, and operationally trustworthy in a regulated manufacturing context.

**Pattern Consistency:**
The implementation patterns support the architectural decisions well. Naming conventions, API format rules, service boundaries, and state transition rules are aligned with the Django + DRF + React + TypeScript stack. The explicit architecture enforcement tooling now added to the repository further strengthens consistency across future AI-agent contributions.

**Structure Alignment:**
The project structure supports the chosen architecture. Backend app boundaries, shared technical modules, frontend app/shared/features separation, and deployment/configuration directories all map cleanly to the earlier decisions. The structure also supports the agreed backend ownership of business rules and the frontend ownership of workflow-specific UI.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
No epic files were loaded. The requirement groups and feature areas are mapped into architectural modules and frontend feature areas, but the planning dossier is not yet BMAD-complete for implementation readiness because epics/stories are still missing.

**Functional Requirements Coverage:**
All major FR categories have architectural support:
- template governance through `mmr`
- execution through `batches`
- trust semantics through `signatures`, `audit`, and `exceptions`
- review and release through `reviews` and `releases`
- RBAC and site scope through `authz` and `sites`
- exports, references, and future integrations through dedicated modules

**Non-Functional Requirements Coverage:**
Performance, security, resilience, and operational concerns are addressed architecturally. The most important NFRs are supported by session-based auth, step-up re-authentication for signatures, additive migration strategy, explicit observability, conservative deployment structure, and architecture boundary checks. The 3x8 operating model is reflected in rollout and rollback discipline.

### Implementation Readiness Validation ⚠️

**Decision Completeness:**
The architecture artifact now documents the main implementation-shaping decisions clearly enough for platform and first-slice work to start. Versions are identified where they matter, workflow actions are explicit, and deferred decisions are marked to prevent accidental premature expansion.

**Structure Completeness:**
The project structure is implementation-ready. It is concrete enough to guide file placement, app boundaries, API locations, frontend feature ownership, and test placement without leaving core layout decisions open to interpretation.

**Pattern Completeness:**
The implementation patterns are strong enough to prevent common AI-agent conflicts. Naming, formatting, placement, state transition handling, and error-handling expectations are all documented. The repository now also includes executable enforcement for backend and frontend architectural boundaries.

**Dossier Completeness Limitation:**
Full implementation readiness is still conditional on wider planning cleanup. The epics/stories artifact and implementation-readiness report now exist, but backlog structure and browser-support alignment still need follow-through before implementation handoff is truly clean.

### Gap Analysis Results

**Critical Gaps:**
- None. The planning set now includes the epics/stories artifact and the implementation-readiness report.

**Important Gaps:**
- Async job execution is intentionally deferred in detail and should be finalized once export/notification workloads become concrete.
- Frontend API client generation and schema-sharing mechanics are implied but not yet specified as a dedicated implementation convention.

**Nice-to-Have Gaps:**
- A future ADR or short implementation note for background jobs
- A future note on OpenAPI client generation strategy
- A future note on contract/integration test layering once the first real endpoints exist

### Validation Issues Addressed

The most relevant consistency risk identified during the workflow was uncontrolled placement and import behavior across backend and frontend code. This has now been addressed with explicit implementation patterns plus executable enforcement:
- backend architecture check in `tools/check_backend_architecture.py`
- frontend dependency boundary checks in `frontend/dependency-cruiser.cjs`
- `make architecture-check` and CI integration in the quality workflow

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** ARCHITECTURE ALIGNED; FULL PLANNING DOSSIER NOT YET READY FOR IMPLEMENTATION

**Confidence Level:** Medium-High for the architecture artifact itself; not yet sufficient for full BMAD readiness across the whole planning set

**Key Strengths:**
- Strong alignment between product scope and architecture scope
- Clear backend ownership of regulated business rules
- Explicit support for traceability, signatures, review-state semantics, and 3x8 operations
- Explicit alignment with the UX design-system, shared-workstation, and review-surface decisions
- Concrete project structure and enforceable consistency rules
- Conservative MVP boundaries that reduce operational and architectural risk

**Areas for Future Enhancement:**
- Epics/stories decomposition and readiness sign-off
- Async workload strategy
- API client/codegen convention
- Expanded test architecture once first real business flows are implemented
- More explicit integration patterns when ERP/WMS scope becomes active

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries
- Use the architecture enforcement tooling before merging structural changes
- Refer to this document for all architectural questions

**First Implementation Priority:**
Initialize the split-stack project structure, then scaffold the Django backend and Vite frontend foundation as the first implementation story using the agreed starter commands and quality gates.
