# Execution 05 — Production Data Recovery Proof

## MVT Core

- Objective & Hypothesis: preserve the current production dataset without mutating its
  runtime branch, create a provider-internal point-in-time checkpoint plus an encrypted
  portable PostgreSQL archive, restore that archive into an isolated Neon branch, and prove
  schema, migration head, row counts, and application readiness. The hypothesis is that
  production CD is unsafe until recovery is executable evidence rather than an assumed
  Neon capability.
- Guardrails Touched: `staging` is the current data-bearing runtime branch and is read-only
  in this execution; no production app or traffic route is created; database credentials,
  dump contents, and row values never enter Git, Actions artifacts, or terminal output.
- Verification: compare a credential-free manifest of schema/head/table counts before and
  after restore, run the checked-in readiness command against the restored branch, and retain
  archive checksum plus recovery instructions next to the encrypted archive.

## Classification And Mode

- Reality:
  - current business data lives on Neon branch `staging`;
  - there is no Neon `production` branch and no Heroku production app;
  - Git `main` and `develop` have diverged by 7 and 131 unique commits respectively;
  - the Neon free-v3 plan cannot protect branches;
  - the source schema claims repository head `a1b2c3d4e5f6` but differs from current
    metadata by 17 Alembic operations.
- Constraint: existing production rows must survive any later migration reset or hard
  cut-off; they are not seed data.
- Artifact: recovery checkpoint branch, encrypted custom-format dump, checksum/manifest,
  isolated restore branch, and verified recovery procedure.
- Active mode: Execute for the snapshot/archive, then Diagnose if restore evidence differs.

## Impact Handshake

- Target:
  - source branch `staging`, read-only;
  - checkpoint branch `backup/pre-cutover-20260723`;
  - rehearsal branch `rehearsal/production-restore-20260723`;
  - local backup directory
    `/Volumes/WorkSSD/Development/InKCre/backups/core-py/2026-07-23/`.
- Current state:
  - `staging` is the parent of sanitized `preview-base`;
  - preview CD has proved current migrations and runtime against isolated data-free branches;
  - production CD is not enabled.
- Requested operation:
  - remove the unrelated expiring agent branch created by the Copilot setup run after proving
    no runtime references it;
  - create/reuse the exact checkpoint from `staging` without expiry;
  - install a PostgreSQL client new enough for the Neon server;
  - stream `pg_dump --format=custom --no-owner` from the checkpoint directly into
    encryption, retaining application grants without creating a plaintext archive;
  - encrypt the archive to the operator's existing SSH public key;
  - capture SHA-256 and a value-free source manifest;
  - create an isolated rehearsal branch and restore with
    `--clean --if-exists --no-owner --exit-on-error`;
  - preserve the provider-owned `public` schema defaults and filter only the two Neon-owned
    `DEFAULT ACL` entries which the database owner cannot replay;
  - verify data and schema equivalence.
- Explicit exclusions:
  - no writes, migrations, schema reset, or traffic changes on `staging`;
  - no use of `develop`, `preview-base`, or production rows as seed data;
  - no production Heroku app, `main` deployment workflow, or cutover;
  - no Git commit containing the archive, credentials, row values, or backup manifest;
  - no deletion of the checkpoint or encrypted archive in this execution.
- Invariants:
  - branch IDs, names, parents, endpoint IDs, and connection targets are resolved and checked
    before destructive restore;
  - only archive-listed objects on the rehearsal branch may be cleaned;
  - the provider-owned `public` schema is not dropped;
  - the encrypted archive is readable only through the selected operator key;
  - manifest comparison includes Alembic head and every application table;
  - `portless.json` remains untouched.
- Likely repository files: this packet and, only if recurrence automation is justified,
  provider-neutral recovery scripts under `scripts/` plus deployment documentation.

## Acceptance Criteria

1. `staging` branch identity, migration head, table counts, and row counts remain unchanged.
   Provider metadata timestamps are not used as a write detector because child-branch
   operations update them.
2. The checkpoint has `staging` as its parent, no TTL, and contains the same migration head
   and table counts.
3. The only retained portable artifact is encrypted; its SHA-256 and decryption command are
   recorded outside Git with mode `0600`.
4. The rehearsal reset guard proves its Neon branch name before any destructive SQL.
5. `pg_restore` exits zero into the rehearsal branch.
6. Source and restored manifests match for migration head, table set, and row counts.
7. `pdm run container:ready` succeeds against the restored branch at repository head.
8. Existing Heroku staging/preview apps and the production dataset remain unchanged.

## Evidence

- Source:
  - Neon project `small-feather-66252738`;
  - branch `staging` / `br-broad-bread-a1j7v4ct`;
  - initial and post-rehearsal manifests are byte-identical;
  - logical size remains `33325056` bytes.
- Checkpoint:
  - `backup/pre-cutover-20260723` / `br-polished-forest-a1m6qwrd`;
  - parent is the exact source branch;
  - parent LSN `0/8126370`, parent timestamp `2026-07-23T09:22:15Z`;
  - no TTL.
- Portable artifact:
  - encrypted custom archive is `472938` bytes;
  - SHA-256 is
    `03b57de3733186f1d547136bf3d0693351495e68e18e2328842f5e82c16a055e`;
  - PostgreSQL client 18.4 and age 1.3.1;
  - no plaintext archive was written;
  - operator instructions and all evidence remain outside Git at the guarded backup path
    with mode `0600`.
- Rehearsal:
  - `rehearsal/production-restore-20260723` / `br-divine-band-a11acyf6`;
  - parent is the exact checkpoint and TTL expires `2026-07-30T10:40:36Z`;
  - repeated pipeline exited with `age=0` and `pg_restore=0`;
  - source and restored manifests share SHA-256
    `b28e6f446047ce1c80aa07976b63de52a031ac8e3786a4df8fc3034a3c83fdfc`;
  - the manifest records head `a1b2c3d4e5f6`, 12 application tables, and 476 rows;
  - checkpoint-to-rehearsal Neon schema diff is empty;
  - `pdm run container:ready` passes;
  - the provider-owned `public` schema and 35 `authenticated` table ACL entries survive.
- Diagnostic:
  - `alembic check` reports the same 17-operation metadata drift on source and rehearsal;
  - the restore reproduced current production faithfully, so this is a pre-existing migration
    lineage defect rather than restore loss.

## Follow-Up Boundary

Execution 06 must append a schema-convergence migration and prove it on a disposable
descendant of the recovered checkpoint before any live branch is migrated. Execution 07
must then reconcile `main` with the tested delivery line before creating production CD.
It may promote a verified branch into canonical `production` only after documenting rollback
to both the encrypted archive and the Neon checkpoint.
