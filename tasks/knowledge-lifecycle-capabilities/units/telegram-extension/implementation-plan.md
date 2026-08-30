# Telegram Extension and Release Contract Implementation Plan

> Proposed Execution baseline after the accepted Product、Technical and Acceptance design through D-436 and address-sensitive
> preflight。
> It does not authorize source mutation；execution begins only after the Impact Handshake and Sir explicitly says `开始`。

## Worktree and delivery placement

Implementation uses two isolated repository branches，without mixing the currently occupied checkouts：

1. create a fresh core-py worktree/feature branch from the integrated protected-main base after PR #88 is available；place the
   release-contract migration and Telegram Extension implementation together because the feature fragments and new controller
   must arrive atomically；
2. create a fresh `InKCre/.github` worktree/feature branch from its current `origin/main` for only `RELEASING.md` and the
   governance link；do not touch its existing `feat/thin-github-workflows` checkout；
3. do not commit、push、open a PR or publish from either repository without a separate explicit Human command。

The organization guidance is independent and may merge in either order。The core-py feature PR remains self-contained and
does not require the guidance commit at runtime。

## Track A — Replace the repository release contract

### A1 — Establish one Core-and-Extension project model

1. Replace `scripts/extension_release.py` with `scripts/release.py` as the single repository release orchestrator。Discover the
   root Core project plus every first-party Extension already identified by `tool.inkcre-extension`；keep Extension-only
   enumeration available to preview/publication callers so Core cannot enter their matrix。
2. Preserve the current canonical SemVer parser and make bump calculation maturity-aware：for `0.x`，breaking/`removed`
   advances minor；for stable projects it advances major；`added`/`deprecated` select minor and
   `changed`/`fixed`/`security` select patch。
3. Classify feature diffs by delivered project ownership。Core includes application、database、runtime/delivery inputs and the
   production dependency projection；an Extension owns its Distribution inputs；generated OpenAPI follows its behavior owner；
   release infrastructure and development-only dependencies own no project Release。
4. Update `build_extension_preview.py`、Extension publication automation and PDM command names to consume the renamed shared
   discovery/version operations without creating a second project model。

### A2 — Move fragments and rendering to PDM-managed Towncrier

1. Add exact `towncrier==25.8.0` to the PDM `dev` group and lock it。Remove the Changie Action/setup、`.changie.yaml`、legacy
   release entries under root `.changes/` and every command/environment expectation for the external Go binary。
2. Add one root `towncrier.toml` with Markdown output and the ordered six accepted types。Use root `.changes/` +
   `CHANGELOG.md` for Core and each `extensions/<id>/.changes/` + local `CHANGELOG.md` for an Extension through Towncrier's
   shared-config `--dir` mode and explicit version。
3. Insert a Towncrier cutover marker above existing Extension history without reconstructing old fragments。Create the Core
   changelog at its current baseline and explicitly avoid invented historical entries。
4. Feature checking requires at least one valid native orphan fragment for each affected project and rejects fragments for an
   unaffected project、unknown types、feature-PR version mutations and feature-PR generated changelog changes。
5. Preparation copies one project's current changelog/fragments/config into a temporary directory with no Git ancestor，runs
   Towncrier there，validates the complete result，then applies only that project's fragment deletions、version line and
   changelog to the disposable Release checkout。Do not add a custom fragment allocator or TOML-writing dependency。

### A3 — Add the minimum independent Release PR controller

1. Add one workflow triggered by a successful protected-main `Repository and artifact checks` run。Checkout that checked main
   SHA，install the frozen PDM development group and prepare every project with pending fragments。
2. Use one `cancel-in-progress` concurrency group。With no generated diff，exit；otherwise commit the exact allowed preparation
   output，force-update generated branch `release/next` and use ordinary `gh` to create the PR only when one is not already open。
3. Give the job only repository contents/pull-request permissions required by its `GITHUB_TOKEN` operations。Use ordinary
   `git`/`gh` rather than a third-party PR Action、PAT、GitHub App or custom generated-branch protocol。
4. CI recognizes two modes：feature PRs carry fragments with unchanged versions/changelogs；the Release PR carries only
   consumed fragment deletions、matching version bumps and reproducible changelogs。Both remain subject to the ordinary
   repository check and protected-main merge gate；the Release PR publishes nothing。

### A4 — Make prepared Core versions select normal production

1. Keep immutable source-SHA/digest image publication and the mutable `main` candidate available after successful main checks。
2. Gate normal production delivery and `stable` promotion on a root Core version change in that main commit。An Extension-only
   Release PR merge therefore publishes selected Extension versions without deploying Core。
3. Preserve the existing production `workflow_dispatch` as an explicit recovery lane and exact SHA/digest as the artifact
   identity。It does not manufacture changelog/version history。
4. Update core-py contributor and deployment documentation from source-PR Changie preparation to feature fragments、Release PR
   preparation and protected-main delivery。Add a Core `changed` fragment for this observable delivery-contract change。

### A5 — Publish optional organization guidance separately

1. In the isolated `.github` worktree，add concise tool-agnostic `RELEASING.md` guidance for feature fragments、repository
   project classification、independent preparation PR、pre-1.0 bumping and protected-main delivery authority。
2. Link it once from `GOVERNANCE.md`'s protected-main release section。Do not prescribe Towncrier、core-py paths、one branch
   name or repository-specific commands，and do not add organization workflows。

## Delivery topology

```text
ordinary core.source.collect.v1 Job
  -> extensions.telegram Source + python-telegram-bot 22.8
  -> per-update primary PostgreSQL transaction
       -> core text/html and/or Telegram attachment metadata
       -> Source cursor
  -> optional attachment materialization
       -> existing writable Storage + core semantic content child
  -> post-commit 👍 or qualified reply

explicit /telegram/attachments/materialize
  -> Telegram attachment Resolver
  -> live owning Source + current bot credential
  -> same idempotent materialization operation
```

The implementation stays inside `extensions/telegram/**`。The only expected repository-external consequence is regeneration
of `docs/openapi.json` for the materialization route，serialized against the co-resident MCP Sink route set。

## Slice 1 — Replace the PoC contracts without losing its published decoder

1. Replace the Source config with strict `bot_token`、positive numeric `bound_user_id` and
   `download_attachments: bool = False`。Remove `collect_method` and webhook configuration。
2. Add a typed Source state with optional `bot_id` and `last_update_id`，accepting unknown state fields but rejecting the
   legacy/inconsistent `last_update_id`-without-`bot_id` branch before Telegram update fetch。
3. Add canonical attachment metadata and solved projection models。Persist only retrieval/materialization facts：kind、
   `file_id`、`file_unique_id`、filename、declared MIME/size and available title/performer/emoji/dimensions/duration。
4. Retain the exact `extensions.telegram.message.v1` class and historical schema solely as a read-only legacy decoder。
   Register the new exact `extensions.telegram.attachment.v1` Resolver alongside it。
5. Do not add a Telegram Message、User、Chat、Album or generic remote-resource model。

## Slice 2 — Build one extension-local primary collection path

1. Use one short-lived `telegram.Bot` async context per collect command。Validate state，call `getMe()` and transactionally
   pin/recheck `bot_id` before calling `getUpdates`。
2. Fetch at most 100 updates with `allowed_updates=["message"]` and `offset=last_update_id + 1` when a cursor exists。Process
   ascending `update_id` values；continue full pages and stop after a short page or retryable primary failure。
3. Admit only private direct messages from exact `bound_user_id`。Consume unauthorized and stale non-message updates through
   a cursor-only transaction without graph or reply。
4. Treat exact `/start` as control：cursor-only commit followed by brief usage guidance。No other command grammar enters MVP。
5. Project Telegram entities through PTB's `text_html` / `caption_html`。Use `core.text.v1` when no useful entity semantics
   exist and `core.html.v1` otherwise。
6. Select the largest photo candidate and one exact attachment from the admitted photo/animation/audio/document/sticker/
   video/video-note/voice set。Avoid `effective_attachment` and collapse animation's backward-compatible document view。
7. For each update，open one caller-owned session，lock/recheck the Source row，ensure its `core.source.v1` anchor when an
   attachment exists，persist all primary Blocks/Relations and update `last_update_id` in the same commit。Use
   `Source --collects--> attachment` and `attachment --caption--> text/html`；plain text needs no Telegram provenance root。
8. If a concurrent runner sees an already accepted cursor，create no graph、enrichment or acknowledgement and continue from
   the live state。

## Slice 3 — Add one idempotent attachment materialization operation

1. Attachment Resolver solved/text/label behavior reads metadata plus an optional single `content` relation。It ignores
   `materialize_missing` for network effects so ordinary retrieval/indexing never downloads bytes。
2. Materialization derives exactly one live Telegram Source through the incoming Source-anchor `collects` relation。It
   validates current config/state，verifies that the current token still resolves to the pinned `bot_id` and uses the stored
   bot-scoped `file_id` to request a fresh file location。
3. Download outside the database transaction with PTB `get_file()` + `download_as_bytearray()`。Never persist temporary
   `file_path` URLs。
4. Classify by detected bytes，Telegram-declared MIME，filename extension，attachment kind，then `core.file.v1` fallback。
5. Lock/recheck the metadata Block，resolve the Source's current writable Storage，then atomically write bytes、one core
   semantic Block and one `content` relation。Return the existing child when another caller won the race。
6. Map absent/deleted Source、ambiguous provenance、bot mismatch and deterministic provider file limits to explicit
   materialization-unavailable outcomes。Network/provider failures remain retryable at the explicit operation boundary。
7. Replace the retired webhook route with one authenticated Extension route，`POST /telegram/attachments/materialize`，for
   one attachment Block。Follow the existing Mail command shape：404 unknown Block，422 wrong Resolver，409 unavailable and
   the materialized/existing semantic `BlockModel` on success。No batch/API framework is added。
8. When `download_attachments=true`，collection calls this same operation after primary commit。Failure records bounded
   enrichment diagnostics and produces a qualified partial reply without changing cursor or metadata。

## Slice 4 — Make completion truthful and observable

1. Initialize bounded Job state before processing and retain counts plus bounded per-update diagnostics for saved、partial、
   unsupported、unauthorized、primary failure、materialization failure and acknowledgement failure。
2. After complete primary acceptance，call `set_message_reaction(..., reaction="👍")` on the originating message。Do not send
   `committed` text。
3. Send a reply only for `/start` guidance or partial/unsupported/retryable-primary-failure qualification。State whether
   primary information was saved and whether retry remains possible；exact prose stays implementation-owned。
4. Treat post-commit reaction/reply failure as diagnostic only。A Job may still finish after a lower-value notification or
   enrichment failure；a primary failure raises so the Job closes failed and the cursor remains retryable。
5. Accept Telegram's media-group reaction routing to the first non-deleted group message。Do not buffer/reconstruct albums。

## Slice 5 — Reconcile the first-party Distribution

1. Remove obsolete webhook/`collect_method` claims from README and document direct private delivery、exact sender config、
   default metadata-only attachments、optional eager bytes、manual/Cron ownership and one-bot-per-Source guidance。
2. Add Telegram `added`/`removed` Towncrier fragments for the direct inbox and Source hard cut while the published legacy
   Resolver remains readable。The feature PR leaves `0.1.0` unchanged；the independent Release PR applies the accepted
   pre-1.0 rule and prepares `0.2.0`。
3. Regenerate `docs/openapi.json` only after the MCP Sink route set is stable，then inspect the combined diff so neither
   unit's routes disappear。
4. Do not add a migration、client-web contribution、setup UI、Cron、generic Resolver/Source framework or durable shared-doc
   edit in this slice。

## Slice 6 — Verify the accepted behavior

1. During implementation run owned-path Ruff/format/Pyrefly and focused disposable protocol/transaction checks，then the
   repository gate once co-resident MCP work is at a coherent checkpoint。
2. Execute A1/A2 with a real bot、bound Human identity、ordinary production Source Job and disposable migrated PostgreSQL +
   writable Storage。Hydrate materialized bytes and exercise ordinary retrieval。
3. Use deterministic PTB doubles/fault injection for sender rejection、stale updates、primary failure、concurrent runners、
   materialization limits/transient failures and reaction failure。These supplement the real-bot path。
4. Run A6 against one published `0.1.0` legacy Block and invalid legacy cursor state。
5. Keep the first acceptance realization manual/scripted。No recurring automated test is added unless Sir separately
   approves it after demonstrated regression value。
6. Run the renamed release-intent check and the full repository gate through the locked PDM environment，without any external
   Changie binary and without cleaning/staging MCP Sink files。

## Frozen invariants for execution review

- Primary graph/cursor commit is the only collection progress authority。
- Metadata-only is complete when configured；byte materialization is enrichment。
- A success reaction means configured primary information is durable，not that every optional enrichment succeeded。
- Ordinary Resolver projection is side-effect free with respect to Telegram/network/graph mutation。
- One attachment has at most one semantic `content` child；concurrent losers reuse it。
- Current Source provenance and pinned bot identity are required for later remote bytes；no guessing across Sources/bots。
- Telegram implementation does not absorb MCP Sink/Core framework changes from the shared worktree。
- Towncrier renders project news；repository orchestration alone owns project impact、version calculation and delivery selection。
- Feature PRs carry fragments；only the generated Release PR carries version/changelog preparation and neither PR publishes。
- Core production selection uses the prepared Core version；exact SHA/digest remains artifact identity。
- No source mutation、generated OpenAPI update、release preparation or new automated test occurs before the final Impact
  Handshake and explicit `开始`。
