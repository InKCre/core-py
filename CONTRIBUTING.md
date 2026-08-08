# Contributing

The organization-wide Git and pull-request policy lives in
[InKCre Git and GitHub Governance](https://github.com/InKCre/.github/blob/main/GOVERNANCE.md).
This guide adds the `core-py` setup, validation, migration, and delivery details required by that
policy; it does not weaken the organization baseline.

## Development Setup

```bash
git submodule update --init --recursive
pdm install -G dev --frozen-lockfile
pdm run doctor
pdm run check
```

`.python-version` is the shared Python runtime anchor. CI installs PDM 2.27.0, and
`doctor` reports a mismatch when the local toolchain does not match that contract.

`check` is the same hermetic repository gate used by CI. It verifies the lock and
requirements export, migration configuration and append-only baseline, Ruff formatting,
repository lint, and the complete unit-test suite. Use narrower commands while iterating:

```bash
pdm run format:check
pdm run lint
pdm run test
pdm run check:foundation
```

The test harness sets `INKCRE_ENV_FILE=""` before application imports. Tests do not read a
developer `.env` or use its database and API credentials.

## Database Migrations

Generate a candidate revision only after changing model metadata:

```bash
pdm run db:generate "describe the schema change"
```

Review and commit the generated file before applying it. Generation never upgrades a
database. After review, append its digest to the integrity baseline:

```bash
pdm run db:record
```

Apply checked-in revisions explicitly:

```bash
pdm run db:migrate
```

Deployment release processes may run `db:migrate`; they must never run `db:generate`.
Pull-request CI also rejects modifications, deletions, and renames of revisions that already
exist on the base branch; migration history is append-only.

## Container Contract

The OCI artifact has three provider-neutral commands:

```bash
python scripts/container.py web
python scripts/container.py migrate
python scripts/container.py ready
```

`web` honors `$PORT`; `migrate` only applies checked-in revisions; `ready` performs a
read-only connectivity and Alembic-head check. Checked-in extensions and their root-locked
dependencies are immutable image content. The running service never downloads extension
code.

## Shared Docs And Skill Discovery

`core-py` is a Spoke repo and consumes shared Hub truth from `docs/_shared/`.

The canonical shared-doc editing skill lives in:

- `docs/_shared/00-meta/skills/edit-svc-shared-docs/`

Because Codex auto-loads repo-root `.agents/skills`, this repo also carries a thin discovery wrapper at:

- `.agents/skills/edit-svc-shared-docs/SKILL.md`

Use the repo-root wrapper only to discover the canonical skill. Do not fork the workflow into the wrapper.

## Shared-Doc Update Order

1. Capture the local pressure in the active Spoke task packet.
2. Edit shared docs in `InKCre/docs`.
3. Push the shared Hub commit first.
4. Bump `core-py/docs/_shared` to that pushed commit.
5. Keep Spoke-local runtime and implementation docs outside `docs/_shared`.
6. Do not mix shared-doc edits, ref bumps, and local implementation changes in one commit.
