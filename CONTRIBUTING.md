# Contributing

## Development Setup

```bash
pdm install -G dev
git submodule update --init --recursive
```

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
