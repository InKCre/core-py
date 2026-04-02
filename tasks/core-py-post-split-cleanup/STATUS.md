# Status

## Purpose

This file is the session handoff for `tasks/core-py-post-split-cleanup/`.

If a later session needs to continue this task, start here before reopening the older phase notes.

## Current State

Status: `core cleanup slice completed; follow-up work is optional and bounded`

Last confirmed repo commit at task completion:

- `core-py`: `cb6ee1e` on `develop`

## What Has Been Completed

### Shared Baseline Alignment

- `core-py` now consumes shared SVC v9.3 from `docs/_shared/00-meta/_svc_v9_3.md`
- shared mode protocols are available under `docs/_shared/00-meta/mode-*.md`

### Local Context Cleanup

These local tactical guides were upgraded:

- `app/business/source/AGENTS.md`
- `app/business/sink/AGENTS.md`
- `app/business/info_base/resolver/AGENTS.md`
- `app/business/info_base/storage/AGENTS.md`

### Unit-TDD Admission

One slow-moving unit-local structure was admitted into `docs/30-unit-tdd/`:

- `docs/30-unit-tdd/business-pipeline-and-authority.md`

Admitted structure:

- `extension -> source/resolver -> info_base -> sink`

### Meta-Engine Decision

Local `docs/00-meta/` was explicitly **not** admitted for `core-py` at this stage.

## What Was Explicitly Rejected

These remain tactical or unstable and should stay out of `docs/30-unit-tdd/` unless the codebase changes materially:

- source scheduling details
- resolver-local import hazards
- storage built-in ID conventions
- sink retrieve-mode implementation details

## Read Order To Resume

1. `tasks/core-py-post-split-cleanup/STATUS.md`
2. `tasks/core-py-post-split-cleanup/00-meta.md`
3. `tasks/core-py-post-split-cleanup/30-phase-3-4-execution-output.md`
4. `tasks/core-py-post-split-cleanup/40-phase-5-meta-gap-decision.md`
5. `docs/30-unit-tdd/business-pipeline-and-authority.md`
6. relevant local guides under `app/business/**/AGENTS.md`

## Resume Conditions

Only reopen this task if one of these happens:

- the business pipeline structure changes across `extension/source/info_base/sink`
- a new slow-moving unit-local structure appears and may deserve `docs/30-unit-tdd/`
- a repeated workflow pain suggests `core-py` really does need local `docs/00-meta/`
- one of the upgraded local guides proves insufficient in practice

## Next Likely Follow-Ups

These are not required to consider this task complete, but are the most plausible next work:

- audit whether `app/business/AGENTS.md` should become thinner now that routing is stronger below it
- revisit source scheduling only when the TODO in `app/business/source/main.py` is actually being resolved
- revisit `docs/30-unit-tdd/` only if another slow-moving structural truth clearly survives locality

## Do Not Re-Do

- do not recreate mixed docs under local `docs/15-alignment/` or `docs/20-product-tdd/`
- do not create local `docs/00-meta/` just because v9.3 allows it
- do not move tactical hazards back out of local `AGENTS.md`
