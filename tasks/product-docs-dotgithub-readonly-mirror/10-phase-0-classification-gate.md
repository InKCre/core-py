# Phase 0: Classification Gate

## Purpose

Prevent the migration from moving docs based on folder names instead of actual ownership and scope.

## Why This Phase Comes First

Current `core-py/docs` content is mixed:

- some files look product-scope
- some files look unit-local
- some files mix both

If this phase is skipped, the mirror system will preserve the wrong boundaries.

## Required Documents

### 1. Classification Table

Required fields:

- current path
- current layer
- actual scope: product / cross-unit / unit-local / mixed
- proposed owner repo
- target path
- action: keep / move / split / rename / delete
- rationale

### 2. Split Notes

For each `mixed` file:

- which sections stay local
- which sections move to `.github`
- whether the original file is replaced, split, or renamed

### 3. Terminology Check

Small note listing terms that are:

- product-level canonical names
- unit-local implementation names
- places where the current docs conflate the two

## Suggested Working Method

1. inspect every file under `core-py/docs`
2. classify without trusting the current directory name
3. identify files that must be split before any repo move
4. freeze the accepted table before Phase 1

## Initial Hypotheses To Check

- `docs/10-prd/core-product.md` may actually describe the whole product, not the unit
- `docs/15-alignment/glossary.md` likely mixes product terms with Python-specific terms
- some files under `docs/20-product-tdd/` may really be unit TDD, not product TDD
- `docs/40-deployment/` should remain local unless a file is truly product-runtime-wide

## Review Questions

- Which files are truly consumed across multiple units?
- Which files are only useful when touching `core-py` internals?
- Which names are canonical for the product, and which are only Python-side aliases?

## Exit Criteria

- every current `core-py/docs` file has one accepted classification row
- every mixed file has an explicit split decision
- no unresolved ownership ambiguity remains for the first rollout set
