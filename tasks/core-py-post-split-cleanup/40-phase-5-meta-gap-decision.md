# Phase 5 Meta-Gap Decision

## Decision

`core-py` does **not** admit a local `docs/00-meta/` at this stage.

## Reasoning

- the shared baseline under `docs/_shared/00-meta/` now already provides:
  - `_svc_v9_3.md`
  - mode-a / mode-b / mode-c / mode-d protocols
- root `AGENTS.md` in `core-py` already acts as a usable dispatcher/routing layer
- the concrete pain discovered in post-split cleanup was:
  - weak local tactical guides
  - missing unit-local structure memory

It was **not**:

- missing repo-specific execution workflows
- missing repo-specific diagnosis SOPs
- repeated agent failure caused by absence of local meta-engine files

## Revisit Conditions

Only reconsider local `docs/00-meta/` if one of these becomes true:

- `core-py` needs a repo-specific diagnosis workflow not covered by shared Mode D
- `core-py` needs a repo-specific execution SOP that repeatedly cannot live in root/local guides
- shared baseline and local routing prove insufficient for repeated agent operations
