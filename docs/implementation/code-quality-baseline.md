# Code Quality Baseline

This document defines the initial code quality tooling baseline for DLE-SaaS.

The project architecture is currently fixed around:
- Django + DRF on the backend
- React + TypeScript + Vite on the frontend
- PostgreSQL
- Docker Compose

The quality baseline should reflect that stack and stay small enough to be used every day.

## Principles

- Prefer a small number of strong tools over many overlapping tools.
- Reserve expensive or noisy checks for CI.
- Keep local developer commands explicit via `make`, not automatic git hooks.
- Treat type checking as part of code readability, not only bug prevention.

## Daily Tooling

### Python

- `ruff`
  - primary Python linter
  - import sorting
  - formatter
- `mypy`
  - strict-enough static typing baseline
  - use with `django-stubs`
- `pytest`
  - test runner
- `pytest-django`
  - Django integration for tests
- `pytest-cov`
  - coverage reporting
- `factory-boy`
  - fixtures and factories for readable tests

### Frontend

- `eslint`
  - primary frontend linting tool
- `typescript` with `tsc --noEmit`
  - mandatory typecheck gate
- `vitest`
  - unit and component tests
- `react-doctor`
  - targeted React audit for correctness, architecture, dead code, and performance issues
  - use after React changes and before merge on frontend-heavy work

## CI / Security Tooling

- `bandit`
  - Python security linting
  - useful in CI, but too noisy to be your main quality signal
- `pip-audit`
  - Python dependency vulnerability scan
- `gitleaks`
  - repository secret scanning
- `dependency-cruiser`
  - frontend architectural boundary enforcement
- `tools/check_backend_architecture.py`
  - backend placement and import-boundary enforcement

## Recommended Local Commands

Use the root [Makefile](/home/axel/DLE-SaaS/Makefile) as the command entrypoint.

- `make lint`
  - runs `ruff` and frontend linting
- `make format`
  - applies `ruff --fix` and `ruff format`
- `make typecheck`
  - runs `mypy` and `tsc --noEmit`
- `make test`
  - runs `pytest` and `vitest`
- `make security`
  - runs `bandit`, `pip-audit`, and `gitleaks`
- `make architecture-check`
  - runs backend and frontend architecture boundary checks
- `make doctor`
  - runs `react-doctor`
- `make check`
  - runs the full local quality suite

Bootstrap files already added in this repository:

- [pyproject.toml](/home/axel/DLE-SaaS/pyproject.toml)
- [frontend/package.json](/home/axel/DLE-SaaS/frontend/package.json)
- [frontend/dependency-cruiser.cjs](/home/axel/DLE-SaaS/frontend/dependency-cruiser.cjs)
- [frontend/eslint.config.js](/home/axel/DLE-SaaS/frontend/eslint.config.js)
- [frontend/tsconfig.json](/home/axel/DLE-SaaS/frontend/tsconfig.json)
- [frontend/vitest.config.ts](/home/axel/DLE-SaaS/frontend/vitest.config.ts)
- [tools/check_backend_architecture.py](/home/axel/DLE-SaaS/tools/check_backend_architecture.py)
- [quality.yml](/home/axel/DLE-SaaS/.github/workflows/quality.yml)

## Dependency Baseline

### Backend

Suggested initial Python dev dependencies:

```txt
ruff
mypy
django-stubs
pytest
pytest-django
pytest-cov
factory-boy
bandit
pip-audit
```

### Frontend

Suggested initial frontend dev dependencies:

```txt
dependency-cruiser
eslint
typescript
vitest
@typescript-eslint/eslint-plugin
@typescript-eslint/parser
eslint-plugin-react-hooks
eslint-plugin-react-refresh
```

`react-doctor` can remain an `npx` command and does not need to be pinned on day one unless you want stricter reproducibility in CI.

## Opinionated Defaults

- Prefer `ruff` over a split `black` + `isort` + multiple Python linters.
- Do not add `pre-commit`.
- Do not use `bandit` as a substitute for clean architecture or tests.
- Do not replace `eslint` or `tsc` with `react-doctor`; it is additive, not foundational.
- Use architecture checks to enforce folder boundaries and import rules, not to replace domain review.

## Suggested Next Step

From this baseline, the next practical step is to install and lock the dependencies:

1. `pip install -e .[dev]`
2. `npm install --prefix frontend`
3. commit the generated frontend lockfile once the stack is scaffolded for real

Current bootstrap note:

- `pip-audit` is configured to audit the local project declaration rather than the entire shared virtual environment.
- `react-doctor` requires `react` to be present in `package.json`, even for a minimal bootstrap.
- local `gitleaks` execution expects a system-installed `gitleaks` binary; CI remains the enforcement point via GitHub Actions.
