# Mail Extension Implementation Preflight

- **Status**: Completed and accepted as the R5 execution preflight through D-315；no product code changed。
- **Date**: 2026-08-10。

## Repository And Branch Evidence

- core-py is on `feat/synchronized-client-v3-restacked` at `9dea682`。Its dirty worktree is confined to the active task
  packet；`git diff --check` is clean。
- client-web is on `feat/organization-git-workflow-phase-6` at `bd08c2d` with a clean worktree。
- Required preceding client implementation is not missing：it exists on `feat/synchronized-core-v3` as
  `93090d2`、`c25b0c7` and `3d95b03`。A temporary local clone cherry-picked those three commits in order with zero conflicts。
  The later `41137d5` shared-ref commit is deliberately excluded so current governance/shared truth remains authoritative。
- Current untouched baselines pass：core-py `385 passed, 34 skipped`；client-web full `pnpm type-check` passes workspace、
  runtime、database-contract and every package/application type-check。

## Codebase Consequences Confirmed

- Current `SourceBase` couples collection to `SourceCollectJobModel`、requires obsolete `_organize` and installs
  `collect_at` through process-local APScheduler。`SourceCollectJobManager` has a hard-coded five-minute timeout and only a
  Python execution path。This is a behavior-rewrite boundary，not a safe incremental Mail patch。
- Current Mail fetches full RFC822 messages，stores UID/attachment summary in Email root，swallows failures and retains a
  separate Newsletter Source。It is requirements/failure evidence only。
- PostgreSQL binary Storage and exact core semantic Resolvers already exist in core-py。Their client-web peer implementation
  is exactly the code recovered in Slice 0。
- `storage_types` does not yet project `writable`；`sources` lacks Storage/Block/timestamps；Source types expose setup schema
  only；database contract/profile/readiness and client generated types all name `sources_collect_jobs`。The schema wave must be
  atomic across these owners。
- Existing `InfoBaseManager.submit_graph(GraphForm)` supports signed local Block IDs and arbitrary edges，while
  reconciliation/update paths still need Mail-owned queries and ordinary Managers。The plan does not force update/reconcile
  behavior through an insert-only GraphForm。
- Current extension runtime can hot-add/remove FastAPI routes，but it has no extension-owned Peer-inbound hook and does not
  republish capabilities on dynamic start/close。That is the only common extension-runtime change required by Mail
  materialization。
- client-web has no executable Source/Job registry，uses source-specific Job/UI models and still keeps solved rendering inside
  `BlockDetailsPanel`。The accepted InfoBase UI work is therefore a real refactor rather than a component rename。

## IMAP Library And Protocol Evidence

- IMAPClient 3.1.x is the selected mature client。Its public code supports UID operations、parsed SELECT response including
  UIDVALIDITY/HIGHESTMODSEQ、recursive BODYSTRUCTURE、ENABLE and FETCH modifiers such as CHANGEDSINCE。
- It has no public QRESYNC SELECT API；aioimaplib exposes no comparable QRESYNC/CONDSTORE/BODYSTRUCTURE support。A thin pinned
  adapter-internal QRESYNC extension is lower risk than replacing mature UID/MIME parsing or implementing a protocol parser。
- Dovecot supports CONDSTORE/QRESYNC but not RFC OBJECTID。Therefore J1 can prove the high-value synchronization path；the
  optional provider smoke observes OBJECTID when available，and D-314 correctly avoids a bespoke fake server merely for that
  optional rung。

## Runtime And Tooling Evidence

- The repository physically lives under `/Volumes/WorkSSD/Development` through the user's Development symlink；generated
  corpus、PostgreSQL cluster、Dovecot state and browser acceptance artifacts can remain on WorkSSD。
- No Docker CLI/runtime is currently available。The Acceptance contract requires ephemeral Dovecot，not a container。The
  smallest local harness is Homebrew Dovecot 2.4.4 plus a process-owned loopback config/maildir under the WorkSSD workspace。
  Local PostgreSQL 17 is installed but stopped；PostgREST 16 and Dovecot are available as bottled packages but not installed。
  Their package footprint is small；all material test data remains on WorkSSD。
- The shell has PDM 2.28.0 while repository/CI deliberately pin 2.27.0，so `pdm run doctor` alone reports that mismatch。
  Implementation must use/restore the pinned 2.27.0 toolchain rather than weakening the repository check。Ordinary tests and
  lock verification currently run successfully under the installed environment。
- The retained Alembic strategy is already frozen by D-195：append reviewable revisions，then reset disposable databases from
  the full chain。Do not rewrite the migration baseline or retain `collect_at` compatibility merely because current local rows
  exist。

## Branch And Failure Simulation

| Branch | Expected action | Bounded outcome |
| --- | --- | --- |
| existing MIME child | solve locally before Source/Storage routing | no IMAP、no Peer dispatch、no new bytes |
| browser missing child | exact Mail Peer delegation | provider materializes；browser reloads child from shared DB |
| no eligible Mail provider | delegation unavailable surfaced by explicit action | existing graph unchanged |
| QRESYNC | changed flags + VANISHED + new UIDs under one typed checkpoint | reliable prospective deletion when enabled |
| CONDSTORE only | CHANGEDSINCE flags + new UIDs | no deletion inference |
| base UID only | new occurrence progression | no flag/deletion completeness claim |
| ordinary first run | filter transient INTERNALDATE against `sources.created_at` | pre-setup history skipped without persisting INTERNALDATE |
| backfill | exact `[since,before)` scan | ordinary checkpoint untouched |
| source storage absent | deployment default，then `-4` | ordinary fallback |
| source/deployment storage explicitly invalid | configuration error | no hidden fallback |
| duplicate MIME materialization race | lock/recheck reduces duplicate；any child is usable | no uniqueness/stability API |
| multiple capable Job workers | eligibility before conditional claim | one runner；losers leave row alone |
| multiple Cron checkers | current-minute evaluation + locked Cron transaction | one Job/current occurrence，no overlap/misfire debt |

## Impact Handshake Draft

### Address and Object

- core-py：`app/schemas/source`、new Job/Cron schemas/business/routes、Source/Storage/InfoBase/Extension runtime、
  `extensions/mail`、database contract/migrations and Mail acceptance assets。
- client-web：three recovered prerequisite commits，`packages/core` Source/Job/Cron/Peer/InfoBase contracts，client routes/
  popups/views，new `extensions/mail` remote，generated database types and browser acceptance。
- durable docs：core-py local Unit TDD/deployment/security projection，client-web local architecture，then Hub PRD/Product TDD
  through the canonical shared-doc workflow。

### State Diff

```text
PoC full-message IMAP + Source-specific jobs/schedules + inline Block content panel
  -> typed incremental Mail graph + global Job/Cron + lazy Resolver materialization
     + exact Peer command + route-realized solved-content UI
```

### Operation

- Append schema migration and hard-cut obsolete unreleased runtime surfaces。
- Rewrite Mail behavior around a mature protocol client and canonical graph。
- Restore already completed client peer/content work，then add the accepted generic Job/InfoBase and Mail UI layers。
- Add four black-box acceptance journeys；do not add the deferred negative suite。

### Blast Radius Forecast

- High but bounded to two Spokes plus later Hub documentation。Every existing Source implementation must adopt the new
  ordinary Job signature；Source UI/routes and database artifacts must move together。RSS/Memos/Twitter/GitHub/Telegram
  product behavior and already closed acceptance contracts must remain unchanged。
- Extension lifecycle changes affect capability publication and hot enable/disable，so current extension runtime tests and
  Peer capability snapshots are regression surfaces。
- InfoBase UI changes affect every solved renderer，including Twitter and all core semantic content renderers；their content
  projections remain unchanged while shell/navigation ownership moves。

### Invariants Check

- One authority per fact：Mail root stays small；graph owns participants、bodies、membership、flags、references and MIME
  structure；Source state owns only validator/checkpoint；Storage owns bytes。
- Peer subsystem understands only discovery/delegation，not Mail payload；no generic invoke or delegation Job。
- Resolver owns graph interpretation/materialization；Adapter owns protocol access only；Source owns collection/state。
- `refresh`、`materialize_missing`、Job terminality and Cron occurrence retain their frozen independent meanings。
- No hidden retry、rollback、checkpoint campaign、misfire catch-up、eager attachment download or Mail-specific browse page。
- No shared docs are edited from `docs/_shared` inside a Spoke，and no commit/push occurs without separate explicit authority。

### Verification

- Static/type/migration/contract checks after each coherent schema/runtime wave。
- Existing core and client baselines preserved after Slice 0–2。
- J1–J3 real Dovecot/PostgreSQL black box；J4 built-browser black box；then full repository checks。
- Database reset/dump workflow proves the exact new migration head and contract revision rather than relying on local rows。

### Uncertainty

- IMAPClient's QRESYNC bridge and non-root Dovecot 2.4 configuration are the only library/environment-specific seams。Both
  are isolated behind the Adapter/Acceptance harness and will be proven before Mail collection is considered complete。
- The exact private helper names、batch size、checkpoint JSON field names、CSS/component filenames and diagnostic strings are
  implementation-owned。Evidence that changes domain ownership、observable behavior or the four journeys reopens R5；ordinary
  mechanical variation does not。

## R5 Conclusion

Sir accepted the derived exact MIME materialization capability as the first extension-owned Peer delegation。No remaining
evidence requires another product-design round before implementation。The next state transition is the final Impact Handshake
confirmation followed by an explicit `开始`。
