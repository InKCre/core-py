# Telegram Extension Acceptance

- **Status**: Human-agreed and preflighted Execution-baseline candidate；not implementation authorization until the Impact
  Handshake is reviewed and Sir explicitly says `开始`。
- **Purpose**: prove that an operator-configured Telegram Source turns useful direct bot messages into retrievable semantic
  info-base content with truthful sender feedback、admission and retry behavior。It does not prove Telegram object fidelity、
  a setup UI or scheduler latency。

## Evidence allocation

- The primary value journey uses a real Telegram bot、the bound Human Telegram identity、the production Extension/Source/Job
  path and a disposable migrated PostgreSQL database with writable Storage。
- Real sent text and media bytes must reach the committed graph and be read back through ordinary Block hydration、Resolver
  behavior and retrieval；hand-authored graph fixtures cannot replace this vertical evidence。
- Deterministic transport doubles or controlled failure injection may pressure cursor、transaction、acknowledgement and
  concurrency consequences that cannot be reproduced reliably against Telegram。They supplement rather than replace the
  real-bot journey。
- Pydantic/schema、registration、package shape and absence of retired contracts belong to static verification。Do not add
  automated tests merely to mirror those literals。
- These journeys are initially manual or scripted acceptance evidence。Promotion into recurring automated regression tests
  requires the task's separate Human approval and demonstrated regression value。

## A1 — Direct text becomes ordinary retrievable information

1. Enable the production Telegram Extension and create one Source through the production Source-creation boundary with a
   valid `bot_token`、the bound Human's numeric `bound_user_id` and writable PostgreSQL Storage。No pairing/setup operation is
   performed and initial Source state has no `bot_id` or cursor。
2. The bound user sends the exact `/start` command，authors one useful text message containing meaningful formatting and a
   link，and forwards one independently useful text message directly to the bot。
3. Execute an ordinary `core.source.collect.v1` Job through the production Job Handler。The first `getMe` pins the exact
   `bot_id` before updates are fetched；the admitted updates commit and advance the Source cursor in Telegram update order。
4. `/start` creates no graph and receives brief usage guidance；it neither binds the sender nor enters setup。The authored and
   forwarded messages produce ordinary `core.text.v1` or inline `core.html.v1` Blocks as required by useful Telegram
   text/entity semantics。The graph contains no `extensions.telegram.message.v1` root and does not retain sender/chat/forward
   envelope fields as information merely because Telegram supplied them。
5. Each successful message receives one ordinary 👍 reaction on the original message only after its graph/cursor effect is
   durable；no routine `committed` reply is sent。Ordinary Resolver/read and retrieval paths recover the saved meaning without
   Telegram-specific presentation。
6. A second collect with no new updates creates no duplicate graph effect and sends no duplicate success acknowledgement。
7. A message sent by the bound user before Source creation but still present in Telegram's unconfirmed queue is admitted by
   the first collect。Acceptance does not invent a Source-creation-time cutoff or claim recovery after Telegram's retention
   horizon。

## A2 — Attachment metadata is useful without eager bytes

1. The bound user sends a captioned image、a captioned video and a downloadable document with a meaningful filename directly
   to the bot。Create the Source without overriding `download_attachments=false`。
2. An ordinary collect Job persists one `extensions.telegram.attachment.v1` metadata Block for each attachment，including
   its durable Telegram file locators and use-relevant kind、filename、declared MIME/size and available dimensions/duration。
   It writes no attachment bytes and creates no `content` child merely because the attachment was delivered。
3. Useful captions are independent text/HTML Blocks connected from the attachment；the metadata Resolver exposes filename
   and type facts to ordinary text/label retrieval without triggering network I/O。There is no Telegram message wrapper。
   Metadata-only collection is the configured complete outcome，so each message receives 👍 without a warning reply。
4. Multiple album items，if included in the chosen real corpus，remain independently retrievable content；Acceptance does not
   require reconstruction of a Telegram album/message envelope or incidental database order。Because Telegram redirects an
   item's reaction to the media group's first non-deleted message，one visible group-level 👍 is accepted；a qualified failure
   for an individual item must still be explicit rather than hidden by that check。
5. Static/protocol-double evidence covers the admitted file-bearing dispatch set and proves that duplicate protocol views of
   one attachment（such as animation plus backward-compatible document）produce one metadata Block。Acceptance does not need
   a separate real Telegram upload for every admitted media class when the metadata/materialization path is identical。
6. Invoke the attachment's explicit materialization capability，then repeat it。The first call resolves the live owning
   Telegram Source，downloads known bytes through the current bot，writes one matching `core.image.v1`、`core.video.v1`、other
   exact semantic Resolver or `core.file.v1` child through the Source's writable Storage and relates it as `content`；the
   second call returns the existing child。Hydration equals the original bytes and no duplicate child is created。
7. With `download_attachments=true` on a separate Source/corpus，ordinary collection invokes the same materialization path
   automatically after primary metadata/cursor commit；it does not use a second eager-download representation。

## A3 — Exact sender admission cannot pin later owner content

1. A Telegram identity other than `bound_user_id` sends a private message to the bot，followed by a useful message from the
   bound user。
2. Collection produces no graph effect for the unauthorized update but durably advances past it。The later bound-user update
   is saved normally in the same or next bounded batch。
3. Missing/invalid `bound_user_id` is rejected as Source configuration rather than selecting a sender during collect。A
   username match or first-sender rule cannot satisfy this journey。
4. Rotating to a token that resolves to the same pinned bot preserves collection continuity。A token resolving to another bot
   fails before fetching its updates and does not reinterpret or advance the existing Source cursor。

## A4 — Retryable primary failure preserves exactly-once accepted progress

1. Arrange two ordered admissible updates and inject a retryable primary metadata/graph-persistence failure for the first
   update before its accepted commit boundary。
2. The Job reports failure，the failed update's cursor does not advance，no success acknowledgement is sent and the later
   update is not skipped。No partial primary graph is presented as saved。
3. Remove the injected fault and run a new ordinary collect Job。The first update is saved once，then later updates proceed in
   order。Already committed updates from any earlier batch remain valid and are not replayed。
4. When two collect Jobs race on the same update，the Source cursor lock/recheck admits one primary effect；the losing runner
   creates no duplicate graph or acknowledgement。Acceptance cares about the observable single effect，not which Job wins。

## A5 — Unsupported content and acknowledgement failure have shallow truthful outcomes

1. Deliver an update with no accepted semantic content，followed by a supported update。Also allow a stale non-message update
   to appear despite the explicit `allowed_updates=["message"]` request。Each unsupported update creates no graph，records a
   bounded unsupported outcome and advances the cursor so the supported update can be saved。
2. For a supported update，inject 👍 reaction failure only after graph/cursor commit。The Job retains actionable diagnostics，
   but the durable content remains accepted and a later collect does not replay it or send a duplicate routine reply。
3. With `download_attachments=true`，send a captioned attachment beyond the standard Bot API's downloadable-file limit and
   separately inject a transient download failure。In both cases metadata/caption and cursor remain durably accepted and 👍
   marks that fact；no `content` child is created，and a correlated partial reply states that bytes were not materialized。
   Explicit later materialization returns a deterministic-unavailable or retryable failure respectively without mutating the
   accepted cursor。Acceptance does not freeze today's numeric provider limit as an InKCre configuration parameter。
4. Delete or invalidate the owning Telegram Source before explicitly materializing a metadata-only attachment。The operation
   reports materialization unavailable，does not guess another Source/bot and leaves metadata/retrieval intact。

## A6 — Published legacy content remains readable without inheriting an unscoped cursor

1. Seed one valid `extensions.telegram.message.v1` Block using the published `0.1.0` content shape and enable the upgraded
   Extension。The exact legacy Resolver still produces its historical solved/text/label behavior；ordinary new collection
   never emits another Block of that type。
2. Present a legacy Source state containing `last_update_id` but no `bot_id`。Even after config gains a numeric
   `bound_user_id`，collect fails before `getUpdates` because the cursor's bot identity cannot be proven。
3. Create a new direct-configured Source for the intended bot/sender and collect from its currently unconfirmed queue。No
   migration resets the legacy cursor、rewrites historical Telegram Blocks or claims recovery of already confirmed/expired
   updates。

## Deliberately outside this Acceptance

- Creation or correctness of a Cron、a specific collection frequency or an end-to-end latency target；the user owns manual
  and scheduled Job creation independently。
- Recovery of updates after Telegram's externally owned retention horizon or a Source promise to compensate for a schedule
  that did not collect in time。
- Runtime prevention or isolation of two operator-configured Sources sharing one bot identity。User-facing configuration
  guidance states that this is unsupported because both Sources would consume one Telegram confirmation queue；future setup
  UI may prevent it without turning Source collection into a cross-Source coordination system。
- Pairing code、deep link、setup transaction、Telegram-specific setup UI、username admission or first-sender binding。
- Bot membership in groups/channels、chat synchronization、history import、edited-message lifecycle or Telegram envelope
  reconstruction。
- OCR、ASR、summarization、Organization behavior or specialized Telegram browsing UI。
- Automatic byte download when `download_attachments=false`，silent Resolver-triggered network access，or preservation of a
  temporary Telegram `file_path` URL whose validity is externally bounded。
- Exact row IDs、incidental relation order、implementation helper shape or exhaustive Telegram update-family coverage。

## Open Acceptance pressure

- Preflight must determine whether a real second Telegram identity is available for A3；otherwise a protocol double must
  prove unauthorized-queue progress without weakening A1/A2 real-bot evidence。
- The exact bounded Job diagnostic shape is Technical work still pressure-tested by A4/A5；Acceptance requires truthful,
  correlated outcomes but should not freeze an incidental JSON layout before callers demonstrate that need。

## Release-contract Acceptance pressure after scope expansion

The replacement Acceptance must additionally prove all of the following；exact commands and file layout remain Technical
work until the release-cadence fork is resolved：

1. A clean `pdm sync` with the declared development group provides the pinned Towncrier CLI。Release checks and preparation
   require no separately installed Changie、Go toolchain、Homebrew package or `CHANGIE`/PATH override。
2. Core and every first-party Extension are discoverable release-contract projects，but Extension preview/publication
   enumeration never treats Core as an Extension artifact。
3. The bump policy remains observable：Added/Deprecated select minor，Changed/Fixed/Security select patch，and Removed selects
   major only for stable projects；for `0.x` it selects minor。Multiple fragments select the highest maturity-aware bump。The
   orchestration，not Towncrier，owns next-version calculation and exact `pyproject.toml` mutation。
4. Towncrier owns fragment validation/type rendering and changelog composition。Historical released changelog entries remain
   byte-for-byte meaningful beneath the cutover marker；legacy Changie config/version entries do not become a second current
   authority。
5. Preparing one project changes only that project's version、changelog and fragments。Render/validation failure leaves the
   project untouched，and successful preparation leaves the pre-existing Git index unchanged despite Towncrier's native
   unconditional newsfile staging behavior。Other dirty Unit work remains intact。
6. An Extension-only source change does not accidentally advance Core，and a Core-only change does not advance or publish an
   Extension。Project-impact classification follows delivered behavior ownership rather than every changed repository byte；
   a mixed change requires independent intent for every affected project。
7. An ordinary feature PR changes project artifact inputs only when it adds at least one valid fragment for every affected
   project。It does not mutate that project's version or generated changelog。CI rejects missing/invalid fragments and rejects
   source-PR attempts to perform release preparation。
8. After feature fragments reach protected `main`，one serialized repository-owned controller creates or updates one
   independent Release PR。That PR consumes all currently pending fragments、selects the highest bump independently per
   affected project、updates the matching `pyproject.toml` versions and renders only those changelogs。A later main change
   updates the same open Release PR rather than creating competing preparation branches。
9. The Release PR is subject to ordinary protected-main review/check/current-base rules and carries no publication authority。
   Only after it merges does the main release lane select changed Extension versions for canonical Registry publication；Core
   is never added to that Extension matrix。No canonical artifact is published from the Release PR。
10. With no generated release diff，the controller exits without creating an empty Release PR。Rerunning from the same checked
    main state produces the same prepared files。
11. The controller uses one fixed generated `release/next` branch/PR and one `cancel-in-progress` repository concurrency group。
    A later run force-updates that disposable branch。The generated PR diff contains only project fragment deletions、version
    mutations and rendered changelogs；any product/source diff fails。
12. Towncrier preparation occurs under a temporary directory with no Git ancestor。The resulting validated files are applied
    only to the disposable Release branch checkout，and the Towncrier process cannot stage、unstage or remove files from the
    caller's repository index。A render failure produces no release commit or branch update。
13. The controller uses repository `GITHUB_TOKEN` plus ordinary `git` and `gh`，with no PAT、GitHub App or third-party PR
    action。The generated Release PR passes the repository's normal review and required checks before merge。
14. An ordinary protected-`main` change that leaves the Core version unchanged does not normally deploy production or advance
    the `stable` channel，even when CI retains immutable source-SHA/digest evidence or a mutable `main` candidate reference。
15. A merged Release PR that changes the Core version selects that exact protected-`main` source SHA/digest for normal
    production deployment and `stable` promotion。An Extension-only Release PR merge never deploys Core，and a Core release
    never enters the Extension publication matrix。SemVer is the release-selection and Human contract；the immutable
    SHA/digest remains the deployed artifact identity。
16. Explicit `workflow_dispatch` remains a visible recovery lane that may redeploy a selected current artifact without
    manufacturing a version/changelog change。It is not the ordinary unversioned production-delivery path and cannot rewrite
    Release PR history or confer publication authority on a pull request。
17. CI rejects a Core behavior change without a Core fragment、an Extension Distribution change without that Extension's
    fragment，and a mixed change missing either intent。A generated `docs/openapi.json` consequence follows its behavior owner
    and does not independently trigger Core。
18. Towncrier/release-controller/contributor-guidance changes and a development-only dependency/lock change create no false
    Core Release。A production-dependency projection change does require Core intent even though both cases may touch the same
    root `pyproject.toml` and `pdm.lock` files。
19. Core and every discovered Extension accept the same six lowercase fragment types from their project-local `.changes/`
    directory through one root Towncrier config。A native `+<generated-id>.<type>.md` orphan fragment is valid without an issue
    or pull-request number，and two independently created fragments do not collide。
20. One project cannot consume、render or delete another project's fragments。A prepared Extension changelog retains its
    existing history below the cutover marker；the new Core changelog identifies its current baseline without fabricating old
    release entries。
21. Fragment content is non-empty、valid Markdown and represents user-useful project news。Unknown types、invalid names and
    release-infrastructure-only fragments fail validation rather than silently selecting or polluting a project Release。
22. For a project at `0.x`，a highest `removed`/breaking fragment advances minor and resets patch；for a stable project it
    advances major。`added`/`deprecated` remain minor，`changed`/`fixed`/`security` remain patch，and the highest applicable bump
    wins。Telegram's accepted hard-cut Source change therefore prepares `0.2.0` from `0.1.0`。
23. Organization guidance describes the lifecycle and responsibility split without requiring Towncrier or core-py's exact
    paths、branch name、project mapping or commands。It preserves protected `main` as canonical authority and labels
    repository-local release mechanics as repository-owned。
24. The `.github` guidance change is isolated on its own current-main-based worktree/branch and contains only the durable
    release reference plus its governance link；it does not include the unrelated existing `.github`
    `feat/thin-github-workflows` branch state or any core-py implementation commit。
