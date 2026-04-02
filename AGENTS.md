# AGENTS

## Purpose

Durable docs are a selective memory system. Keep them small. Put stable product truth in PRD, stable cross-unit technical truth in Product TDD, runtime truth in deployment docs, and volatile work in `tasks/`.

Reason in English. Communicate with humans in Chinese.

If a requested change would reduce readability or maintainability, stop and discuss the trade-off before proceeding.

## Read Order

1. Read this file first.
2. Read the relevant local `AGENTS.md` before touching a subtree.
3. Read shared durable docs when they are relevant to the task:
   - `docs/_shared/00-meta/_svc_v9_2.md` if present
   - `docs/_shared/10-prd/`
   - `docs/_shared/15-alignment/`
   - `docs/_shared/20-product-tdd/`
4. Read local runtime and deployment docs when they are relevant to the task:
   - `docs/40-deployment/`
5. Read `tasks/` for volatile plans, exploration, and backlog items.

## Dynamic Execution Protocol

### Mode A: Exploration

Use this mode when the request is vague, exploratory, or still forming.

- Do not update durable docs or production code.
- Work only in `tasks/`.
- Use Q&A, option analysis, and first-principles reasoning to reduce ambiguity.

### Mode B: Solidification

Use this mode when the request is clear enough to record, but the durable truth is still missing.

- Decide whether the new truth belongs in PRD, Product TDD, Unit TDD, or deployment docs.
- Perform the pre-execution restatement.
- Await human confirmation before updating durable docs.
- Update durable docs before implementation changes.

### Mode C: Execution

Use this mode when the task is specific, local, and already aligned.

- Read the relevant local docs.
- Perform the pre-execution restatement.
- Await human confirmation before logic-altering work when references or invariants matter.
- Prefer tests, types, runtime checks, and CI guardrails over prose.
- After completion, ask whether the related task doc should be archived or deleted.

## Pre-Execution Restatement

Before any reference-sensitive or logic-altering change, restate:

- target path or anchor
- current state or context
- requested operation
- scope, including explicit exclusions
- invariants that must not break
- likely affected files
- uncertainty or assumptions

## Durable Truth Map

- `docs/_shared/00-meta/`: shared collaboration/framework baseline for multi-repo units
- `docs/_shared/10-prd/`: shared product what and why, user-visible semantics, workflow intent
- `docs/_shared/15-alignment/`: shared glossaries or maps that reduce repeated naming drift
- `docs/_shared/20-product-tdd/`: shared cross-unit technical contracts and architectural truths
- local `AGENTS.md` near code: hard local design memory only when code and tests are not enough
- `docs/40-deployment/`: runtime topology, deployment, CI, operational constraints
- `tasks/`: plans, exploration, backlog, temporary reasoning, migration notes

Do not store volatile plans in durable docs. Do not build a second software system out of prose.

## Repository Map

- `run.py`: FastAPI entry point and runtime bootstrap
- `app/`: application core, routes, schemas, and business logic
- `extensions/`: built-in extensions
- `libs/`: shared AI and observability libraries
- `migrations/`: Alembic migrations
- `tests/`: automated checks

Read these local guides when working in their areas:

- [app/AGENTS.md](app/AGENTS.md)
- [app/business/AGENTS.md](app/business/AGENTS.md)
- [app/routes/AGENTS.md](app/routes/AGENTS.md)
- [app/schemas/AGENTS.md](app/schemas/AGENTS.md)
- [extensions/AGENTS.md](extensions/AGENTS.md)
- [libs/AGENTS.md](libs/AGENTS.md)
- [migrations/AGENTS.md](migrations/AGENTS.md)
- [utils/AGENTS.md](utils/AGENTS.md)

## Local Engineering Rules

- Package management: use PDM.
- Run Python commands through `pdm run` when they depend on project packages.
- If the same logic appears in more than two places, extract it.
- Export frequently used package items from `__init__.py`.
- Keep implementation truth in code, tests, types, assertions, lint, and CI whenever possible.
