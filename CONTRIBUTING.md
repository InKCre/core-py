# Contributing

## Development Setup

```bash
git submodule update --init --recursive
pdm install -G dev --frozen-lockfile
pdm run doctor
pdm run check:foundation
```

`.python-version` is the shared Python runtime anchor. CI installs PDM 2.27.0, and
`doctor` reports a mismatch when the local toolchain does not match that contract.

`check:foundation` is the current green containment gate. It verifies lock and
requirements consistency plus the migration configuration, graph, metadata, and release
contract. Full-repository diagnostics remain available separately:

```bash
pdm run lint
pdm run test
```

Those full diagnostics still expose known legacy lint and extension-test debt; they are not
represented as green by the foundation workflow.

The legacy full test collection can import extensions that read `.env`, attempt database
access, and include validation inputs in tracebacks. Until the test-isolation packet lands,
do not run `pdm run test` with a credential-bearing `.env` in shared CI or agent logs. The
foundation command is hermetic and is the safe default.

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
