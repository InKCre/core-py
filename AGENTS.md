# AGENTS

## Purpose

Durable docs are a selective memory system. Keep them small. Put stable product truth in PRD, stable cross-unit technical truth in Product TDD, runtime truth in deployment docs, and volatile work in `tasks/`.

Reason in English. Communicate with humans in Chinese.

If a requested change would reduce readability or maintainability, stop and discuss the trade-off before proceeding.

This repository is a Spoke repo in the SVC optional multi-repo topology. Shared Hub truth is consumed through `docs/_shared/`.

## Minimal Cheat Sheet

- Unit: a logical technical boundary and ownership surface; it is not the same thing as a folder.
- PRD (`docs/_shared/10-prd/`): owns business intent and observable behavior only.
- Product TDD (`docs/_shared/20-product-tdd/`): owns cross-unit technical contracts and topology.
- Unit TDD (`docs/30-unit-tdd/`): owns this repo's internal logic architecture and internal contracts.

## Read Order

1. Read this file first.
2. Read `docs/_shared/00-meta/_svc_v9_6.md`.
3. Read `docs/_shared/00-meta/multi-repo.md` when the task touches shared truth, `docs/_shared/`, or cross-repo ownership.
4. Read the matching route doc in `docs/_shared/00-meta/input-*.md`.
5. Read the active mode SOP in `docs/_shared/00-meta/mode-*.md`.
6. Read `docs/_shared/00-meta/concepts.md` only when boundary language is unclear.
7. Read the relevant local `AGENTS.md` before touching a subtree.
8. Read shared PRD or Product TDD when the owning layer demands it:
   - `docs/_shared/10-prd/`
   - `docs/_shared/15-alignment/` if present
   - `docs/_shared/20-product-tdd/`
9. Read local unit or runtime docs when relevant:
   - `docs/30-unit-tdd/`
   - `docs/40-deployment/`
10. Read `tasks/` for volatile plans, diagnostics, local-pressure capture, and artifact workspace.

## Operating Model

1. Classify the request as Intent, Constraint, Reality, or Artifact.
2. For non-trivial work, open or update a task packet with Objective & Hypothesis, Guardrails Touched, and Verification.
3. Choose the active mode for this slice of work: Explore, Solidify, Execute, or Diagnose.
4. Load only the route doc, mode SOP, topology extension, and governing anchors needed for the current step.
5. Execute and verify.
6. Re-enter another mode if the evidence state changes.
7. Promote only stable truths after verification.

## Typed Input Guide

- Intent: the business wants new behavior, scope, or policy. Update shared PRD first.
- Constraint: product behavior stays the same, but technical or environment boundaries change. Update shared Product TDD or local Unit TDD.
- Reality: runtime truth disagrees with expectation. Diagnose with evidence first, then add recurrence tripwires near code if needed.
- Artifact: produce a bounded deliverable. Keep it tactical unless reuse is proven.

## Mode Guide

- Explore: map unknowns, alternatives, and assumptions.
- Solidify: restate findings into explicit claims, contracts, or decisions.
- Execute: implement a clear, verified change.
- Diagnose: investigate mismatches between expected and observed reality.

Mode guidance:

- do not assume one task equals one mode
- switch modes when evidence or clarity changes
- mode selection never overrides durable ownership

## Multi-Repo Rules

- `core-py` is a Spoke repo. Read shared truth from `docs/_shared/` and treat it as read-only during ordinary local execution.
- If local work discovers missing shared truth, capture the local pressure in the active task packet before editing the Hub source repo.
- Never edit `docs/_shared/**` directly from this repo context.
- Never mix Hub doc edits, shared-ref bumps, and Spoke-local code or local-doc changes in one commit.
- Shared truth lives in `docs/_shared/00-meta/`, `docs/_shared/10-prd/`, and `docs/_shared/20-product-tdd/`; local structure lives in `docs/30-unit-tdd/`; runtime truth lives in `docs/40-deployment/`; tactical hazards live in the nearest local `AGENTS.md`.
- When a shared-doc update is required, use the canonical workflow at `docs/_shared/00-meta/skills/edit-svc-shared-docs/` via the repo-root wrapper when needed.

## Pre-Execution Restatement

Before any reference-sensitive or logic-altering change, restate:

- target path or anchor
- current state or context
- requested operation
- scope, including explicit exclusions
- invariants that must not break
- likely affected files
- uncertainty or assumptions

## Negotiation Triggers

Pause and ask for human input when any of these happen:

- the requested change conflicts with an existing product claim or technical contract
- blast radius crosses multiple durable owners and the correct owner is unclear
- a shortcut would damage readability, maintainability, or an explicit guardrail
- evidence is insufficient for a bug fix or architectural decision

## Repository Map

- `run.py`: FastAPI entry point and runtime bootstrap
- `app/`: application core, routes, schemas, and business logic
- `extensions/`: built-in extensions
- `libs/`: shared AI and observability libraries
- `migrations/`: Alembic migrations
- `tests/`: automated checks

Read these local guides when working in their areas:

- `app/AGENTS.md`
- `app/business/AGENTS.md`
- `app/routes/AGENTS.md`
- `app/schemas/AGENTS.md`
- `extensions/AGENTS.md`
- `libs/AGENTS.md`
- `migrations/AGENTS.md`
- `utils/AGENTS.md`

## Local Engineering Rules

- Package management: use PDM.
- Run Python commands through `pdm run` when they depend on project packages.
- If the same logic appears in more than two places, extract it.
- Export frequently used package items from `__init__.py`.
- Keep implementation truth in code, tests, types, assertions, lint, and CI whenever possible.
