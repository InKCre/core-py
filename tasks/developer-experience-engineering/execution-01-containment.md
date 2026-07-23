# Execution 01 — DX And Migration Containment

## MVT Core

- Objective & Hypothesis: stop release-time migration generation and establish a small,
  reproducible local/CI contract that can prove migration configuration, graph, metadata,
  release, Python, PDM, lock, and exported-requirements invariants without application
  startup or database access. The hypothesis is that these containment gates remove the
  most dangerous delivery behavior while keeping legacy test, lint, image, and schema
  recovery work explicit for later packets.
- Guardrails Touched: PDM remains the package manager; checked-in Alembic revisions are
  review artifacts; release may apply but never generate revisions; migration execution
  depends only on `DATABASE_URL`; production data and control planes are out of scope;
  existing revisions stay byte-for-byte unchanged; existing user changes to
  `pyproject.toml` and `portless.json` remain preserved.
- Verification: run one local foundation command that checks the interpreter/tool versions,
  lock freshness, requirements export, targeted Ruff surface, migration contract tests,
  Alembic graph parsing, and pre-commit configuration. CI runs the same command with pinned
  Python and PDM and rejects non-additive migration-history changes.

## Classification And Mode

- Input types:
  - Constraint: release, migration, and developer-tool boundaries.
  - Reality: deploy-time autogeneration, migration/application settings coupling, and
    non-portable pre-commit behavior.
  - Artifact: foundation checks and their CI workflow.
- Active mode: Execute.

## Impact Handshake

- Address and Object:
  - `Procfile` release command;
  - migration-only settings and metadata modules;
  - Alembic environment and future revision template;
  - Python/PDM developer contract and foundation CI;
  - local deployment and migration documentation.
- State Diff:
  - release `autogenerate + upgrade` -> checked-in `upgrade` only;
  - global application settings -> migration-only `DATABASE_URL`;
  - implicit `LogModel` side effect -> explicit metadata registration assertion;
  - unpinned Heroku Python / CI PDM -> `.python-version` and pinned setup action;
  - mutating Windows-only pre-commit -> cross-platform read-only consistency checks;
  - no application gate -> explicitly scoped foundation gate.
- Expected side effects:
  - local `pdm run check:foundation` becomes the first green machine-readable contract;
  - full-repository `ruff` and `pytest` remain diagnostic and are not represented as green;
  - future migration generation still produces a candidate file for human/agent review.
- Blast radius:
  - local tooling, GitHub Actions, Alembic configuration, and future Heroku releases;
  - no application behavior, external environment, or database state.

## Files In Scope

- `Procfile`
- `alembic.ini`
- `migrations/__init__.py`
- `migrations/settings.py`
- `migrations/metadata.py`
- `migrations/revision-integrity.json`
- `migrations/env.py`
- `migrations/script.py.mako`
- `migrations/AGENTS.md`
- `migrations/README.md`
- `tests/migrations/`
- `tests/test_settings.py`
- `scripts/_tooling.py`
- `scripts/doctor.py`
- `scripts/check_lock.py`
- `scripts/check_requirements.py`
- `scripts/check_migration_history.py`
- `pyproject.toml`
- `.python-version`
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`
- `CONTRIBUTING.md`
- `README.md`
- `docs/40-deployment/development-environment.md`
- `docs/40-deployment/heroku.md`
- `docs/40-deployment/README.md`

## Explicit Exclusions

- No edit to `migrations/versions/**`.
- No new revision, baseline, stamp, reset, upgrade, downgrade, role, grant, extension, or
  production catalog operation.
- No Docker/OCI repair in this slice; the current image remains non-release-capable.
- No full lint baseline or extension test repair.
- No preview workflow, Heroku app, Neon branch, GitHub environment, secret, or deployment
  mutation.
- No commit of implementation changes without another explicit user command.

## Acceptance Criteria

1. `Procfile` release is exactly `alembic upgrade head`.
2. Alembic can load its graph without `DATABASE_URL`; actual migration execution obtains
   only `DATABASE_URL` and does not import `app.settings`.
3. Migration metadata explicitly includes `logs` and every application table.
4. Contract tests prove one Alembic base/head and forbid release-time revision generation.
5. `.python-version` selects Python 3.12 and CI installs PDM 2.27.0.
6. `pdm run check:foundation` is read-only and green.
7. pre-commit is cross-platform, never runs `git add`, and does not rewrite
   `requirements.txt`.
8. Local documentation names the foundation gate honestly and retains the known full-suite
   debt.
9. CI bootstraps a checked-in integrity baseline across legacy branch divergence, then
   rejects modification, deletion, rename, or manifest rewrite of protected revisions on
   pull requests and managed-branch pushes.

## Verification Commands

```bash
pdm run doctor
pdm run check:lock
pdm run check:requirements
pdm run check:migrations
pdm run check:foundation
pdm run check:migration-history <base-ref>
pdm run pre-commit validate-config
pdm run pre-commit run --all-files
pdm run python -B -m alembic heads
```

Diagnostic non-gates:

```bash
pdm run lint
pdm run test
```

## Execution Outcome

- The release command now applies only checked-in revisions.
- CI enforces a bootstrappable, append-only revision integrity baseline on pull requests and
  managed-branch pushes.
- Migration configuration is isolated from application settings and normalizes generic
  PostgreSQL URLs to the installed psycopg driver.
- Migration metadata registration and the current one-base/one-head graph are executable
  contracts.
- Python 3.12 and PDM 2.27.0 are shared local/CI anchors.
- Lock and requirements checks are read-only; pre-commit no longer stages or rewrites files.
- The foundation CI runs the same PDM command as local development.
- Application settings tests are hermetic and no longer depend on a developer's `.env`.

## Verification Evidence

- `pdm run check:foundation`: passed.
  - migration contract: 11 tests passed, including a no-JWT offline upgrade and
    revision-manifest verification;
  - settings contract: 20 tests passed;
  - Alembic head: `a1b2c3d4e5f6`;
  - lock and production requirements export: consistent.
- `pdm run pre-commit validate-config`: passed.
- `pdm run pre-commit run --all-files`: all 6 hooks passed.
- `alembic upgrade head --sql` with a synthetic URL: generated 4,908 bytes of SQL through
  both existing revisions without connecting to a database.
- Python compileall, TOML/YAML parsing, and `git diff --check`: passed.
- `migrations/versions/**`: unchanged.
- Integrity bootstrap, new-revision append, and protected-revision rewrite rejection were
  proven in an isolated temporary Git repository.
- No Heroku, Neon, production database, or other external control-plane write was made.

## Remaining Pressures

- Full Ruff remains red with 73 findings; it is diagnostic rather than a green gate.
- Full pytest collection finds 32 tests but stops on three extension collection failures:
  stale mail schema import, RSS import-time database access, and a Twitter circular import.
  It also remains unsafe around credential-bearing `.env` files until extension imports are
  isolated.
- The current Docker artifact is still non-release-capable: runtime source coverage,
  migration revision inclusion, and platform-port behavior require a separate repair and
  image-build proof.
- No disposable-database round trip, schema drift check, production schema/data inventory,
  or baseline/reset decision belongs to this containment slice.

## Next Step

Open the next bounded execution packet around a green full test collection and portable
OCI artifact. Production preservation and any migration hard cut remain a later,
evidence-driven packet: inventory and dump first, rehearse restore on a disposable branch,
then change production only under an explicit runbook.
