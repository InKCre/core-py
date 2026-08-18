<!-- Create one packet for every non-trivial Consumer Task. `svc task init` creates only this shape. Do not create family children until their topology or information owner is admitted; keep this as a compact Human collaboration surface, not a completed-work log. -->
# core-preview-registry-controller

<!-- State the outcome, not the process. This lets a returning Human judge what the work is for. -->
- **Objective**: Bootstrap the trusted default-branch controller and frozen tooling for per-PR sibling Extension Registry previews without setup product runtime changes.
<!-- Keep authority, boundaries, invariants, and excluded effects here; do not hide a mutation gate in a child. -->
- **Guardrails**: Start from current `origin/main`; keep the source feature worktree untouched; include only controller, preview build tooling, lock, tombstone, and deployment-contract surfaces; add no tests; do not commit or push.
<!-- State the terminal claim and evidence horizon, not a command inventory. -->
- **Verification**: Scoped diff, actionlint, YAML parse, script compile/Ruff, and `git diff --check` pass. Frozen `extension-preview` install, lock consistency, build smoke, and full `pdm run check` remain gated by the unpublished Toolkit asset and regenerated lock.
<!-- Compress supported state, decisions, foreground mismatch, and material uncertainty; include consequential child returns. -->
- **Current Truth**: The controller carries its own build script and dependency group because it executes from trusted default-branch source. Toolkit distribution is a GitHub Release wheel URL, not PyPI. The proposed `toolkit-v0.1.0` URL currently returns HTTP 404; `pdm install --no-default --group extension-preview --frozen-lockfile` fails at that URL, so `pdm.lock` is intentionally unchanged rather than fabricated. The host PDM is 2.28.0 while the repository requires 2.27.0.
<!-- Keep one next concrete Agent action or one Human decision/review need. -->
- **Next Step**: Publish the Toolkit wheel, generate `pdm.lock` from the live asset, then run the complete verification horizon.
