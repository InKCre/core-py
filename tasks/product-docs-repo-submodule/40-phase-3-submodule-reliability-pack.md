# Phase 3: Submodule Reliability Pack

## Goal

Make submodule operationally safe enough for daily collaboration.

## 3.1 Submodule Topology Candidate

Consumer repo mount point:

```text
docs/_shared/   -> submodule: https://github.com/InKCre/docs.git
```

Consumed content:

- `docs/_shared/00-meta/**`
- `docs/_shared/10-prd/**`
- `docs/_shared/15-alignment/**`
- `docs/_shared/20-product-tdd/**`

Local-only content stays outside submodule paths.

## 3.2 SOP Draft (Must Push Before Pointer Update)

For shared-doc edits:

1. edit in source repo `InKCre/docs` on feature branch
2. merge and push source commit first
3. in `core-py`, update submodule pointer to pushed commit
4. run local verification commands
5. commit pointer bump in `core-py`

For consumer-only work:

- do not edit submodule content
- keep pointer unchanged unless explicitly requested

## 3.3 Agent Skill Draft

Skill responsibilities:

- detect whether target path is inside submodule mount
- block direct edits in detached HEAD context
- enforce "source push first, pointer update second"
- emit pre-flight checks before pointer bump
- emit post-update checks before commit

Skill minimum checks:

- submodule initialized
- submodule working tree clean
- target commit reachable on source remote
- `.gitmodules` URL is expected org repo

## 3.4 CI Guard Draft

Required checks on PR:

- `.gitmodules` path and URL integrity
- submodule pointer commit reachable from source remote
- allowlist-only usage under submodule (`00-meta`, `10-prd`, `15-alignment`, `20-product-tdd`)
- no unexpected path overlap between local docs and submodule mount

Optional strict checks:

- fail when submodule is modified but pointer bump commit message lacks source commit reference

## 3.5 Failure And Recovery

Failure classes:

- pointer references non-pushed source commit
- accidental edits inside submodule working tree
- stale local submodule after branch switch

Recovery baseline:

- re-sync submodule from remote
- reset local submodule worktree only after explicit confirmation
- redo pointer bump from valid source commit

## Exit Criteria

- accepted SOP
- accepted Skill spec
- accepted CI guard scope

## Execution Snapshot

- Skill implemented at:
  - `/Users/lanzhijiang/.codex/skills/inkcre-shared-docs-submodule`
- Deterministic check script:
  - `scripts/check-submodule.sh`
- Validation:
  - `quick_validate.py` passed
  - check script passed on temporary repo with `docs/_shared` submodule
