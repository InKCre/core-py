<!-- Create one packet for every non-trivial Consumer Task. `svc task init` creates only this shape. Do not create family children until their topology or information owner is admitted; keep this as a compact Human collaboration surface, not a completed-work log. -->
# core-preview-registry-controller

<!-- State the outcome, not the process. This lets a returning Human judge what the work is for. -->
- **Objective**: Bootstrap the trusted default-branch controller and frozen tooling for per-PR sibling Extension Registry previews without setup product runtime changes.
<!-- Keep authority, boundaries, invariants, and excluded effects here; do not hide a mutation gate in a child. -->
- **Guardrails**: Start from current `origin/main`; keep the source feature worktree untouched; include only controller, preview build tooling, lock, tombstone, and deployment-contract surfaces; add no tests. Preview delivery must not download and compare the complete public tree, add cache-busters, extend propagation retries, or replace the stable PR alias with an immutable URL/digest merely to satisfy automation.
<!-- State the terminal claim and evidence horizon, not a command inventory. -->
- **Verification**: Scoped diff, actionlint, YAML parse, script compile/Ruff, and `git diff --check` pass. Frozen `extension-preview` install, lock consistency, build smoke, and full `pdm run check` remain gated by the unpublished Toolkit asset and regenerated lock.
<!-- Compress supported state, decisions, foreground mismatch, and material uncertainty; include consequential child returns. -->
- **Current Truth**: The controller and Toolkit bootstrap are already on `main`. Repeated delivery failures exposed an over-designed synchronous verification gate: full-tree public reads, byte comparison, long retries, cache-busting, and immutable deployment URL substitution did not improve the review outcome. Provider deployment success is sufficient automation evidence; the deterministic PR alias is passed to Core, while consumer acceptance remains independent.
<!-- Keep one next concrete Agent action or one Human decision/review need. -->
- **Next Step**: Remove the rejected verification gate, validate the workflow structure locally, and land the cleanup before resuming PR preview delivery.
