---
name: edit-svc-shared-docs
description: Thin discovery wrapper for the canonical shared-doc workflow in `docs/_shared/00-meta/skills/edit-svc-shared-docs`. Use when a Spoke repo needs to update shared Hub docs or bump `docs/_shared` safely.
---

# Edit SVC Shared Docs

This is a thin repo-root discovery wrapper.

Codex auto-loads repo-root `.agents/skills`, but it does not auto-load `docs/_shared/00-meta/skills`.

Before doing anything else:

1. if `docs/_shared/` is missing, run `git submodule update --init --recursive`
2. read the canonical skill at [docs/_shared/00-meta/skills/edit-svc-shared-docs/SKILL.md](../../../docs/_shared/00-meta/skills/edit-svc-shared-docs/SKILL.md)
3. follow the canonical workflow there

Do not maintain the real workflow in this wrapper.
