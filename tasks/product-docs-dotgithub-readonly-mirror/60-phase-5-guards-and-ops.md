# Phase 5: Guards And Operations

## Purpose

Keep the mirror system stable after rollout and prevent silent drift between source and consumers.

## Required Documents

### 1. Edit Guard Policy

Must define:

- whether mirrored files reject direct edits in CI
- whether exceptions are ever allowed
- how a maintainer fixes an accidental local edit

### 2. Maintainer Operations Note

Must define:

- normal authoring flow in `.github`
- how sync PRs are reviewed
- how failed sync runs are retried
- how to add a new consumer repo

### 3. Drift Detection Rule

Must define:

- how drift is detected
- whether detection happens in source, consumer, or both
- what signal is shown to maintainers

### 4. Incident Note Template

Small template for recording:

- wrong classification
- overwrite of local docs
- failed sync
- mirror stamp mismatch

## Review Questions

- How strict should the initial CI guard be?
- Do we need soft warnings before hard failures?
- Who owns operational maintenance when the sync bot fails?

## Exit Criteria

- one accepted guard policy
- one accepted maintainer runbook outline
- one accepted drift detection rule
