# AGENTS

## Purpose

Durable docs are a selective memory system. Keep them small. Put stable product truth in PRD, stable cross-unit technical truth in Product TDD, runtime truth in deployment docs, and agent-owned volatile work in `tasks/`.

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
2. Read `docs/_shared/00-meta/_svc_v9_8.md`.
3. Read `docs/_shared/00-meta/multi-repo.md` when the task touches shared truth, `docs/_shared/`, or cross-repo ownership.
4. Read the matching route doc in `docs/_shared/00-meta/input-*.md`.
5. Read the active mode SOP in `docs/_shared/00-meta/mode-*.md`.
6. Read `docs/_shared/00-meta/implementation-taste.md` for non-trivial code design or implementation changes that shape structure, boundaries, data, state, authority, durable naming, abstraction, or complexity budget.
7. Read `docs/_shared/00-meta/concepts.md` only when boundary language is unclear.
8. Read the relevant local `AGENTS.md` before touching a subtree.
9. Read shared PRD or Product TDD when the owning layer demands it:
   - `docs/_shared/10-prd/`
   - `docs/_shared/15-alignment/` if present
   - `docs/_shared/20-product-tdd/`
10. Read local unit or runtime docs when relevant:
   - `docs/30-unit-tdd/`
   - `docs/40-deployment/`
11. Read the active `tasks/` packet for volatile plans, diagnostics, evidence, local-pressure capture, and artifact work.

## Operating Model

1. Classify the request as Intent, Constraint, Reality, or Artifact.
2. Identify the owning layer and likely blast radius.
3. For non-trivial work, open or update an agent-owned task packet with Objective & Hypothesis, Guardrails Touched, and Verification.
4. Keep the task packet current when discussion, exploration, implementation friction, or verification changes the working state.
5. Choose the active mode for this slice of work: Explore, Solidify, Execute, or Diagnose.
6. Load only the route doc, mode SOP, topology extension, and governing anchors needed for the current step.
   - For non-trivial code work, load `docs/_shared/00-meta/implementation-taste.md`.
7. Search source and durable docs with volatile workspaces and generated surfaces excluded by default.
8. Expand into Alignment Substrate fields only when MVT is not enough to constrain mutation safely.
9. Execute and verify.
10. Re-enter another mode if the evidence state changes.
11. Promote only stable truths after verification.

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

- creative engineering is non-linear; do not model work as design -> code -> verify
- prepare the verification shape as soon as a design claim is stable enough, and let it constrain Execute
- do not assume one task equals one mode
- switch modes when evidence or clarity changes
- mode selection never overrides durable ownership

## Task Packet Guidance

- Task packets are agent-owned and may be created, updated, split, and reorganized inside the task boundary.
- Keep each packet human-inspectable and steerable, with a compact control surface for objective, guardrails, verification, current understanding, confirmed constraints, active mode, and next step.
- Split by collaboration pressure rather than by a fixed folder scheme.
- Keep packet content non-durable until it passes the promotion test.

## Search Guidance

- Exclude `tasks/`, temporary directories, generated output, dependency folders, virtual environments, and tool caches from ordinary source and durable-doc search.
- Search those surfaces only when the active question targets them, when recovering the active packet, or when reviewing task evidence.

## Multi-Repo Rules

- `core-py` is a Spoke repo. Read shared truth from `docs/_shared/` and treat it as read-only during ordinary local execution.
- If local work discovers missing shared truth, capture the local pressure in the active task packet before editing the Hub source repo.
- Never edit `docs/_shared/**` directly from this repo context.
- Never mix Hub doc edits, shared-ref bumps, and Spoke-local code or local-doc changes in one commit.
- Shared truth lives in `docs/_shared/00-meta/`, `docs/_shared/10-prd/`, and `docs/_shared/20-product-tdd/`; local structure lives in `docs/30-unit-tdd/`; runtime truth lives in `docs/40-deployment/`; tactical hazards live in the nearest local `AGENTS.md`.
- When a shared-doc update is required, use the canonical workflow at `docs/_shared/00-meta/skills/edit-svc-shared-docs/` via the repo-root wrapper when needed.

## Impact Handshake

Before any reference-sensitive, logic-altering, or non-obviously-local durable mutation, restate:

- Address and Object: target path, anchor, symbol, or surface.
- State Diff: objective `From -> To`.
- Operation: mutation class and expected side effects.
- Blast Radius Forecast: likely affected files, modules, and downstream surfaces.
- Invariants Check: scope boundaries, exclusions, and facts that must remain unchanged.
- Verification: objective proof that bounds side effects.
- Uncertainty: evidence gaps or assumptions that could change the operation.

If evidence or ownership remains unclear, return to Explore or Diagnose instead of handshaking a guess.

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
- Preserve one authority for every durable fact, state, relationship, and decision.
- Classify cross-boundary values as authority facts, stable references, commands or proposals, user-authored values, or derived projections.
- Name durable semantics directly and consistently.
- Spend complexity only for clear return; avoid premature optimization, premature abstraction, and over-applied OOP or design patterns.
- If the same logic appears in more than two places, extract it.
- Export frequently used package items from `__init__.py`.
- Keep implementation truth in code, tests, types, assertions, lint, and CI whenever possible.
