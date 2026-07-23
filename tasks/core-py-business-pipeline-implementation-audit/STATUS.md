# Status

## Purpose

This directory holds the implementation-audit follow-up that was split out of `tasks/core-py-post-split-cleanup/`.

## Current State

Status: `not started; audit notes separated from post-split cleanup scope`

## Why It Was Split Out

`core-py-post-split-cleanup` is about applying SVC v9.3 to `core-py` through:

- shared baseline consumption
- Unit TDD admission
- local `AGENTS.md` strengthening
- routing / setup doc cleanup

Implementation drift work would make that task boundary muddy, so it now lives here.

## Important Caution

Some issues noticed during the audit may be true code bugs, but some may only be symptoms of outdated docs or stale local guides. Re-verify each item before changing code.

## Read Order

1. `tasks/core-py-business-pipeline-implementation-audit/STATUS.md`
2. `tasks/core-py-business-pipeline-implementation-audit/50-implementation-audit-scope-boundary.md`
3. `docs/30-unit-tdd/business-pipeline-and-authority.md`
4. relevant local guides under `app/business/**/AGENTS.md`
5. target implementation files in `app/business/**`

## Scope Reminder

This task is the correct place for any future execution work around:

- embedding upsert correctness
- extension running-state bookkeeping
- resolver/storage legacy drift
- re-verification of whether mismatches are code drift or doc drift
