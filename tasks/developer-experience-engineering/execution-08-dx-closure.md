# Execution 08 — DX Closure And Preview Proof

## MVT Core

- Objective & Hypothesis: close the remaining gap between a working delivery platform and
  a reliable human-agent development contract. The working hypothesis is that one bounded
  cleanup can make formatting executable, remove a dead documentation deployment path,
  eliminate the remaining owned Node 20 action runtime, reconcile stale collaboration
  guidance, and prove or repair automatic per-PR application delivery.
- Guardrails Touched: preserve product behavior and the provider-neutral OCI/release
  contract; keep PDM and checked-in migrations authoritative; keep production data,
  canonical Neon branches, Heroku production configuration, and `docs/_shared/**`
  unchanged; never expose deployment credentials; leave the unrelated untracked
  `portless.json` untouched.
- Verification: diagnose the missing automatic preview run from GitHub event evidence before
  changing its trigger; run the complete PDM repository contract, Ruff format check,
  pre-commit, workflow syntax/static checks, and dependency/lock checks; publish a real
  same-repository pull request and require its repository, Neon, and automatic Heroku
  preview lifecycle to complete before considering the slice closed.

## Classification And Mode

- Constraint:
  - formatting becomes one shared local/CI contract;
  - obsolete Bump.sh delivery is removed rather than replaced by another provider;
  - remaining workflow actions must not depend on deprecated Node 20 runtimes when the
    repository owns a simple replacement.
- Reality:
  - the automatic `Preview application` deploy path has no successful run evidence;
  - durable development guidance and the top-level DX packet disagree with current green
    tests and completed execution work.
- Artifact:
  - this execution packet and its final evidence.
- Active mode: Execute. GitHub run evidence proved that the downstream workflow receives an
  empty PR association and the deploy job therefore skips; trusted PR-target orchestration
  removes that unreliable authority path.

## User-Confirmed Constraints

- Sir explicitly authorized this DX closure execution.
- The Bump.sh subscription has expired, so
  `.github/workflows/openapi-doc.yml` should be deleted.
- An open-source documentation deployment on Cloudflare Pages is optional and lower
  priority; it is not introduced in this slice without a separate product/hosting decision.

## Impact Handshake

- Address and Object:
  - `.github/workflows/preview-deploy.yml` and its upstream workflow relationship;
  - `.github/workflows/branching-database.yml` preview cleanup;
  - `.github/workflows/openapi-doc.yml`;
  - `pyproject.toml`, `.pre-commit-config.yaml`, and mechanically affected Python files;
  - local developer/deployment guidance and the parent DX packet.
- State Diff:
  - automatic preview application delivery: implemented but unproven or non-triggering
    -> evidence-backed and proven by this packet's PR;
  - format expectation: writable command only -> read-only local/pre-commit/CI gate;
  - dead Bump.sh workflow: checked in but unreachable -> removed;
  - Neon cleanup action with an indirect Node 20 runtime -> pinned CLI cleanup with narrow,
    deterministic authority;
  - stale task/document state -> current, non-contradictory control surface.
- Operation:
  - diagnose event topology first;
  - delete obsolete workflow;
  - make format consistency executable and apply the repository formatter once;
  - replace only the provider action whose behavior can be reproduced with a smaller pinned
    command;
  - update volatile and durable guidance at their existing owners.
- Blast Radius Forecast:
  - GitHub Actions trigger behavior and PR-close resource cleanup;
  - formatting-only diffs across the currently non-conforming Python files;
  - local and CI repository checks;
  - developer/agent navigation.
- Invariants Check:
  - no application semantics, migration revision, database contents, production identity,
    provider secret, shared Hub document, or extension profile changes;
  - preview deletion remains limited to `preview/pr-<number>`;
  - fork pull requests never receive infrastructure secrets;
  - production remains gated by exact-main checks.
- Verification:
  - local full repository and format contracts;
  - actionlint/YAML parsing and shell syntax;
  - a live same-repository PR with exact-head repository/artifact/database checks, automatic
    preview deployment, health probes, and close cleanup.
- Uncertainty:
  - the preview symptom may be event-association behavior rather than the job predicate;
    no trigger mutation is justified until run/API evidence ranks the cause.

## Diagnostics Matrix

| Observation | Leading hypotheses | Required evidence |
|---|---|---|
| Upstream pull-request checks pass but no successful automatic preview deploy is visible | Confirmed: the downstream event cannot supply a PR through `workflow_run.pull_requests[0]`, so its predicate rejects the payload | Replace the association with trusted `pull_request_target` metadata and retain exact-head check polling |
| Ruff lint and tests pass while `ruff format --check` reports drift | Format was never made part of the repository contract | Confirm the exact mechanical file set and add one read-only gate |
| Node 20 remains only in dead docs automation and Neon cleanup | Deleting the dead workflow plus a pinned CLI cleanup can remove repository-owned runtime debt | Inspect the action implementation and prove equivalent name/ID guards and not-found handling |
| Top-level packet remains Explore and development docs report old red tests | Execution evidence was recorded in slices but not reflected in the control surface | Reconcile only statements contradicted by executable evidence |

## Explicit Exclusions

- Cloudflare Pages or another API documentation hosting product.
- New type-checking or coverage policy.
- Scheduler/process topology changes.
- Production/manual approval policy changes.
- Neon plan upgrades, branch protection, schema changes, or data cleanup.
- Archival of the legacy staging app, durable checkpoint, or encrypted backup.

## Diagnostic Decision

- GitHub created downstream runs, but the upstream pull-request run objects exposed an empty
  `pull_requests` array. The existing job predicate and PR-number inputs therefore had no
  authority value and skipped.
- `pull_request_target` supplies the base branch's trusted workflow plus exact PR metadata.
  The deploy job remains same-repository only, validates the open PR and its exact head,
  waits for repository/artifact/Neon checks, and checks out untrusted source only afterward.
- The obsolete Bump.sh workflow is deleted without adding a replacement hosting provider.
- Neon cleanup uses pinned `neonctl 2.36.0`, an exact `preview/pr-<number>` namespace guard,
  a provider-resolved branch ID, and an absent-is-success recheck. Authentication or network
  failures remain failures.

## Next Step

Publish the locally verified change through `develop`. After the trusted workflow reaches
the integration branch, use a fresh same-repository PR to prove automatic preview
deployment and close cleanup.

## Execution Evidence

### Implemented locally

- Replaced the unreliable PR `workflow_run` association with same-repository
  `pull_request_target` orchestration. The trusted base workflow now verifies the open PR,
  exact head SHA, and three GitHub Actions check authorities before checking out source,
  then reverifies the same authority immediately before credentialed delivery.
- Replaced `neondatabase/delete-branch-action@v3` with exact `neonctl 2.36.0` cleanup.
  Namespace, branch-count, branch-ID, expected-parent, absent-state, and concurrent-delete
  guards prevent the cleanup job from broadening its authority.
- Deleted the expired Bump.sh/OpenAPI workflow. Manual `docs/openapi.json` generation remains
  available; no replacement hosting provider was introduced.
- Added `format:check`, made it part of the repository contract and pre-commit, formatted the
  16-file mechanical baseline, normalized two legacy CRLF Python files, and made Ruff
  enforce LF for Python output.
- Reconciled the parent DX packet, development/runtime docs, and the broken `libs` guide
  link with executable reality.

### Local verification

- `pdm run check`: passed; 97 tests passed.
- `pdm run pre-commit run --all-files`: all eight hooks passed.
- `pdm run python -m pip check`: no broken requirements.
- Ruff format contract: 122 files passed.
- Actionlint and explicit YAML parsing: passed for every remaining workflow and composite
  action.
- `git diff --check`: passed.
- Known Node 20 action refs and obsolete OpenAPI workflow references: absent from active
  GitHub/deployment surfaces.

### Remaining external proof

- Implementation PR
  [#27](https://github.com/InKCre/core-py/pull/27) passed repository, artifact,
  dependency, and Neon checks and merged into `develop` as `d7d5175`.
- automatic Heroku preview deployment from the trusted workflow after this workflow version
  exists on the PR base branch; the follow-up proof PR owns this evidence;
- deterministic Heroku and Neon cleanup on probe-PR close.
