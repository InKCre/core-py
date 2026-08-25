# Production delivery simplification

- **Objective**: reduce canonical production delivery to one observable convergence path：consume the exact `main` artifact，
  resolve the configured Neon branch connection，converge and verify the database，release core + PostgREST，publish the Peer
  advertisement，probe the live deployment，then move `stable` only after success。
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
- **Next Step**: local implementation and repository verification are complete。Await explicit commit/push authorization，
  then open the hotfix PR，observe CI/preview，merge with authorization and require an exact-main production success before
  closing this task or resuming knowledge-lifecycle unit selection。

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
