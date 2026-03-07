# Project Docs

This directory contains the canonical project documentation that should remain useful once implementation starts.

## Structure

- `decisions/`
  - canonical product and architecture decisions
  - source of truth for what should be built
- `implementation/`
  - canonical implementation references derived from discovery work
  - includes implementation baselines such as code quality tooling
- `archive/`
  - historical material, long-form references, and supporting artifacts
  - not part of the primary implementation path

## Recommended Reading Order

1. `decisions/architecture-decisions.md`
2. `decisions/transcript-product-decisions.md`
3. `implementation/mmr-version-schema-minimal.json`
4. `implementation/django_models_v1.py`
5. `implementation/code-quality-baseline.md`
6. `archive/references/` for secondary PDF references when needed

## Notes

- `_research/` remains the local, gitignored research lab for cloned repositories, raw analysis and temporary experiments.
- `_bmad-output/` remains a working artifact area produced during discovery.
- When a topic exists in both `_bmad-output/` and `docs/`, the `docs/` version is the canonical one.
- Reference PDFs are stored under `archive/references/` so the repository root stays focused on code and canonical docs.
