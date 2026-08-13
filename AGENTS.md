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
- `SECURITY.md`: owns public vulnerability reporting and routes readers to the security model.
- `docs/30-unit-tdd/security-model.md`: owns this repo's actors, assets, trust boundaries,
  security-impact criteria, and proportionality method.

## Working Protocol

- SVC 10.0.1 owns the upstream working protocol and implementation judgment. Run
  `svc status . --json`, then query only the guidance needed with `svc lookup`.
- This repository owns its product projections, local architecture, runtime truth, task
  state, and unmarked instructions; generated SVC surfaces are not project truth.
- Read the active task packet and nearest local `AGENTS.md` before modifying a governed
  subtree.
- Read shared PRD or Product TDD only when the owning layer demands it, then read the
  relevant local Unit TDD or deployment document.
- Before making a security-sensitive claim, read the security model and name the actor,
  capability, asset, boundary, harm, and attack path. Treat missing defense in depth as
  hardening unless evidence shows a boundary violation.
- Prepare an Impact Handshake before reference-sensitive, logic-altering, or
  non-obviously-local durable mutation.

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
- Shared product truth lives in `docs/_shared/10-prd/` and
  `docs/_shared/20-product-tdd/`; Hub/Spoke operations live in
  `docs/_shared/00-meta/`; local structure lives in `docs/30-unit-tdd/`; runtime truth
  lives in `docs/40-deployment/`; tactical hazards live in the nearest local `AGENTS.md`.
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

<!-- svc:begin navigation sha256=01d8643023a40533a997a67c70e920bb0ff0056081d2d18bec59e47324318152 -->
## SVC

This project uses the local Sustainable Vibe Coding CLI. Query framework guidance when it is needed instead of copying framework documents into this repository.

- Use `svc lookup --keyword "<need>"` to find relevant guidance, then `svc lookup --name '<exact-path-regex>'` to read an authoritative document.
- Use `svc status` before broad process changes. If the installed corpus is newer than the adopted version in `svc.json`, read its migration guidance before `svc adopt`.
- Treat all unmarked project instructions and documentation as consumer-owned.
<!-- svc:end navigation -->
