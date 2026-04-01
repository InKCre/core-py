# Phase 0: Classification Gate

## Goal

Classify current `core-py/docs` by real ownership and usage before defining transport.

## Required Artifact

One table with columns:

- current path
- declared layer
- actual scope: product / cross-unit / unit-local / mixed
- owner repo
- target location
- action: keep / move / split / rename / delete
- rationale

Current output file:

- `11-phase-0-core-py-docs-classification.md`

## Mandatory Checks

- mixed files must have split notes
- product vs implementation naming collisions must be listed
- files in `docs/40-deployment/` default to local unless proven cross-unit

## Exit Criteria

- every current file has exactly one accepted row
- no unresolved mixed file for pilot scope
