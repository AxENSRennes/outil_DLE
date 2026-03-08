PYTHON ?= /home/axel/wsl_venv/bin/python
PIP ?= /home/axel/wsl_venv/bin/pip

BACKEND_DIR ?= backend
FRONTEND_DIR ?= frontend

.PHONY: help lint lint-python lint-frontend format format-python typecheck typecheck-python typecheck-frontend test test-backend test-frontend security architecture-check architecture-check-backend architecture-check-frontend doctor check

help:
	@printf '%s\n' \
		'make lint          Run Python and frontend linters' \
		'make format        Format Python code with ruff' \
		'make typecheck     Run mypy and TypeScript checks' \
		'make test          Run backend and frontend tests' \
		'make security      Run dependency and security scans' \
		'make architecture-check  Run backend and frontend architecture boundary checks' \
		'make doctor        Run react-doctor on the frontend app' \
		'make check         Run the full local quality suite'

lint: lint-python lint-frontend

lint-python:
	$(PYTHON) -m ruff check $(BACKEND_DIR)

lint-frontend:
	npm --prefix $(FRONTEND_DIR) run lint

format: format-python

format-python:
	$(PYTHON) -m ruff check $(BACKEND_DIR) --fix
	$(PYTHON) -m ruff format $(BACKEND_DIR)

typecheck: typecheck-python typecheck-frontend

typecheck-python:
	$(PYTHON) -m mypy $(BACKEND_DIR)

typecheck-frontend:
	npm --prefix $(FRONTEND_DIR) run typecheck

test: test-backend test-frontend

test-backend:
	$(PYTHON) -m pytest $(BACKEND_DIR)

test-frontend:
	npm --prefix $(FRONTEND_DIR) run test

security:
	$(PYTHON) -m bandit -r $(BACKEND_DIR) -x $(BACKEND_DIR)/tests
	XDG_CACHE_HOME=$(CURDIR)/.cache $(PYTHON) -m pip_audit . --skip-editable
	@if command -v gitleaks >/dev/null 2>&1; then \
		gitleaks detect --source . --no-git --redact; \
	else \
		printf '%s\n' 'Skipping local gitleaks: install the gitleaks binary or rely on CI.'; \
	fi

architecture-check: architecture-check-backend architecture-check-frontend

architecture-check-backend:
	$(PYTHON) tools/check_backend_architecture.py

architecture-check-frontend:
	npm --prefix $(FRONTEND_DIR) run architecture-check

doctor:
	npm --prefix $(FRONTEND_DIR) run doctor

check: lint typecheck test security architecture-check doctor
