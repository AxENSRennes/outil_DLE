# DLE-SaaS

DLE-SaaS is a B2B SaaS project for electronic batch record workflows in cosmetics manufacturing.

The repository is intentionally split between canonical project docs, implementation bootstrap, and discovery artifacts.

## Start Here

- `docs/`
  - canonical product, architecture, and implementation references
- `backend/`
  - future Django + DRF application area
  - currently contains only bootstrap quality scaffolding
- `frontend/`
  - future React + TypeScript + Vite application area
  - currently contains tooling bootstrap and placeholder app files

## Secondary Areas

- `_bmad-output/`
  - generated planning and discovery artifacts kept for traceability
  - use `docs/` first when both locations contain the same topic
- `_bmad/` and `.agents/`
  - BMAD agent framework and local skill definitions
- `_research/`
  - local research workspace, gitignored on purpose

## Developer Commands

- `make lint`
- `make typecheck`
- `make test`
- `make security`
- `make doctor`
- `make check`

## Reference Material

Reference PDFs and long-form supporting material live under `docs/archive/references/` to keep the repository root focused on code and canonical docs.
