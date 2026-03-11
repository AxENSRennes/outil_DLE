# Project Docs

This directory contains the canonical project documentation that should remain useful once implementation starts.

## Structure

- `decisions/`
  - canonical product and architecture decisions
  - source of truth for what should be built
- `implementation/`
  - implementation-facing baseline docs and pointers
  - includes quality/tooling guidance without duplicating BMAD-managed artifacts
- `archive/`
  - historical material, long-form references, and supporting artifacts
  - not part of the primary implementation path

## Recommended Reading Order

1. `decisions/architecture-decisions.md`
2. `decisions/transcript-product-decisions.md`
3. `_bmad-output/implementation-artifacts/mmr-version-schema-minimal.json`
4. `_bmad-output/implementation-artifacts/django_models_v1.py`
5. `implementation/code-quality-baseline.md`
6. `archive/references/` for secondary PDF references when needed

## Notes

- `_research/` remains the local, gitignored research lab for cloned repositories, raw analysis and temporary experiments.
- `_bmad-output/` remains a working artifact area produced during discovery.
- The current BMAD-managed implementation artifacts live under `_bmad-output/implementation-artifacts/`.
- `docs/implementation/` keeps supporting baseline docs and pointers rather than duplicate generated artifacts.
- Reference PDFs are stored under `archive/references/` so the repository root stays focused on code and canonical docs.
