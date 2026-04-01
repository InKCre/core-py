# Phase 1: Source Boundary In `InKCre/docs`

## Goal

Define where exportable product docs live inside `InKCre/docs` and what is excluded.

## Source Layout Candidate

```text
00-meta/
10-prd/
15-alignment/
20-product-tdd/
```

## Boundary Rules

- Exportable:
  - `00-meta/**` (process/framework meta)
  - `10-prd/**`
  - `15-alignment/**`
  - `20-product-tdd/**`
- Not exportable:
  - other repo content outside the allowlist above
  - org profile content
  - site tooling/build config
  - repo governance files unrelated to product memory

## Open Design Point

Submodule cannot mount only a subdirectory. Consumer repos will pull the full shared docs repository even when they only read the exported root allowlist above.

Maintainability risk:

- keeping exported docs at source-repo root is acceptable only with strict allowlist enforcement in SOP/CI; otherwise ownership drift is likely.

## Exit Criteria

- one accepted source subtree path
- one accepted export boundary definition

## Local Execution Snapshot

- Local repo prepared at `/Users/lanzhijiang/Development/InKCre/docs`.
- Boundary implemented under `00-meta`, `10-prd`, `15-alignment`, `20-product-tdd`.
