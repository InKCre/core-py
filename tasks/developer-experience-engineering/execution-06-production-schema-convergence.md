# Execution 06 — Production Schema Convergence

## MVT Core

- Objective & Hypothesis: append one audited Alembic revision that converges both the
  rewritten-history production schema and a fresh database built from the protected
  revisions onto one explicit metadata contract, without changing production row values.
  The hypothesis is that the 17-operation drift is caused by a mixture of stronger legacy
  constraints and weaker rewritten revisions, so blindly applying autogenerate would
  discard useful invariants and narrow `logs.id`.
- Guardrails Touched: published revisions remain append-only; production data is never
  seed; `staging`, the durable checkpoint, and the successful restore rehearsal remain
  read-only; type changes may widen but not narrow production data; required-column
  semantics must agree across Python types, SQLAlchemy metadata, and the database.
- Verification: apply the new revision only to a disposable descendant of the durable
  checkpoint, require unchanged value-free table counts, the new exact Alembic head,
  `alembic check` with no operations, application readiness, and a green fresh-database CI
  path before any live branch is eligible for migration.

## Classification And Mode

- Reality:
  - `staging` and the byte-equivalent recovery rehearsal report head `a1b2c3d4e5f6` but
    `alembic check` finds 17 operations;
  - the two protected current revisions build a different schema from production history;
  - deleted historical revision `84d7ce8b3d27` created `logs.id` as `BIGINT`;
  - the source has zero NULL values in every column whose nullability is under review.
- Constraint: converge with an append-only revision; do not rewrite the protected baseline
  or mutate existing production/recovery branches.
- Artifact: corrected metadata, one convergence revision plus integrity digest, tests,
  disposable Neon proof, and migration evidence.
- Active mode: Solidify for this packet, then Execute on a disposable branch; re-enter
  Diagnose on any data, schema, privilege, or lock mismatch.

## Impact Handshake

- Target:
  - SQLAlchemy metadata for the affected models;
  - a new revision after `a1b2c3d4e5f6`;
  - disposable Neon branch `rehearsal/schema-convergence-20260723`, parented to checkpoint
    `br-polished-forest-a1m6qwrd` with a seven-day TTL;
  - migration contract tests and local deployment documentation.
- Current state:
  - source, checkpoint, and restore rehearsal manifests are byte-identical at 12
    application tables and 476 rows;
  - checkpoint-to-restore schema diff is empty;
  - current fresh-database CI is internally consistent with the weaker rewritten revisions;
  - production retains stronger required-column constraints and `BIGINT` log IDs, but uses
    three unbounded `VARCHAR` columns and a restrictive block-storage foreign key.
- Requested operation:
  - make non-Optional model fields explicitly `nullable=False`;
  - model `logs.id` explicitly as `BIGINT`;
  - append a convergence revision which:
    - preserves/establishes required-column `NOT NULL` constraints;
    - widens `logs.id` and its owned sequence to `BIGINT`;
    - widens the three unbounded string columns to `TEXT`;
    - replaces `blocks_storage_fkey` with `ON UPDATE CASCADE ON DELETE SET NULL`;
  - record the new revision in `revision-integrity.json`;
  - apply and verify only on the exact disposable branch.
- Explicit exclusions:
  - no upgrade, stamp, reset, or schema write on `staging`;
  - no mutation or deletion of `backup/pre-cutover-20260723`;
  - no mutation of `rehearsal/production-restore-20260723`;
  - no table deletion, row deletion, value fabrication, seed, or nullable relaxation;
  - no rewrite of `e5a01f9e69ef` or `a1b2c3d4e5f6`;
  - no Heroku production app, production CD, `main` reconciliation, or traffic switch;
  - no touch to `portless.json`.
- Invariants:
  - the disposable branch ID, name, parent ID, endpoint ID, and TTL are guarded before
    migration;
  - table counts are captured before and after with the checked-in value-free manifest;
  - `logs.id` is never converted to a narrower type during upgrade;
  - migration failure on unexpected NULL data is preferable to inventing business values;
  - the canonical schema after upgrade is identical whether the starting point was the
    production legacy shape or the fresh protected-revision shape;
  - downgrade, if implemented, targets the canonical fresh `a1b2c3d4e5f6` schema and must
    refuse unsafe BIGINT-to-INTEGER narrowing.
- Likely files:
  - affected schema models under `app/schemas/` and `libs/obsrv/`;
  - one new file under `migrations/versions/`;
  - `migrations/revision-integrity.json`;
  - focused tests under `tests/migrations/`;
  - `docs/40-deployment/neon.md` and this packet.

## Convergence Decisions

| Drift | Decision | Reason |
|---|---|---|
| 11 required columns are `NOT NULL` in production but nullable in metadata/fresh revisions | Keep or establish `NOT NULL`; correct metadata | Python types are non-Optional, defaults exist for structured values, and production contains zero NULLs |
| `extensions.id`, `extensions.nickname`, and `sources.nickname` are unbounded `VARCHAR` in production but `TEXT` in metadata | Widen to `TEXT` | No length contract exists; conversion is non-lossy |
| `logs.id` is `BIGINT` in production but `INTEGER` in metadata/fresh revisions | Make model, column, and owned sequence `BIGINT` | Logs are append-only/high-growth; narrowing is unsafe and historical intent was BIGINT |
| `blocks.storage` uses `ON DELETE RESTRICT` in production | Converge to `ON UPDATE CASCADE ON DELETE SET NULL` | The field is Optional and block content can survive removal of its backing storage |

## Acceptance Criteria

1. The two protected revisions and their integrity digests remain unchanged.
2. Exactly one new revision extends `a1b2c3d4e5f6` and is recorded in the integrity
   manifest.
3. Metadata expresses all 11 required columns as non-null and `logs.id` as `BIGINT`.
4. A fresh database upgrades from base to the new head and `alembic check` reports no
   operations.
5. The exact disposable production-copy branch upgrades to the new head; no source,
   checkpoint, or prior rehearsal branch changes.
6. Pre/post manifests have identical table sets and row counts; only the expected Alembic
   head changes.
7. Post-upgrade catalogs show the required nullability, `TEXT` columns, `BIGINT` log ID and
   sequence, and the intended foreign-key actions.
8. `pdm run container:ready` and the full checked-in test/pre-commit contract pass.
9. Any downgrade path has an explicit overflow guard before changing `logs.id` to INTEGER;
   otherwise the revision declares downgrade unsupported instead of risking data loss.

## Follow-Up Boundary

Execution 07 owns production delivery: reconcile the tested delivery line into `main`,
select/promote the canonical production Neon branch, create the Heroku production app,
configure GitHub production protections and secrets, prove release/health/rollback, and
only then consider traffic cutover. It must reuse the durable checkpoint and encrypted
archive from Execution 05.

## Execution Evidence

- Revision and metadata:
  - new head `c4e8a7b6d5f0` extends `a1b2c3d4e5f6`;
  - both protected revision digests remain unchanged;
  - the new revision digest is recorded in `revision-integrity.json`;
  - focused metadata tests assert all 11 required columns, `BIGINT` log IDs, and the
    block-storage foreign-key actions.
- Disposable production-copy branch:
  - `rehearsal/schema-convergence-20260723` / `br-round-meadow-a1fa4mia`;
  - parent checkpoint is exactly `br-polished-forest-a1m6qwrd`;
  - endpoint is exactly `ep-rapid-fire-a18bnryp`;
  - TTL expires `2026-07-30T10:59:00Z`.
- Upgrade proof:
  - pre-manifest is byte-identical to the checkpoint/source manifest at old head;
  - upgrade completed transactionally from `a1b2c3d4e5f6` to `c4e8a7b6d5f0`;
  - all 12 table counts and 476 total rows are unchanged;
  - `alembic check` reports no new operations and readiness passes;
  - catalog verification reports all required columns `NOT NULL`, all three widened
    columns `TEXT`, `logs.id` and `logs_id_seq` `BIGINT`, and
    `blocks_storage_fkey` as `ON UPDATE CASCADE ON DELETE SET NULL`;
  - all 35 `authenticated` table ACL entries remain.
- Reversibility proof:
  - downgrade returned to the canonical old head with INTEGER log column and sequence;
  - pre/downgraded table counts are identical;
  - re-upgrade returned to a byte-identical post-manifest;
  - final `alembic check` and readiness pass at `c4e8a7b6d5f0`.
- Repository proof:
  - `pdm run check` passes with 94 tests and the single new migration head;
  - fresh PostgreSQL/OCI verification remains the final external gate after push.
