# Project Docs

This directory contains the canonical project documentation that should remain useful once implementation starts.

## Structure

- `decisions/`
  - architecture and product decisions that guide implementation
- `implementation/`
  - implementation reference artifacts derived from current discovery work
  - includes implementation baselines such as code quality tooling
- `archive/`
  - longer research and brainstorming material kept for traceability, not daily use

## Recommended Reading Order

1. `decisions/architecture-decisions.md`
2. `decisions/transcript-product-decisions.md`
3. `implementation/mmr-version-schema-minimal.json`
4. `implementation/django_models_v1.py`
5. `implementation/code-quality-baseline.md`

## Notes

- `_research/` remains the local, gitignored research lab for cloned repositories, raw analysis and temporary experiments.
- `_bmad-output/` remains a working artifact area produced during discovery. The files promoted into `docs/` are the ones considered canonical at this stage.
