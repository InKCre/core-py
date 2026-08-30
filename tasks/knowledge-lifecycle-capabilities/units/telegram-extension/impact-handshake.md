# Telegram Extension and Release Contract Impact Handshake

> Replacement Human-review handshake for the accepted design through D-436。This does not authorize source mutation；
> execution begins only after Sir explicitly says `开始`。

## Addresses and ownership

### core-py feature branch

- Telegram runtime and Distribution：`extensions/telegram/**` plus its project-local fragment。
- Generated API evidence：`docs/openapi.json`，regenerated only from the integrated application route set。
- Release project/tooling：root `pyproject.toml`、`pdm.lock`、new `towncrier.toml`、root/Extension `.changes/` and
  changelogs、`scripts/release.py` plus its existing discovery/publication callers。
- Automation and durable local truth：repository check、Release PR、artifact/publication/production workflows，
  `CONTRIBUTING.md` and the relevant Deployment release document。
- Explicit exclusions：Core Source/Resolver/Extension framework、database schema/migrations、client-web、Cron/setup UI and
  shared `docs/_shared/**` truth。

### InKCre/.github guidance branch

- Add one tool-agnostic `RELEASING.md` and one link from `GOVERNANCE.md` protected-main release guidance。
- Add no organization workflow、tool requirement or core-py implementation detail。

Both repositories require new current-main-based worktrees。The current core-py MCP checkout and `.github`
`feat/thin-github-workflows` checkout remain untouched。No commit、push、PR creation or publication is authorized by this
handshake。

## State diff

```text
Telegram PoC wrapper/webhook/cursor-before-graph
  -> bound private bot inbox
     -> semantic text/HTML + metadata-first attachments
     -> per-update graph/cursor commit
     -> optional bytes + post-commit 👍

feature PR version/changelog preparation + external Changie
  -> PDM Towncrier fragments in feature PR
     -> one generated Release PR prepares versions/changelogs
     -> protected main publishes changed Extensions
     -> Core version change selects normal production/stable

repository-local realization
  -> optional tool-agnostic organization guidance/example
```

## Side effects and compatibility

- Telegram Source config hard-cuts to `bot_token`、`bound_user_id` and `download_attachments=false`。Existing Sources lack
  sender/bot-scoped cursor proof and must be recreated；the legacy `extensions.telegram.message.v1` decoder remains readable。
- Default capture stores useful attachment metadata/caption without bytes。Explicit/eager materialization may later contact
  Telegram and write one Storage-backed semantic child。Routine success becomes a post-commit 👍 reaction。
- The obsolete webhook route is replaced by one authenticated attachment-materialization command；combined OpenAPI retains
  every integrated route。
- The core-py feature PR carries Telegram and Core release fragments but no version/changelog preparation。After merge，the new
  controller prepares Telegram `0.1.0 -> 0.2.0` and the maturity-appropriate Core version in `release/next`。
- Existing Extension changelog history remains below the Towncrier cutover marker；Core begins at its current baseline without
  fabricated history。Legacy Changie config/version entries stop being authority。
- Immutable Core images and the `main` candidate remain available after checked main commits。Normal production/`stable`
  moves only for a prepared Core version change；manual dispatch remains recovery。Extension-only Releases never deploy Core。
- The `.github` reference describes this lifecycle as optional guidance。Repository-local documentation continues to own exact
  tools、commands、paths、project mapping and delivery implementation。

## Blast radius

- Telegram runtime behavior affects only configured Telegram Sources、the bot update queue、new semantic Blocks/Relations and
  optional writable Storage bytes。
- Release-contract behavior affects contributor intent checks、Core and all first-party Extension release notes/versions，one
  generated Release PR，Extension selection and Core production cadence。
- Root dependency/lock changes are development-only Towncrier changes；Telegram adds no new runtime dependency。
- Organization impact is documentation guidance only。No shared product truth、organization enforcement setting or workflow
  changes。
- Database schema/data and scheduler behavior do not change。The existing remote development database is reused without reset。

## Invariants

- Telegram graph + cursor primary effects commit together per update；no success acknowledgement precedes them。
- Metadata-only is complete when configured；ordinary Resolver reads never perform Telegram network or graph mutation。
- One attachment has at most one semantic `content` child and later bytes require the exact live Source/pinned bot identity。
- Towncrier owns fragment validation/type rendering；repository orchestration owns affected projects、maturity-aware bumping、
  version mutation and delivery selection。
- Feature PRs carry fragments and unchanged versions/changelogs。Only the generated Release PR prepares them，and neither PR
  publishes canonical artifacts。
- Core never enters Extension publication。Core SemVer selects normal delivery；exact source SHA/digest remains artifact
  identity。
- Generated `release/next` is disposable automation output；the minimum controller has no custom lease/attestation/security
  protocol。
- Concurrent MCP and `.github` branch work is preserved and never staged、reset、cleaned or committed by this Unit。

## Verification

- Release contract：clean `pdm sync -G dev` exposes exact Towncrier without Changie/Go/PATH setup；project discovery separates
  Core from Extensions；feature intent classification covers Core、Extension、mixed、generated and dev-only dependency diffs；
  maturity-aware bumping and isolated reproducible rendering satisfy Acceptance 1–24。
- Automation：a checked-main fixture with no fragments is a no-op；pending fragments generate only allowed Release PR files；
  a later main run updates the same branch/PR；Extension-only preparation cannot select Core production。
- Telegram static/runtime：owned Ruff/format/Pyrefly，combined OpenAPI inspection，deterministic failure/race probes and the full
  coherent repository gate。
- Telegram real vertical：configured bot + bound Human + ordinary Source Job + migrated PostgreSQL/writable Storage，including
  semantic retrieval、metadata-only success、explicit materialization and 👍 after commit。
- Compatibility：published `0.1.0` legacy Block remains readable；invalid legacy cursor fails rather than inheriting a bot。
- Organization guidance：diff contains only `RELEASING.md` and the governance link，uses tool-agnostic language and does not
  weaken protected-main authority。
- No new recurring automated suite is implied；use the smallest existing checks and disposable/manual probes that demonstrate
  these observable branches。

## Ready prerequisites and bounded uncertainty

- Shared SSH/database runtime is ready at migration head `143c4f4adc85` and must not be reset or stopped。
- Ignored root `.env` is mode `0600` with non-empty Telegram token/bound-user inputs；values remain local and undisclosed。
- Towncrier `25.8.0` behavior and package compatibility are inspected；the exact executable becomes available through the
  implementation's PDM lock rather than a machine prerequisite。
- Exact private helper names、fragment prose and in-Extension decomposition may simplify during execution without reopening
  this handshake when ownership、public contracts and Acceptance remain unchanged。

## Authorization boundary

After reviewing this replacement handshake，an explicit `开始` authorizes the two isolated source/documentation diffs and the
stated non-destructive verification。It does not authorize commits、pushes、PR creation/merge、artifact publication、production
deployment、new recurring tests、MCP edits、shared-Hub edits or destructive environment/database operations。
