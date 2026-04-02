# Contributing

## Development Setup

```bash
pdm install -G dev
git submodule update --init --recursive
```

## Shared Docs And Skill Discovery

`core-py` consumes shared durable docs from `docs/_shared/`.

The canonical shared-doc editing skill lives in:

- `docs/_shared/00-meta/skills/edit-shared-docs/`

Because Codex auto-loads repo-root `.agents/skills`, this repo also carries a thin discovery wrapper at:

- `.agents/skills/edit-shared-docs/SKILL.md`

Use the repo-root wrapper only to discover the canonical skill. Do not fork the workflow into the wrapper.

## Shared-Doc Update Order

1. Edit shared docs in `InKCre/docs`.
2. Push the shared source commit first.
3. Bump `core-py/docs/_shared` to that pushed commit.
4. Keep unit-local runtime and implementation docs outside `docs/_shared`.
