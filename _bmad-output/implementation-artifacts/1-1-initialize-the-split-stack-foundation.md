# Story 1.1: Initialize the Split-Stack Foundation

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a product engineering team member,
I want a runnable split-stack workspace with shared backend, frontend, database, and environment conventions,
so that parallel development on later epics can start from a stable and consistent foundation.

## Acceptance Criteria

1. Given the repository is prepared for the first implementation slice, when the foundation story is completed, then a Django backend project exists under `backend/` and a Vite React TypeScript frontend exists under `frontend/`, and both applications start successfully in local development.
2. Given the platform foundation is intended to support regulated workflow development, when the backend is scaffolded, then PostgreSQL is configured as the primary application database for local development, and the project structure preserves a clean backend/frontend separation aligned with the architecture artifact.
3. Given multiple future epics should be developed in parallel, when developers start from this foundation, then a canonical Docker Compose development baseline and environment configuration template are available, and they can run the stack without inventing local conventions per epic.
4. Given later stories will build APIs and workflow features independently, when the initial backend and frontend shells are delivered, then the backend exposes a basic health or readiness endpoint and the frontend exposes a basic application shell, and both are ready to accept feature work without restructuring the repository again.
5. Given this project must preserve consistency across future implementation agents, when the foundation is reviewed, then the initial file layout matches the approved architecture boundaries at a minimal level, and no domain-specific tables, endpoints, or feature modules beyond what this story needs are created prematurely.

## Tasks / Subtasks

- [x] Scaffold the backend platform shell under `backend/` with Django 5.2 LTS using `/home/axel/wsl_venv/bin/python` (AC: 1, 2, 5)
  - [x] Replace the current placeholder-only backend state with a real Django project rooted at `backend/manage.py` and `backend/config/`.
  - [x] Split settings into `backend/config/settings/{base,dev,uat,prod}.py` to match the architecture baseline.
  - [x] Create the minimal backend directories required by the architecture guardrails: `backend/apps/`, `backend/shared/`, and `backend/tests/`.
  - [x] Keep `backend/README.md` aligned with the new real scaffold instead of the current placeholder note.

- [x] Add the backend API baseline without introducing business-domain modules (AC: 1, 4, 5)
  - [x] Install and wire `djangorestframework` and `drf-spectacular`.
  - [x] Mount the API namespace under `/api/v1`.
  - [x] Expose one minimal health/readiness endpoint under `/api/v1` that proves the Django app boots and can verify database connectivity.
  - [x] Publish the OpenAPI schema from the Django side using drf-spectacular so later frontend work has a canonical contract source.
  - [x] Do not create `mmr`, `batches`, `signatures`, `reviews`, `exports`, or other domain apps in this story.

- [x] Configure PostgreSQL as the local system of record and preserve environment separation (AC: 1, 2, 3)
  - [x] Use PostgreSQL 17.x for local development to match the architecture decision, even though PostgreSQL 18 is current.
  - [x] Read backend database settings from environment variables rather than hard-coding local credentials.
  - [x] Add or update `.env.example` with backend, frontend, and database variables needed to boot the stack.
  - [x] Keep the migration posture additive-first; do not introduce destructive schema changes or speculative domain tables.

- [x] Scaffold the frontend as a real Vite React TypeScript app and preserve the approved frontend architecture shape (AC: 1, 4, 5)
  - [x] Replace the placeholder `frontend/src/App.tsx` shell with a proper Vite React TypeScript scaffold while preserving the existing repo-level quality scripts.
  - [x] Introduce the canonical `frontend/src/app/`, `frontend/src/shared/`, and `frontend/src/features/` folders.
  - [x] Add a minimal application shell that proves the app boots and gives later stories a stable root layout to extend.
  - [x] Keep the story scope to platform shell only; do not implement operator execution, identity switching, RBAC UI, or dossier workflows yet.

- [x] Install the mandatory frontend baseline dependencies and wiring needed for later parallel stories (AC: 1, 4, 5)
  - [x] Add Tailwind CSS 4 using the Vite plugin approach.
  - [x] Initialize shadcn/ui for the Vite app and keep owned primitives under the shared UI area.
  - [x] Add Radix-backed primitives through shadcn/ui rather than inventing custom modal/menu/focus-management infrastructure.
  - [x] Add React Router 7 and create the initial app router entrypoint.
  - [x] Add TanStack Query v5 with a top-level `QueryClientProvider`.
  - [x] Add React Hook Form 7 and Zod 4 to establish the future regulated form baseline, but do not build real dossier forms in this story.
  - [x] Configure the Vite browser-compatibility baseline consistently with architecture expectations, including `@vitejs/plugin-legacy` if required to keep the supported desktop-browser matrix.

- [x] Add the canonical container and runtime baseline (AC: 1, 3, 4)
  - [x] Create `docker/backend.Dockerfile` and `docker/frontend.Dockerfile`.
  - [x] Create `compose/compose.dev.yml` as the runnable local baseline for backend, frontend, and PostgreSQL.
  - [x] Add placeholder-but-structured `compose/compose.uat.yml` and `compose/compose.prod.yml` so later stories do not invent alternate deployment locations or naming.
  - [x] Standardize on the Compose plugin command form `docker compose`, not legacy `docker-compose`.

- [x] Preserve and extend the current quality baseline rather than replacing it (AC: 1, 3, 5)
  - [x] Keep `Makefile`, `pyproject.toml`, `frontend/package.json`, `frontend/eslint.config.js`, `frontend/vitest.config.ts`, `frontend/dependency-cruiser.cjs`, `tools/check_backend_architecture.py`, and `.github/workflows/quality.yml` working after the scaffold lands.
  - [x] Update backend/frontend tests so the repository verifies the real scaffold instead of placeholder files.
  - [x] Add a backend smoke/integration test for the health/readiness endpoint.
  - [x] Add a frontend smoke test that renders the real application shell.

## Dev Notes

### Story Intent

This story is the platform spine only. It exists to replace the current placeholder repo state with a real, runnable split-stack baseline that later stories can extend without moving files, changing runtimes, or re-deciding framework choices.

Current repo reality before implementation:

- `backend/README.md` explicitly says no real Django project has been scaffolded yet.
- `frontend/README.md` explicitly says no real Vite app has been scaffolded yet.
- `backend/tests/test_smoke.py` is only `assert True`.
- `frontend/src/App.tsx` is a placeholder string render.
- The quality and architecture enforcement baseline already exists and must be preserved.

### Technical Requirements

- Use `/home/axel/wsl_venv/bin/python` for every Python command, including Django bootstrap, package installs, migrations, and tests.
- Keep the application split between `backend/` and `frontend/`. Do not collapse into a single full-stack framework and do not introduce Next.js.
- Keep PostgreSQL as the local development database from story 1.1 onward. SQLite is not an acceptable shortcut for this repo.
- Expose Django APIs only under `/api/v1`.
- Add one minimal health/readiness endpoint now; do not add feature CRUD or workflow endpoints yet.
- Keep environment-driven configuration for dev/uat/prod separation from the start.
- Keep Docker Compose as the canonical local run path and future deployment baseline.
- Preserve existing repo-level quality commands from `make lint`, `make typecheck`, `make test`, `make architecture-check`, `make doctor`, and `make check`.

### Architecture Compliance

- Follow the architecture starter decision exactly: Django backend plus Vite React TypeScript frontend.
- Treat this as a modular-monolith foundation, but only create the minimum structure needed now. Do not pre-build every future domain app unless required for the scaffold to boot cleanly.
- Keep backend business rules out of the frontend, even in placeholder form.
- Keep frontend organization aligned to `src/app`, `src/shared`, and `src/features`.
- Keep future architectural boundaries visible now by creating the approved directory roots and entrypoints.
- Do not implement shared-workstation identification, signature ceremony, site-aware RBAC, batch workflows, dossier rendering, or export logic in this story.
- Do not create speculative tables, serializers, or endpoints for `MMR`, `Batch`, `Signature`, `ReviewEvent`, or `AuditEvent`.

### Library / Framework Requirements

- Backend framework: Django 5.2 LTS is the required implementation target for this story because Epic 1 Story 1 explicitly names it and Django still lists 5.2 as the supported LTS line through April 2028.
- API framework: Django REST framework is approved and officially supports Django 5.2.
- Schema publication: Use drf-spectacular for OpenAPI generation. Its current docs list `0.29.0` in the changelog, so use the latest stable release compatible with the chosen Django/DRF versions at implementation time.
- Database: PostgreSQL 17.x is the architecture target. PostgreSQL 18 is current as of March 12, 2026, but this project intentionally prefers the more mature 17.x line for a regulated MVP. Use the latest 17.x minor available in the chosen image tag.
- Frontend bootstrap: Use the official Vite React TypeScript template, not a custom hand-rolled scaffold.
- Frontend router/state/forms baseline: React Router 7, TanStack Query v5, React Hook Form 7, and Zod 4 are the approved baseline stack for later feature stories.
- Styling/UI baseline: Tailwind CSS 4 via `@tailwindcss/vite`, plus shadcn/ui on top of Radix primitives.
- Browser support baseline: honor the UX desktop-only scope and the architecture note about legacy-browser support expectations; if the default Vite target is too new for the documented matrix, configure `@vitejs/plugin-legacy` now rather than deferring the compatibility decision.

### File Structure Requirements

- Backend required outcomes:
  - `backend/manage.py`
  - `backend/config/`
  - `backend/config/settings/base.py`
  - `backend/config/settings/dev.py`
  - `backend/config/settings/uat.py`
  - `backend/config/settings/prod.py`
  - `backend/config/urls.py`
  - `backend/apps/`
  - `backend/shared/`
  - `backend/tests/`
- Frontend required outcomes:
  - `frontend/index.html`
  - `frontend/src/main.tsx`
  - `frontend/src/app/`
  - `frontend/src/shared/`
  - `frontend/src/features/`
  - `frontend/src/app/router.tsx` or equivalent top-level router entrypoint
  - `frontend/src/app/providers/` for query/router/provider wiring
  - `frontend/src/shared/ui/` for shadcn/ui primitives and wrappers
- Runtime/config required outcomes:
  - `.env.example`
  - `docker/backend.Dockerfile`
  - `docker/frontend.Dockerfile`
  - `compose/compose.dev.yml`
  - `compose/compose.uat.yml`
  - `compose/compose.prod.yml`
- Do not add future feature directories only for appearance if they have no immediate role in the scaffold. Minimal but correct is preferred over empty noise.

### Testing Requirements

- Backend:
  - Add a real test that verifies the health/readiness endpoint returns success in the configured Django test environment.
  - Ensure `pytest` runs against the real Django project, not just placeholder files.
- Frontend:
  - Replace the placeholder smoke coverage with a render test for the real app shell.
  - Keep Vitest configured and passing after the scaffold conversion.
- Whole-repo verification:
  - `make lint`
  - `make typecheck`
  - `make test`
  - `make architecture-check`
  - `make doctor` because React files change in this story
- Runtime verification:
  - `docker compose -f compose/compose.dev.yml up --build` should boot backend, frontend, and PostgreSQL successfully.
  - Verify the backend health endpoint and the frontend shell manually once the stack is up.

### Latest Technical Information

- Django official download/support docs currently show `5.2.12` as the latest patch on the 5.2 LTS series and indicate support through April 2028. Use Django 5.2 LTS, not Django 6.0, because the architecture deliberately froze on the LTS line for the initial regulated foundation.
- Django REST framework documentation currently states support for Django `4.2, 5.0, 5.1, 5.2`, so it is compatible with the chosen backend baseline.
- drf-spectacular documentation currently lists `0.29.0 (2025-11-01)` in its changelog. Pin the latest stable compatible release instead of copying an older example from memory.
- Vite docs are currently on `v8.0.0`, recommend `npm create vite@latest`, and require Node `20.19+` or `22.12+`. The repo CI already uses Node 22, so keep Node 22 as the team baseline for this story.
- Tailwind CSS v4 docs now recommend the Vite plugin install path with `tailwindcss` plus `@tailwindcss/vite`; do not use older PostCSS-only Tailwind bootstrap instructions by default.
- React Router docs are now centered on the v7 documentation set. Use React Router 7 rather than starting with a v6-era setup that will need immediate migration.
- TanStack Query docs are on Query v5; use v5 APIs and provider setup from the start.
- Zod docs state that Zod 4 is stable and tested against TypeScript 5.5+, which fits the current frontend TypeScript baseline.
- PostgreSQL official versioning docs show PostgreSQL `18.3` and `17.9` as supported as of February 26, 2026. Using 17.x here is an architectural choice for maturity, not an assumption that 18 does not exist.
- Docker Compose docs distinguish the Compose plugin from the standalone legacy install. Standardize on the plugin-based `docker compose` command in docs and scripts.

### Project Context Reference

No `project-context.md` file was present in the repository when this story was created.

Use these as the implementation context sources instead:

- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/ux-design-specification.md`
- `docs/decisions/architecture-decisions.md`
- `docs/implementation/code-quality-baseline.md`
- `README.md`
- `backend/README.md`
- `frontend/README.md`
- `Makefile`

### Project Structure Notes

- The architecture artifact defines a fuller future tree than this story should implement immediately. This story should create the stable roots and entrypoints only.
- The repo already enforces backend root shape through `tools/check_backend_architecture.py`; do not fight that script by inventing alternate backend top-level folders.
- The repo already enforces frontend boundary rules through `frontend/dependency-cruiser.cjs`; do not flatten everything into `frontend/src/`.
- Keep the current quality tooling and CI baseline intact while replacing the placeholder backend/frontend internals with real scaffolds.

### References

- `_bmad-output/planning-artifacts/epics.md` - Epic 1, Story 1.1 acceptance criteria and scope
- `_bmad-output/planning-artifacts/architecture.md` - starter selection, stack decisions, project structure, `/api/v1`, PostgreSQL 17.x, health checks, Docker Compose baseline
- `_bmad-output/planning-artifacts/prd.md` - platform scope, shared-workstation environment, RBAC/review roadmap constraints
- `_bmad-output/planning-artifacts/ux-design-specification.md` - desktop-only workstation scope, keyboard-first constraints, Tailwind/shadcn/Radix baseline
- `docs/decisions/architecture-decisions.md` - stack freeze, split-stack rule, Docker Compose portability, shared-workstation and workflow-state decisions
- `docs/implementation/code-quality-baseline.md` - quality commands and toolchain that must survive the scaffold conversion
- `README.md` - repo entrypoint guidance
- `backend/README.md` - current placeholder backend state to replace
- `frontend/README.md` - current placeholder frontend state to replace
- `Makefile` - canonical local commands
- `frontend/package.json` - current frontend React/TypeScript toolchain baseline
- `pyproject.toml` - current Python tooling baseline
- `https://www.djangoproject.com/download/` - Django LTS support status
- `https://www.django-rest-framework.org/` - DRF compatibility/install guidance
- `https://drf-spectacular.readthedocs.io/en/latest/` - drf-spectacular current changelog/docs
- `https://www.postgresql.org/support/versioning/` - PostgreSQL supported major/minor versions
- `https://vite.dev/guide/` - current Vite bootstrap guidance and Node requirement
- `https://tailwindcss.com/docs/installation/using-vite` - Tailwind CSS v4 Vite install path
- `https://ui.shadcn.com/docs/installation/vite` - shadcn/ui Vite setup
- `https://reactrouter.com/home` - React Router v7 docs
- `https://tanstack.com/query/latest/docs/framework/react/overview` - TanStack Query v5 docs
- `https://zod.dev/` - Zod 4 stability and TypeScript guidance
- `https://docs.docker.com/compose/` - Docker Compose plugin docs

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story context assembled from planning artifacts, repo state, and current official stack documentation.
- `_bmad/core/tasks/validate-workflow.xml` was referenced by the workflow instructions but was not present in the repository; checklist intent was applied manually during story construction.
- `/home/axel/wsl_venv/bin/pip install -e '.[dev]'` completed in the required shared virtualenv to align runtime and quality tooling with the real Django scaffold.
- `make check` passed after updating the local `react-doctor` cache path in `Makefile`.
- `docker compose -f compose/compose.dev.yml config` validated successfully.
- `docker compose -f compose/compose.dev.yml up -d` was validated successfully once Docker was available, using alternate host ports to avoid local collisions (`POSTGRES_HOST_PORT=65432`, `BACKEND_PORT=18080`, `FRONTEND_PORT=15174`).
- The initial compose runtime validation exposed two host/container port-coupling bugs in `compose.dev.yml`; both were corrected so PostgreSQL and Django now keep fixed internal container ports while allowing remapped host ports.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story key resolved from `sprint-status.yaml` as `1-1-initialize-the-split-stack-foundation`.
- No previous story existed in Epic 1, so no previous-story or git-intelligence section applied.
- Replaced the placeholder backend with a Django 5.2 project using split settings, PostgreSQL environment configuration, and shared `/api/v1` health and schema endpoints.
- Replaced the placeholder frontend with a real Vite React TypeScript shell using React Router 7, TanStack Query v5, Tailwind CSS 4, a shadcn-style shared UI baseline, and a routed application shell.
- Added Dockerfiles, compose baselines, and a root `.env.example` so later stories inherit one canonical local runtime convention.
- Updated repo quality and test coverage so `make check` passes end to end, including the new backend health test, frontend smoke test, architecture checks, security checks, and `react-doctor`.
- Verified live Compose boot with remapped host ports and confirmed:
  - backend health endpoint responds at `http://127.0.0.1:18080/api/v1/health/`
  - frontend shell responds at `http://127.0.0.1:15174/`
  - PostgreSQL is healthy on host port `65432`

### File List

- `.env.example`
- `Makefile`
- `_bmad-output/implementation-artifacts/1-1-initialize-the-split-stack-foundation.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `backend/README.md`
- `backend/apps/__init__.py`
- `backend/config/__init__.py`
- `backend/config/asgi.py`
- `backend/config/settings/__init__.py`
- `backend/config/settings/base.py`
- `backend/config/settings/dev.py`
- `backend/config/settings/prod.py`
- `backend/config/settings/uat.py`
- `backend/config/urls.py`
- `backend/config/wsgi.py`
- `backend/manage.py`
- `backend/shared/__init__.py`
- `backend/shared/api/__init__.py`
- `backend/shared/api/exceptions.py`
- `backend/shared/api/urls.py`
- `backend/shared/api/views.py`
- `backend/tests/test_health_api.py`
- `backend/tests/test_smoke.py` (deleted)
- `compose/compose.dev.yml`
- `compose/compose.prod.yml`
- `compose/compose.uat.yml`
- `docker/backend.Dockerfile`
- `docker/frontend.Dockerfile`
- `frontend/README.md`
- `frontend/components.json`
- `frontend/eslint.config.js`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.tsx`
- `frontend/src/app/providers/app-providers.tsx`
- `frontend/src/app/providers/query-client.ts`
- `frontend/src/app/routes/app-layout.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/app/styles.css`
- `frontend/src/features/foundation/routes/foundation-home.tsx`
- `frontend/src/main.tsx`
- `frontend/src/shared/lib/cn.ts`
- `frontend/src/shared/ui/button.tsx`
- `frontend/src/smoke.test.ts` (deleted)
- `frontend/src/smoke.test.tsx`
- `frontend/src/test/setup.ts`
- `frontend/src/vite-env.d.ts`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `frontend/vitest.config.ts`
- `pyproject.toml`

### Change Log

- 2026-03-12: Replaced the placeholder split-stack foundation with a real Django + DRF backend, Vite React frontend, Docker Compose runtime baseline, and passing repo quality gates.
