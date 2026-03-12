# Implementation Baselines

This directory contains implementation-facing baseline docs for DLE SaaS.

## Files

- `authorization-policy.md`
  - canonical site-aware RBAC baseline and enforcement locations
- `code-quality-baseline.md`
  - local and CI quality tooling baseline
- `custom-user-model-cutover.md`
  - required cutover path for environments initialized before Story 1.2 switched to `authz.User`
- `README.md`
  - pointer to the current BMAD-managed implementation artifacts

## Intended Use

Use this directory for supporting implementation guidance that should remain stable outside BMAD workflow outputs.

The current implementation artifacts live in:

- `_bmad-output/implementation-artifacts/mmr-version-schema-minimal.json`
- `_bmad-output/implementation-artifacts/mmr-version-example.json`
- `_bmad-output/implementation-artifacts/django_models_v1.py`
