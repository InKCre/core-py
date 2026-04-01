# Phase 2: Mirror Contract

## Purpose

Define exactly what a mirrored file is, where it lives, and how humans and agents distinguish it from local truth.

## Required Documents

### 1. Mirror Policy

Must define:

- source of truth is `.github`
- consumer repos contain committed snapshots
- mirrored files are not edited locally except through explicit override procedure

### 2. Manifest Schema

Must define fields such as:

- consumer repo name
- source path
- destination path
- include/exclude rules
- whether deletion is propagated

### 3. Source Stamp Format

Must define a standard header or footer with:

- source repo
- source path
- source commit
- sync timestamp or sync PR reference if needed
- local edit policy

### 4. Local Directory Policy

Must define:

- which directories are mirrored
- which directories remain local
- how mixed directories avoid collisions

## Recommended Local Shape In Consumer Repos

```text
docs/
  10-prd/            # mirrored shared docs
  15-alignment/      # only mirrored product-scope alignment docs
  20-product-tdd/    # only mirrored true cross-unit contracts
  30-unit-tdd/       # local
  40-deployment/     # local
```

## Non-Negotiable Rules

- no submodule semantics
- no hidden dependency on clone flags
- no overwriting local-only directories
- mirror provenance must be visible in the file itself or adjacent metadata

## Review Questions

- Can a reviewer tell in one glance whether a file is mirrored or local?
- Can the sync process safely delete moved or removed source files?
- Do we need per-repo exclusions for some shared docs?

## Exit Criteria

- one accepted mirror policy
- one accepted manifest schema
- one accepted file stamp format
- one accepted directory collision rule
