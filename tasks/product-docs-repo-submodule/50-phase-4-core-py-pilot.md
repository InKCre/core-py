# Phase 4: `core-py` Pilot Rollout

## Goal

Validate the chosen strategy in one consumer repo before scaling.

## Pilot Scope

- repo: `core-py`
- first batch: only files already classified as `shared-now`
- mixed files excluded from first move

## Rollout Steps

1. lock Phase 0 classification table
2. prepare source allowlist paths in `InKCre/docs` (`00-meta`, `10-prd`, `15-alignment`, `20-product-tdd`)
3. add submodule mount in `core-py`
4. update docs links and path references only where required
5. run verification checklist
6. collect failure cases and update SOP/Skill

## Verification Checklist

- clean clone can resolve expected docs paths
- AGENTS and README references still point to correct locations
- local deployment docs remain local and untouched
- CI guards pass

## Rollback Path

- revert submodule introduction commit in `core-py`
- restore previous local doc paths from prior commit
- keep source-side docs unchanged unless they were explicitly moved in the same release window

## Exit Criteria

- one successful pilot PR merged
- no unresolved blocker in daily dev workflow
