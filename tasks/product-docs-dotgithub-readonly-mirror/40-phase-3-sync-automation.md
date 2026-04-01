# Phase 3: Sync Automation

## Purpose

Define the mechanical path from source changes in `.github` to reviewable mirror PRs in consumer repos.

## Preferred Operating Model

Source-triggered fan-out PRs:

1. docs change in `.github`
2. workflow detects exportable changes
3. workflow updates one or more consumer repos
4. workflow opens or updates one sync PR per consumer repo

## Required Documents

### 1. Sync Script Spec

Must define:

- inputs
- dry-run behavior
- write behavior
- deletion behavior
- stamping behavior
- deterministic ordering rules

### 2. Workflow Spec

Must define:

- trigger events
- checkout strategy
- consumer repo list source
- PR branch naming
- PR update vs new PR behavior

### 3. Auth And Permissions Note

Must define:

- which token or app writes to consumer repos
- minimum required permissions
- where secrets are stored
- failure mode if one consumer repo cannot be updated

### 4. PR Template

Must define:

- source commit
- exported paths
- affected consumer paths
- manual verification notes

## Bootstrap Recommendation

Start with one consumer repo only:

- `core-py`

Do not expand to more repos until one full change loop succeeds.

## Fallback Model

If source-triggered fan-out is blocked:

- consumer-pulled sync workflow
- manual dispatch or scheduled run
- still creates normal PRs in the consumer repo

This fallback should be treated as temporary because it duplicates automation.

## Review Questions

- Which repo owns the consumer list?
- How do we avoid PR spam when multiple source commits land quickly?
- Should sync collapse into one rolling branch per consumer repo?

## Exit Criteria

- one accepted sync script spec
- one accepted workflow model
- one accepted auth model
- one accepted PR behavior model
