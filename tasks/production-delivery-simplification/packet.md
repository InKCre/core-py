# Production delivery simplification

- **Objective**: reduce canonical production delivery to one observable convergence path：consume the exact `main` artifact，
  resolve the configured Neon branch connection，converge and verify the database，release core + PostgREST，publish the Peer
  advertisement，probe the live deployment，then move `stable` only after success。Keep GitHub Actions as the trigger and
  orchestration adapter only：versioned repository commands own repeatable check，build，publish and deployment logic。
- **Guardrails**: this is an operational-complexity correction，not a knowledge-lifecycle implementable unit and not a
  security audit。Keep exact-main artifact identity、serialized production execution、configured production database
  coordinate、`db init`、`db ready`、real core/PostgREST smoke evidence and success-gated `stable` movement。Remove obsolete or
  weak proof machinery rather than rebuilding it elsewhere。A failed step remains visible with its actual partial state；do
  not add automatic rollback、replacement gates or new abstractions。Business code receives no self-host/production special
  case。
- **Verification**: repository/static gates pass；the workflow contains the accepted seven-step sequence and no removed
  transition/bootstrap/recovery machinery；an exact-main production run completes，core and PostgREST probes pass，the Peer
  advertisement names the released runtime，and GHCR `stable` moves to that admitted commit。Verification remains
  script/manual workflow evidence，not a new automated test suite。
- **Current Truth**: production runs
  [`32800364301`](https://github.com/InKCre/core-py/actions/runs/32800364301) for PR #82 and
  [`32801109994`](https://github.com/InKCre/core-py/actions/runs/32801109994) for PR #80 both completed idempotent `db init`
  and `db ready` at Alembic head `50b2c08dd267`，then failed before application release because
  `scripts/verify_database_manifest_transition.py` ran on the dependency-free GitHub runner and imported Alembic through the
  repository migration graph。That verifier compares only migration lineage and per-table row counts；it cannot prove value
  preservation，rejects legitimate row-count-changing migrations，duplicates existing migration/readiness evidence and has
  poor ROI。The immediate placement bug exposed a wider PR #79 regression：production delivery still contains one-time
  cutover and proof-oriented gates that are no longer part of the desired product/deployment model。
- **Next Step**: PR #83 review found that the simplified production sequence still leaves delivery logic inside GitHub
  composite-action YAML。Extract that logic and the same defect from every core-py workflow into local repository commands，
  add the organization-wide ownership rule in `InKCre/.github`，then rerun repository and real delivery evidence before
  requesting another review。

## Workflow implementation ownership correction

GitHub Actions owns event selection，permissions，concurrency，environments，job dependencies，platform Actions and invocation
of repository commands。It does not own project checks，artifact construction，release selection，provider reconciliation，
retry/polling loops or deployment convergence。Those behaviors must live in versioned commands that can be invoked from a
developer environment with the same explicit inputs。Short one-line setup or command invocations and GitHub expression wiring
remain YAML; do not replace them with a custom workflow framework or enforcement gate。

Audit scope is every file under `.github/workflows/` and `.github/actions/`，not only production delivery。Preserve useful
job/step boundaries so moving code out of YAML improves the feedback loop without collapsing observability。The organization
rule belongs in `InKCre/.github/GOVERNANCE.md`; core-py owns the exact commands and implementation。

## Accepted target sequence

```text
exact main artifact
  → resolve connection from configured Neon branch ID
  → db init
  → db ready
  → release core + PostgREST
  → converge Peer advertisement
  → smoke probe
  → move stable tag after success
```

The arrows are operational order，not new domain abstractions。The existing workflow/composite action may remain the code
owner if deletion makes it readable；do not split files merely to mirror these steps。

## Accepted removal boundary

- Remove automatic pre/post database manifests and `verify_database_manifest_transition.py` from production delivery。Retain
  `database_manifest.py` only where it has a concrete manual backup/restore observation consumer；do not call it on every
  deployment。
- Remove the recovery-branch input and its name/parent/TTL/state gate from ordinary production delivery。A configured Neon
  branch ID is sufficient to resolve the intended connection；connection resolution and `db ready` expose unavailable or
  incompatible state directly。
- Remove repeated Neon branch name、historical parent、TTL and state assertions that do not contribute another runtime
  coordinate or recovery action。
- Remove the one-time `peer-database-runtime-v1` bootstrap branch、legacy role deletion and special stopped-core path after
  confirming the cutover is already complete。
- Remove declarative Heroku topology policing（region、addon absence、pipeline stage and similar assertions）from each deploy。
  Continue to address the two configured app names and create a missing app only if that behavior remains necessary for the
  canonical deployment journey。
- Remove automatic application rollback。Database migrations are not automatically reversed，so rolling back only the web
  image can create a false recovery model。Keep failure output and the observed deployed state available for an explicit
  corrective rerun。
- Preserve bounded retry only around demonstrated transient external operations such as registry transfer or release-state
  polling；do not turn ordinary command failure into a generic retry framework。

## Impact Handshake baseline

- **Exact objects**: `.github/workflows/production-deploy.yml`，`.github/actions/production-delivery/action.yml`，obsolete
  production-only verifier/helpers and their exact deployment documentation claims。
- **From → To**: layered topology/proof/rollback controller → direct idempotent deployment and live acceptance sequence。
- **Side effects**: production no longer snapshots table counts、requires a recovery branch、enforces historical provider/app
  topology or automatically rolls back releases；failed runs expose the last completed step and are repaired by rerunning a
  corrected exact-main delivery。
- **Blast radius**: canonical production CD only。Preview、self-host、database migrations、runtime behavior and Extension
  publication are unchanged unless preflight proves they import the same deleted helper contract。
- **Invariants**: the exact published image is deployed；only the configured production database is mutated；database
  convergence/readiness precedes application release；both public peers pass their real probe before `stable` advances；logs
  preserve the actual failure and partial state。
- **Uncertainty to eliminate in preflight**: whether any current bootstrap/recovery input still has an external workflow
  consumer，whether app creation can remain without the removed topology assertions，and which deployment-doc statements
  describe retired one-time history versus an active contract。

## Preflight closure

- Bootstrap and recovery inputs have no consumer outside the production workflow/composite action。
- `verify_database_manifest_transition.py` has no runtime caller outside production delivery；`database_manifest.py` remains
  the manual backup/restore observation command。
- The one-time role/schema cutover is complete，so its bootstrap branch and stopped-core exception have no active lifecycle。
- App creation remains useful when a configured canonical Heroku app is absent；continuous region/addon/pipeline policing does
  not。
- Heroku's release process image remains a required container-delivery mechanism，not a separate admission boundary。

## Implementation evidence

- `.github/actions/production-delivery/action.yml` shrank from 691 to 424 lines。Its exact step sequence is now：resolve
  database URLs → resolve apps → `db init`/`db ready` → release core/PostgREST → converge Peer advertisement → live probe。
- The production workflow and composite action expose the same exact 11 inputs；bootstrap revision、Neon parent/recovery
  branch and all removed output references are absent。
- Deleted `scripts/verify_database_manifest_transition.py` and all automatic pre/post manifest calls。The manual
  `db:manifest` recovery observation remains。
- Removed repeated Neon topology assertions、Heroku region/addon/pipeline checks、legacy role-cutover behavior and automatic
  application rollback。Create-if-missing、release terminal polling、bounded registry retry、failure logs and success-gated
  `stable` remain。
- Updated Heroku/Neon deployment truth to distinguish ordinary delivery from operator-led backup/restore evidence。
- YAML parsing、exact step/input assertions、retired-symbol scans and `git diff --check` pass。`pdm run check` passes：lock、
  migration integrity、format、Ruff、Pyrefly and admitted tests（7 passed，40 skipped）。

## Workflow ownership correction evidence

- Audited every core-py workflow and composite action。The same misplaced-control-flow defect existed in runtime artifact
  publication，preview database lifecycle，repository/runtime CI，Extension publication，preview delivery and self-host
  delivery，not only production。
- Added focused commands under `scripts/automation/` for those existing responsibilities。They consume the same explicit
  environment inputs and retain the existing observable job/step boundaries; they are commands，not a new workflow framework
  or YAML-shape gate。
- Production and preview delivery composite actions now contain inputs plus seven command-invocation steps，shrinking from
  424/515 lines to 111/111 lines。The seven workflows shrink from 1,374 lines to 759 while retaining GitHub-owned triggers，
  permissions，concurrency，environments，job dependencies and platform Actions。
- The only remaining multiline `run` block is the pure argument list invoking the existing Render + Neon Python controller。
  Folded one-line installation/publication commands remain legitimate glue; no YAML block retains a branch，loop，retry or
  domain reconciliation。
- `pdm run check:automation` checks command syntax as part of the existing foundation gate。Actionlint，YAML parsing，
  `git diff --check`，`pdm run check` and the complete pre-commit contract pass。No low-value automated behavior test or
  workflow-shape gate was added。
- Organization ownership wording is prepared on `InKCre/.github` branch `feat/thin-github-workflows`：Actions owns
  orchestration and repo commands own repeatable implementation，without sacrificing step-level observability。
