# Extension ownership correction

- **Objective**: correct cross-unit ownership errors exposed by GitHub extension review before resuming that unit。
- **Phase**: **Delivery blocked**。Hub PR #18 and core-py PR #82 were owner-separated、verified and squash-merged，but
  production delivery for #82 failed after successful database convergence because the repository-aware manifest-transition
  verifier ran on the dependency-free GitHub runner instead of the exact candidate image。Closure requires the delivery
  boundary fix and a successful exact-main production rerun。
- **Relation to the program**: this is an independent corrective task，not a new knowledge-lifecycle capability or an
  Extension implementation unit。`knowledge-lifecycle-capabilities` remains active but its GitHub unit is paused until this
  correction closes。

## Trigger and evidence

The GitHub extension implementation passed its real-account journey but review exposed repeated promotion errors：

- concrete Extension capabilities were promoted into Hub normative PRD/Product TDD merely because they were important and
  first-party；
- Extension-contributed Source types were represented as core built-ins；
- adjacent persistence primitives were introduced without preserving the existing graph-command topology；
- an installed mature protocol client was replaced by handwritten transport without first proving a capability gap。

PR #79 also deleted the still-active `knowledge-lifecycle-capabilities` task packet by treating the whole `tasks/` subtree as
disposable historical material。That packet is being restored separately as task-control repair；this task owns the resulting
cross-unit product/technical corrections，not the historical packet reconstruction itself。

## Accepted scope

1. **Hub/Spoke durable ownership**
   - Hub normative docs do not claim Memos、RSS、Mail、GitHub or another concrete Extension capability merely because the
     Extension is first-party。
   - Concrete names may remain only as explicitly non-normative implementation examples。
   - Normative protocol、graph、runtime and acceptance contracts live with the owning Extension in its Spoke-local Unit TDD
     or README；verify that local owner exists before removing Hub text。
2. **Core built-in versus Extension publication**
   - Remove all Extension Source types from `BUILTIN_SOURCE_TYPES`，including GitHub、Mail、RSS、Telegram and Twitter。
   - Extension activation/runtime publication is the Source schema owner。
   - If caller evidence shows no true built-in Source remains，delete the empty profile/fallback abstraction instead of
     preserving speculative structure。
3. **Promotion and dependency guidelines**
   - Evaluate delivery owner（core/Extension）、durable owner（Hub/Spoke）、interface layer（domain command/persistence
     primitive）and external capability owner（existing dependency/InKCre）as independent axes。
   - Importance、first-party distribution、current unit pressure and successful acceptance are not promotion evidence。
   - Before implementing external protocol transport，inspect existing dependencies and primary documentation，then record
     the exact unsupported gap；own only the remainder。
4. **Task cleanup lifecycle**
   - `tasks/` is not durable truth，but an active task packet is current collaboration authority。
   - Cleanup is gated by task lifecycle，not directory class、age、line count or completed child units。
   - Content may be split to control a monolith without creating a second control authority。

## Explicitly deferred to GitHub extension

- PyGithub-backed snapshot adapter correction；
- GitHub graph reconciliation and real-account re-acceptance；
- symmetric batch persistence beneath `InfoBaseManager.submit_graph()`；
- GitHub release metadata and PR #80 implementation closure。

These remain recorded in
[`knowledge-lifecycle-capabilities/units/github-extension/packet.md`](../knowledge-lifecycle-capabilities/units/github-extension/packet.md)
and resume only after this task closes。

## Planned sequence

1. Inspect Hub concrete Extension claims and confirm each Extension-local normative owner。
2. Freeze the exact Hub deletions/normalizations and local Unit TDD additions。
3. Trace Source type publication、database init/readiness and cold Extension restore callers。
4. Decide whether the built-in Source profile abstraction is removed entirely or retained for a demonstrated core Source。
5. Prepare an Impact Handshake covering Hub、shared ref、database contract/runtime and documentation guidelines。
6. Wait for Sir's explicit start；then mutate Hub first，push its owner commit，apply core correction，and bump the shared ref
   separately。
7. Verify Hub links/ownership、database reset/readiness、Extension activation catalog publication and repository gates；close
   this task before resuming GitHub extension。

## Guardrails

- Do not broaden this into general Extension hardening or release work。
- Do not modify GitHub-specific protocol/reconciliation behavior in this task。
- Do not add speculative registries、fallbacks or tests merely to preserve deleted structure。
- Keep Hub edits、Spoke-local implementation and shared-ref bump in owner-separated commits。

## Implementation and verification evidence

- Restored the still-active `knowledge-lifecycle-capabilities` packet deleted by PR #79：102 deleted paths plus the original
  program/capability-map structure，with GitHub integrated as a paused unit and stale graph-navigation control corrected。
- Hub removes concrete Memos、RSS/Atom、Mail and GitHub capability、claim、workflow、realization and reference-integration
  contracts。Generic memo-like capture、collection、source/enrichment、graph and Extension contracts remain。
- The canonical shared-doc workflow now checks delivery owner、durable owner、interface layer and external capability owner
  independently before promotion。
- Core removes `SourceTypeProfile`、all Extension schema copies、`BUILTIN_SOURCE_TYPES` and its lookup，catalog seed/readiness
  loops，and the `SourceManager.sync_source_types()` fallback。No true core built-in Source was found，so no empty abstraction remains。
- Local Memos、RSS and Mail Unit TDDs explicitly own their complete Extension-specific product/technical contracts；core
  contribution guidance records promotion、dependency reuse and active-task cleanup boundaries。
- A clean worktree development database reset produced an empty `sources_types` catalog and passed database/Core readiness。
  Publishing GitHub、Mail、RSS、Atom、Telegram and Twitter through the real `SourceManager.sync_source_types()` path then
  produced exactly six rows；description、config、collect and backfill schemas matched each registered Source class exactly。
- Existing deployment rows are not forcibly deleted：they may represent installed Sources and are protected by lifecycle/FK
  concerns。The correction removes false core authority; catalog garbage collection remains outside scope。
- `pdm run check` passes：foundation、lock、migration integrity、format、Ruff、Pyrefly and the admitted test baseline（7
  passed，40 skipped）。Hub `git diff --check` passes and normative PRD/Product TDD contains no Memos、RSS/Atom、Mail or
  GitHub implementation reference after correction。
- Hub's existing SVC adoption remains on corpus/config 10.0.1 while the installed CLI is 14.0.0；`svc status` therefore
  reports its pre-existing project-upgrade work。This correction does not mix an SVC adoption upgrade into the owner diff。
- Hub PR #18 merged as `47f7439`，then core-py PR #82 merged as `8ca3007`。The GitHub extension branch was rebased onto that
  corrected core baseline before PR #80 merged，so the Extension PR no longer duplicated or owned this correction。
- Production runs `32800364301` (#82) and `32801109994` (#80) both completed idempotent `db init` and `db ready` at
  `50b2c08dd267`，then failed with `ModuleNotFoundError: alembic` when the GitHub runner directly invoked
  `scripts/verify_database_manifest_transition.py`。No application release、Peer advertisement or stable-channel movement
  followed。This is a PR #79 delivery-runtime placement regression，not an Extension catalog or migration failure。
