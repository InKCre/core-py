# AGENTS

Reason in English. Communicate with humans in Chinese. Call the user “Sir”. If a requested shortcut would reduce readability or maintainability, stop and discuss the trade-off.

## Repository And Knowledge Owners

`core-py` is an SVC Spoke. Shared Hub truth is mounted read-only at `docs/_shared/`.

- Product behavior and language: `docs/_shared/10-prd/`
- Cross-unit contracts and topology: `docs/_shared/20-product-tdd/`
- Expensive core-py internal design: `docs/30-unit-tdd/`
- Runtime, packaging, migration, observability, and recovery: `docs/40-deployment/`
- Shared security model: `docs/_shared/20-product-tdd/security-boundary-model.md`; vulnerability reporting: `SECURITY.md`;
  core runtime realization: `docs/30-unit-tdd/security-model.md`
- Volatile task control: `tasks/`; never treat it as durable truth, but retain an active packet until its parent task closes
- Mechanically enforceable facts: code, configuration, schemas, tests, assertions, lint, and CI
- Repeated subtree hazards only: the nearest local `AGENTS.md`

Resolve the semantic owner before adding durable material. A Unit is a logical responsibility boundary, not a folder.

## Working Rules

- Run `svc status . --json`; for non-trivial work load `svc lookup --path index.md` and start or recover one Human-facing task packet.
- Follow the organization-wide [Git and GitHub Governance](https://github.com/InKCre/.github/blob/main/GOVERNANCE.md)
  and [contribution workflow](https://github.com/InKCre/.github/blob/main/CONTRIBUTING.md) for branches, pull requests,
  release authority, and delivery boundaries; repository-local documents own exact commands.
- Before a reference-sensitive, logic-altering, or non-obviously-local durable mutation, state the exact object, `From -> To`, side effects, blast radius, invariants, verification, and uncertainty.
- Before promoting behavior, evaluate delivery owner, durable owner, interface layer, and external capability owner independently. Importance, first-party distribution, current pressure, or successful acceptance on one axis does not prove another.
- Before owning external protocol mechanics, inspect existing dependencies and primary documentation and name the unsupported gap. Keep only the application-specific remainder.
- Read the nearest local `AGENTS.md` before changing its subtree. Read shared Product or Product TDD only when that owner is implicated, then the relevant local Unit TDD or Deployment document.
- Before a security-sensitive claim，read the shared security model and relevant local realization；name actor，capability，
  asset，boundary，harm and attack path。Missing defense in depth is hardening unless evidence shows a boundary violation。
- Exclude `tasks/`, generated output, dependencies, environments, caches, and temporary directories from ordinary source and durable-doc search unless they are the evidence target.
- Clean task artifacts by parent-task lifecycle, not directory class, age, size, or completed child units. Splitting content must not create a second control authority.
- Use sub-agents only when bounded isolation or parallel capacity repays assignment, validation, integration, conflict, and residual cost. Primary owns the Human relationship, global integration, and material residual.

Pause for Human input when the requested change conflicts with Product/Technical truth, ownership across durable surfaces remains unclear, evidence cannot support a bug or architecture decision, or the shortcut would damage maintainability.

## Multi-Repo Mutation Rules

- Never edit `docs/_shared/**` from this Spoke context.
- Capture missing shared truth in the active task packet, update and push the Hub source first, then bump the Spoke ref separately.
- Never mix Hub edits, shared-ref bumps, and Spoke-local changes in one commit.
- Use `.agents/skills/edit-svc-shared-docs/` to discover the canonical shared-doc workflow.

## Repository Map And Development

- `run.py`: FastAPI bootstrap
- `app/`: application routes, schemas, and business units
- `extensions/`: built-in extension packages
- `libs/`: shared libraries
- `migrations/`: Alembic revisions and integrity baseline
- `tests/`: admitted migration integrity and mature integration/acceptance checks only

- Package management: PDM. Run package-dependent Python through `pdm run`.
- Primary repository gate: `pdm run check`; use narrower declared checks while iterating.
- Follow the organization-wide [Verification and Test Policy](https://github.com/InKCre/.github/blob/main/TESTING.md).
  Repository-local admitted suites do not authorize new automation by analogy.
- Preserve one authority per durable fact. Name semantics directly; spend complexity only for demonstrated return.
- Extract logic after the third occurrence. Export frequently used package items from `__init__.py`.
- Commit only on explicit Human command and include only current-task changes by default.

<!-- svc:begin -->
## SVC

Use `svc --help` or `svc <command> --help`.

- `svc status`: inspect project state
- `svc lookup`: read SVC guidance
- `svc task init`: create a task packet
- `svc task grow`: inspect packet shape without changing files
- `svc dev`: manage declared development targets

If `AGENTS.local.md` exists, read it after this file. It is ignored local guidance; shared rules belong here.
<!-- svc:end -->
