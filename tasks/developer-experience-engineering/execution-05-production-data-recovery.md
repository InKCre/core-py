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
  - this host does not yet provide `pg_dump` or `pg_restore`.
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
  - produce `pg_dump --format=custom --no-owner --no-privileges` from the checkpoint;
  - encrypt the archive to the operator's existing SSH public key and remove only the
    plaintext temporary file;
  - capture SHA-256 and a value-free source manifest;
  - create an isolated rehearsal branch, reset only its application schema, restore with
    `--clean --if-exists --exit-on-error`, and verify equivalence.
- Explicit exclusions:
  - no writes, migrations, schema reset, or traffic changes on `staging`;
  - no use of `develop`, `preview-base`, or production rows as seed data;
  - no production Heroku app, `main` deployment workflow, or cutover;
  - no Git commit containing the archive, credentials, row values, or backup manifest;
  - no deletion of the checkpoint or encrypted archive in this execution.
- Invariants:
  - branch names and connection targets are resolved and checked before destructive reset;
  - only the rehearsal branch may be reset;
  - the encrypted archive is readable only through the selected operator key;
  - manifest comparison includes Alembic head and every application table;
  - `portless.json` remains untouched.
- Likely repository files: this packet and, only if recurrence automation is justified,
  provider-neutral recovery scripts under `scripts/` plus deployment documentation.

## Acceptance Criteria

1. `staging` branch identity and updated timestamp do not change because of this execution.
2. The checkpoint has `staging` as its parent, no TTL, and contains the same migration head
   and table counts.
3. The only retained portable artifact is encrypted; its SHA-256 and decryption command are
   recorded outside Git with mode `0600`.
4. The rehearsal reset guard proves its Neon branch name before any destructive SQL.
5. `pg_restore` exits zero into the rehearsal branch.
6. Source and restored manifests match for migration head, table set, and row counts.
7. `pdm run container:ready` succeeds against the restored branch at repository head.
8. Existing Heroku staging/preview apps and the production dataset remain unchanged.

## Follow-Up Boundary

Execution 06 must reconcile `main` with the tested delivery line before creating production
CD. It may promote the recovered checkpoint into a canonical `production` branch only after
documenting rollback to both the encrypted archive and the Neon checkpoint.
