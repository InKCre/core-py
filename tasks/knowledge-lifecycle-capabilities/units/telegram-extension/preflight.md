# Telegram Extension Implementation Preflight

- **Status**: Completed for the expanded Telegram + repository release-contract + organization-guidance address、dependency、
  protocol、branch and verification plan on 2026-08-30。Ready for Human review of the replacement Impact Handshake；no product、
  release or organization source was changed。
- **Placement**: session `01a04685-aa31-7682-a4a2-824727eacce5`，occupied shared core-py checkout
  `feat/knowledge-lifecycle-task-packet-recovery` at `711d3ccca2b2`，occupied `.github` checkout
  `feat/thin-github-workflows` at `723da698018f`，decision range D-421–D-460。Both implementation branches require fresh
  worktrees from their integrated/current main bases。

## Result

No preflight evidence disproved the accepted Product、Technical or Acceptance model。Telegram runtime remains
`extensions/telegram/**` plus generated OpenAPI；the orthogonal release migration owns its declared repository-wide surfaces；
organization guidance owns two files in a separate repository/branch。MCP Sink and Telegram are logically orthogonal，but the
current shared worktree、database target、repository gate and OpenAPI generation cannot be used as an implementation checkout。

The remote development database、real bot credential/bound identity and provider API evidence are ready。Towncrier is not a
machine-level prerequisite：the implementation adds exact `towncrier==25.8.0` to the PDM development group and its lock，then
all checks invoke it through PDM。Existing Source/Mail/RSS transaction seams plus the release-tool source/CLI inspection are
sufficient to freeze the execution address；verification must still exercise the real vertical and generated Release diff。

## Gate evidence

| Gate | Evidence | Resolution |
| --- | --- | --- |
| Parallel placement | The peer roster records this session and D-421–D-460。PR #88/current checkout owns unrelated MCP work；the `.github` checkout owns unrelated `feat/thin-github-workflows` work。 | Pass。Create independent current-main-based worktrees before implementation；never stage/reset either occupied checkout。 |
| Dependency | `pdm.lock` resolves `python-telegram-bot==22.8`；root and Extension manifests already admit it。 | Pass。No dependency or lock change。 |
| Bot mechanics | Runtime introspection confirmed async `Bot` context plus `get_me`、bounded `get_updates`、`get_file`、`File.download_as_bytearray` and `set_message_reaction`。 | Pass。No `Application` lifecycle or custom HTTP client。 |
| Entity projection | PTB `Update.de_json` branch simulation produced `<b>Read</b> this` through `Message.text_html` and selected the largest photo candidate with caption projection。 | Pass。No UTF-16 parser。 |
| Extension registration | With non-connecting dummy settings，current startup registered `extensions.telegram.source.Source` and legacy `extensions.telegram.message.v1` through existing lifecycle hooks。 | Pass。Register the new attachment Resolver in the same hook。 |
| Existing API shape | The only current Telegram route is the unusable PoC webhook `/telegram/bot/{source_id}`。Mail/RSS already register exact remote-materialization commands through Extension-owned routers。 | Pass。Replace webhook with one single-Block materialization command；no Core API change。 |
| Resolver read effects | Lexical/semantic/Organization and generic Block reads can call Resolver projection with `materialize_missing=True`。RSS enclosure ignores that flag for remote bytes；Mail MIME deliberately uses it。 | Pass。Telegram follows RSS and exposes network I/O only through its explicit command/Source policy。 |
| Primary transaction | `SourceModel.state` is JSONB；`SourceManager.ensure_block(source, session)` locks/creates a Source anchor in the caller session；Block/Relation/Storage managers accept caller-owned sessions。 | Pass。One per-update transaction can own graph + cursor without a Core change。 |
| Materialization transaction | Mail and RSS already implement download-outside / lock-recheck / writable-Storage + semantic-child transaction patterns。 | Pass。Reuse the pattern extension-locally；do not extract a common framework。 |
| Distribution compatibility | Telegram `0.1.0` is published with Changie baseline and the legacy Resolver ID。Source config/collection behavior is incompatible while old Blocks remain readable。 | Pass。Plan `0.2.0` hard cut and retained decoder。 |
| Static baseline | Owned-path Ruff and format checks pass；the repository-configured global `pdm run typecheck` reports zero diagnostics。An ad-hoc directory-only Pyrefly invocation sees an ignored stale `extensions/telegram/build/` copy，while the repository configuration correctly excludes it。 | Pass。Do not treat ignored build output as source or delete it without explicit cleanup scope。 |
| Release tooling | The old pinned Changie check passes and establishes the migration baseline。Official Towncrier `25.8.0` package/CLI、monorepo `--config/--dir/--version` behavior、native orphan naming and Git/no-Git staging paths were inspected。 | Pass。Replace Changie with exact PDM-managed Towncrier；no PATH/Homebrew/Go prerequisite remains。 |
| Runtime database | SSH and remote Docker recovered。The MCP owner added `sinks`/`sink_types` to the matching Core database contract and converged the shared runtime at source fingerprint `d5dbee0e…`，migration head `143c4f4adc85`。The owner probe reports `ready=true`、`source_matches=true`、`provider_matches=true` and `converged=true`；Core `/readyz` reports database、migration、roles、privileges and catalog all ok。 | Resolved。Reuse the current shared DB without reset/stop or Telegram-owned Core edits。An independent SVC observation remains：a default probe may omit the provisioned SSH-provider environment and falsely report provider mismatch，while the explicit owner/provider probe succeeds。 |
| Real Telegram account | Ignored root `.env` has mode `0600` and contains non-empty `TELEGRAM_BOT_TOKEN` and `TELEGRAM_BOUND_USER_ID` without exposing either value。A no-offset Bot API probe identified the bound numeric user and left the discovery update unconfirmed。 | Pass。Use the real bot/bound Human for A1/A2；use a second identity only if readily available，otherwise a deterministic double covers rejection。 |

## Address and ownership simulation

| Accepted behavior | Exact implementation address | Shared-owner consequence |
| --- | --- | --- |
| Config/state/metadata contracts | `extensions/telegram/schema.py` and `source.py` | none |
| Legacy + attachment Resolver | `extensions/telegram/resolver.py` | no Core Resolver change |
| Poll/classify/primary transaction | `extensions/telegram/source.py` | uses current Source/InfoBase APIs as consumer |
| Materialization command | `extensions/telegram/resolver.py` + `__init__.py` | generated OpenAPI only |
| Distribution/docs | Telegram `pyproject.toml`、README、project-local fragment and generated OpenAPI | version/changelog remain Release PR output |
| Repository release contract | root `pyproject.toml`/`pdm.lock`、`towncrier.toml`、`scripts/release.py` callers、CI/release/delivery workflows、Core/all Extension fragment/changelog surfaces and local contributor/deployment docs | no Core Source/Resolver/migration change |
| Organization guidance | isolated `InKCre/.github` worktree：`RELEASING.md` + one `GOVERNANCE.md` link | independent repository/PR；no organization workflow |
| Acceptance evidence | task packet + disposable/manual artifacts | no new CI suite without approval |

Exact helper/file decomposition inside the Extension may be simplified during execution if readability benefits，but it may
not create a Core change or alter the observable contracts above without direct affected-peer reconciliation and the Human
gate when the change is material。

## Two-execution and failure branch simulation

| First execution | Persisted fact | Second execution / observable outcome |
| --- | --- | --- |
| primary text/metadata commit succeeds | graph + `last_update_id` | same/losing runner sees accepted cursor；no duplicate graph or reaction |
| primary persistence fails | no graph/cursor | next Job receives the same update and may save it once；no success reaction |
| unauthorized/unsupported update | cursor only | later bound-user update is no longer pinned |
| default metadata-only attachment | metadata + cursor，no `content` | later explicit materialization can create exactly one child；collection already has 👍 |
| automatic materialization fails | metadata + cursor，no `content` | explicit retry may succeed；primary does not replay；👍 plus partial reply |
| reaction fails after commit | graph + cursor | next collect does not replay；Job retains acknowledgement diagnostic |
| two materializers race | one locked/rechecked `content` relation | winner creates child；loser returns existing child |
| Source deleted/rebound before materialization | metadata remains，no exact live Source/bot | explicit operation reports unavailable and does not guess another Source |
| media-group item succeeds | Telegram redirects reaction to first live group item | one visible group check；per-item partial failure still replies explicitly |

## Verification allocation

- Static：schema/registration/version/OpenAPI shape，Ruff、format、Pyrefly and Extension release checks。
- Deterministic runtime：PTB doubles for admission、dispatch、cursor failure/race、materialization failures and notification
  failure；disposable migrated PostgreSQL for transaction/Storage behavior。
- Real vertical：real bot + bound Human + ordinary Source Job + PostgreSQL + writable Storage + hydration/retrieval。
- Manual/scripted first：no new recurring automated regression suite is authorized by this preflight。
- Shared gate：run full `pdm run check` only at a coherent MCP/Telegram integration checkpoint；today's concurrent dirty MCP
  implementation cannot be attributed as a Telegram baseline result。

## Expanded preflight conclusion

The reviewed [implementation plan](implementation-plan.md) is now complete and addressable for Telegram runtime、the
repository-wide Towncrier/Core release contract and the independent organization guidance reference。Product、Technical and
Acceptance decisions are frozen through D-436；the remote database and real Telegram inputs are ready；implementation placement
is known。No remaining preflight fork blocks Human review of the replacement Impact Handshake。Source mutation still requires
Sir's explicit `开始` and fresh worktrees at the recorded integrated bases。

## Release-contract scope-expansion evidence

- Current organization governance makes protected `main` the canonical release authority and prohibits canonical publication
  from pull-request workflows，while explicitly leaving repository-local release details to each repository。
- `InKCre/ui` provides an accepted organization precedent：feature changes carry Changesets，a protected-main workflow creates
  or updates a dedicated version-package Release PR，and publication occurs only after that PR returns prepared versions to
  `main`。
- Current core-py durable truth is intentionally different and must be migrated：`CONTRIBUTING.md` and
  `docs/40-deployment/native-extension-distribution.md` require version/changelog preparation in the source PR，and CI rejects
  changed Extension artifact inputs that retain their prior version。
- Towncrier `25.8.0` supports a shared monorepo config with per-project directories and explicit versions，but its build path
  unconditionally stages the newsfile and normally uses `git rm` for consumed tracked fragments。Release orchestration must
  isolate Towncrier from the Human/shared index and apply only validated target-project results。
- The accepted replacement therefore needs two distinct checks：feature PR fragment intent without version mutation，and a
  dedicated Release PR whose prepared version/changelog/deletions exactly equal the pending fragments on its current main
  base。Existing post-main Extension publication can continue selecting only changed Extension versions after Release PR merge。
- The Core runtime image explicitly excludes `extensions/**`、`docs/**`、`tasks/**` and `tests/**`。Its delivered inputs are
  rooted in `app/**`、`libs/**`、`migrations/**`、`scripts/**`、`utils/**`、the root dependency/application files and the two
  Docker definitions；generated database-contract evidence is derived during CI。This supports an exact Core project scope
  without treating Extension-only or task/documentation changes as Core artifact changes。
- Towncrier has no repository-specific knowledge that can decide which monorepo project a source diff affects；it renders
  fragments after project assignment。The repository controller must therefore classify delivered Core、Extension and mixed
  changes before invoking Towncrier。Root dependency files need a production projection rather than raw-path matching，because
  the accepted PDM-managed Towncrier migration legitimately changes only development groups and their lock records。
- Towncrier's documented monorepo mode shares one config while selecting a project with `--dir` and supplying `--version`
  explicitly。Its native orphan-fragment form `+.<type>.md` allocates a random collision-resistant identifier and supports
  Markdown output，so the repository needs no PR-number prerequisite or parallel naming mechanism。Project-local `.changes/`
  directories preserve independent consumption and make Release PR deletions reviewable。
- Current runtime publication and production deployment run after every successful `main` check，independent of root project
  version。Therefore adding Core only to Towncrier/version preparation would create release notes after the corresponding
  production delivery；it would not make the Core version a release boundary。Making Core a real release-contract project
  requires normal production/stable promotion to select a Core version change produced by the Release PR，while retaining
  explicit manual dispatch as a separate recovery lane。Sir accepted this production boundary；the replacement implementation
  plan must preserve immutable source-SHA/digest identity while using the Core version change only as the normal release
  selector。
- Towncrier `25.8.0` recursively selects a Git backend only when the build directory or an ancestor contains `.git`；its
  no-VCS backend removes copied fragments with ordinary filesystem operations and makes newsfile staging a no-op。A temporary
  directory outside this repository therefore preserves Towncrier's complete build behavior without touching the Human index。
- The existing `InKCre/ui` Release PR controller demonstrates that the repository token is sufficient。The minimum core-py
  controller needs only one post-check workflow、one generated branch、ordinary `git`/`gh` and the repository's normal PR
  review/check gate；it does not need a PAT、GitHub App、third-party PR action or a custom stale-run protocol。
- An unconditional `removed -> major` conflicts with the already accepted Telegram `0.1.0 -> 0.2.0` hard cut and would label
  the first usable MVP as stable `1.0.0`。The accepted maturity-aware rule keeps breaking changes minor while major is zero and
  returns to ordinary major bumps after stability；the repository orchestration，not Towncrier，must implement it。
- `InKCre/.github` currently owns organization Git/GitHub policy and default contribution guidance while delegating exact
  release mechanics to repositories。A small tool-agnostic release-lifecycle reference linked from protected-main guidance is
  semantically valid there。The local `.github` checkout is clean but belongs to unrelated branch
  `feat/thin-github-workflows` at `723da69` rather than current `origin/main` `44517c1`；mutation requires an independent
  worktree/branch and cannot reuse that checkout。
