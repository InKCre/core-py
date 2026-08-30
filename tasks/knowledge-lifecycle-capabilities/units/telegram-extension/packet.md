# Telegram extension

## Control

- **State**: Active；Telegram Product contract is accepted，and Sir has expanded this Unit to replace repository-wide
  Changie with PDM-managed Towncrier for Core plus first-party Extensions。The Unit remains registered in the
  peer-maintained parallel roster under session `01a04685-aa31-7682-a4a2-824727eacce5` with reserved decision range
  D-421–D-460。
- **Program owner**: [knowledge lifecycle capabilities](../../packet.md) remains the only program control authority；this
  file owns the Telegram unit's Product-through-Verify working state。
- **Packet topology**: this is an implementable Unit packet inside the exceptional parent Task，not an independent SVC Task。
  Its shape and lifecycle follow the parent Task's `collaboration/**` protocol；do not run `svc task init/grow` against this
  Unit or create a second task-control authority。
- **Current phase**: Implementation and Verify are complete；real Telegram text、metadata-only attachment、explicit
  materialization、supported `👍` acknowledgement and the complete repository gate passed。See
  [Implementation Evidence](implementation-evidence.md)。
- **Current placement**: after PR #88 merged as protected-main commit `459a6df`，core-py implementation moved to
  `.worktrees/core-py-telegram-integrated` on `feat/telegram-source-towncrier-integrated`。Organization
  guidance is isolated in `.worktrees/github-release-guidance` on `feat/release-lifecycle-guidance` from `.github`
  `origin/main` `6c7d802`。The former pre-merge implementation worktree remains only as an uncommitted transfer backup until
  integrated verification completes；it is not the delivery branch。The retained MCP worktree remains untouched。
- **Allocated implementation boundary**: Telegram runtime behavior remains confined to `extensions/telegram/**` plus its
  generated OpenAPI consequence。The same Unit additionally owns the repository-wide Changie-to-Towncrier release-contract
  migration，including Core，root dependency/lock、release tooling/automation、changelog/fragment convention and contributor
  guidance，plus one tool-agnostic `InKCre/.github` release-guidance reference on its own repository branch。Core
  Source/Resolver/Extension framework and migrations remain outside ownership。
- **Next surface**: final Human-authorized delivery。Commit、push and PR creation remain separately unauthorized。

## Product outcome

A deployment owner configures one Telegram bot，then sends or forwards useful content to that bot。InKCre retains the
valuable content as ordinary reusable info-base information so it can be browsed、retrieved and later organized。Telegram
is the collection transport，not the durable information model。

The intended user journey is：

```text
send/forward useful content to Telegram bot
  -> bot admits the update for this configured Source
  -> InKCre persists the useful semantic content
  -> bot marks a durably accepted message with 👍 and replies only when qualification is needed
  -> ordinary info-base retrieval can recover the persisted content
```

MVP maturity is judged by whether this low-friction capture job is reliable and whether discarded meaning、delay、failure
and setup cost are acceptable。Protocol field coverage or Telegram object fidelity is not a maturity target。One Source admits
exactly one bound Telegram user sending or forwarding content directly to the bot。The bot does not join、observe or synchronize
the conversation from which content was forwarded；its private conversation with the user is only the delivery inbox，not a
collected chat resource。Groups、channels and open-inbox collection are outside the MVP。This is an Extension/Source protocol
admission fact，not a core User、ACL or tenant domain。

The expanded repository outcome is that every first-party releasable project，including Core and each Extension，uses one
PDM-managed Python release-note tool。Towncrier owns fragment parsing、fragment types and changelog rendering；the repository
release orchestration owns project discovery、artifact scope、SemVer bump policy、next version、`pyproject.toml` version and
delivery-specific checks。No external Go binary or PATH-level tool prerequisite remains。

Feature pull requests carry project-scoped Towncrier fragments but do not prepare versions or changelogs。After those changes
reach protected `main`，one repository-owned controller creates or updates an independent Release PR that consumes pending
fragments、bumps every affected project independently and renders its changelog。Only merging that Release PR returns prepared
versions to protected `main`，where the existing main-authority delivery lane may publish changed Extension Releases。Core
joins the release-note/version contract without becoming an Extension publication target。A Core version change returned by
the Release PR is the normal production/`stable` selector；an Extension-only Release does not deploy Core。The exact protected-
`main` source SHA/digest remains Core deployment artifact identity，and explicit manual dispatch remains a separate recovery
lane。

## Accepted representation direction

Do not introduce or preserve a `TelegramMessage` Block/Resolver merely because Telegram delivered a `Message` object。
Map admitted payloads directly to the existing semantic content contracts such as `core.text.v1`、`core.html.v1`、
`core.image.v1`、`core.video.v1`、`core.audio.v1` and `core.file.v1`。Actual external bytes use the existing writable
Storage path；Storage does not own Telegram or retrieval semantics。

The default graph should contain only information with later use value。A Telegram-specific metadata root such as
`TelegramMessage --body--> text` is justified only if independent message identity、provenance、association or lifecycle
meaning is required by the accepted journey。Transport envelope fields are otherwise discarded after they have served
admission、ordering、diagnostics or acknowledgement。

Accepted content shapes：

```text
plain text             -> core.text.v1 Block
text with useful entity/link semantics
                       -> core.html.v1 Block
Telegram attachment    -> extensions.telegram.attachment.v1 metadata Block
                       -> optionally --content--> core.image/video/audio/file.v1 Block
captioned attachment   -> metadata Block --caption--> core.text/html.v1 Block
```

`extensions.telegram.attachment.v1` is not a Telegram message envelope。It is the durable remote-file locator and
use-relevant metadata needed before bytes exist and for later materialization：attachment kind、bot-scoped `file_id`、stable
`file_unique_id`、declared filename/MIME/size and the small kind-specific facts needed for retrieval such as dimensions or
duration。The Resolver projects filename/type metadata for retrieval without silently downloading bytes。The metadata Block
has at most one `content` child，whose existing core semantic Resolver owns hydrated bytes。Caption remains independently
authored semantic text；filename remains canonical attachment metadata rather than a duplicate text Block。

MVP admits authored text plus conventional downloadable `photo`、`animation`、`audio`、`document`、`sticker`、`video`、
`video_note` and `voice` payloads。For Telegram's photo-size tuple，retain only the largest available original candidate；when
an animation is also exposed through the backward-compatible `document` field，materialize it once。Paid media、stories、live
photos and newly added rich/structured families require deliberate future admission rather than falling through a broad
`effective_attachment` switch that also includes contacts、dice、polls and payments。

Use the pinned `python-telegram-bot` entity projection for best-effort HTML rather than implementing Telegram's UTF-16 entity
offset grammar again。Plain text/caption with no useful entity semantics remains `core.text.v1`；useful formatting or link
semantics becomes inline `core.html.v1`。Materialized bytes use a Storage-backed `BlockForm` with the selected core Resolver；
the existing URL-oriented media `create_graph()` helpers do not define or block this producer path。

The MVP has no Telegram message root。Update ID、sender、chat、forward origin and reply metadata serve admission、cursor、
diagnostics and post-commit reaction only。Albums/media groups are collected as independent semantic content without
reconstructing their Telegram envelope。Location、contact、poll、dice、service messages and other values without an accepted
semantic content contract are explicitly unsupported。

The published `extensions.telegram.message.v1` Resolver remains registered as a read-only legacy decoder for Blocks produced
by `0.1.0`。No new collection path creates that Block shape，and the unit does not migrate、rewrite or delete historical
Telegram Blocks merely to normalize them to the new semantic graph。

The exact `/start` bot command is delivery-inbox control，not authored information。For an already configured Source it
advances the cursor without graph persistence and receives brief usage guidance；it does not bind a sender or reopen a setup
workflow。No other Telegram command surface enters MVP。

This direction does not make retrieval indexes or projections graph authority。Collection persists use-oriented semantic
information and necessary relations；feature、semantic and graph-navigation retrieval continue to consume that ordinary
graph through existing Resolver contracts。

## Accepted user-visible completion

One Telegram update is decomposed into independently useful content parts：

- supported text and caption are persisted through their semantic contracts；each admitted attachment always persists its
  use-relevant metadata，while bytes are an independently materializable semantic child；
- a deterministically unsupported component does not discard an independently useful supported component，and the bot
  reports the exact partial outcome；
- a primary metadata/graph persistence failure does not advance the Source cursor，so the update remains retryable；an
  attachment download/materialization failure does not reinterpret already durable metadata as an uncollected message；
- an update with no supported content receives an unsupported outcome and advances the cursor rather than pinning later
  messages；
- complete primary acceptance is marked by a 👍 reaction on the originating message only after the graph/cursor effect is
  durable，without sending a routine `committed` reply；
- unsupported、partial and retryable-failure replies are reserved for qualification that a check alone cannot communicate；
  reaction/reply failure after durable persistence is diagnostic residue，not a reason to replay primary collection。

The Source processes and checkpoints updates in Telegram order。A later failure preserves already committed earlier updates
and resumes from the first unaccepted update；Job state reports saved、partial、unsupported and failed outcomes without
becoming information authority。

## Accepted direct-sender configuration

The bot is a direct delivery inbox。The user may forward content from any Telegram conversation or author a new message in
the one-to-one conversation with the bot；the bot never joins、reads or synchronizes the originating conversation。

MVP uses exact operator configuration instead of a pairing transaction：

```text
Source config
  bot_token
  bound_user_id
  download_attachments = false

Source state
  bot_id
  last_update_id
```

- The deployment owner supplies Telegram's numeric user ID through the existing schema-driven Source creation form。The
  Source is already sender-bound when created；MVP has no pairing code、pairing transaction、Telegram setup API or Telegram
  setup UI。
- Missing or invalid `bound_user_id` makes Source configuration invalid。Collection never selects、discovers or changes the
  bound sender。
- `download_attachments` defaults to `false`，matching the use-first Mail/RSS attachment pattern：collection retains remote
  metadata without paying byte transfer and Storage cost。Setting it to `true` requests best-effort automatic materialization
  through the same attachment Resolver command available for explicit later materialization；it does not create a second
  attachment representation or change what 👍 means。
- Later content must come from that exact numeric user ID through a private direct message to the bot。
- `chat_id` is only the current message's reaction/reply destination；it is not persisted as a Source target or collected-chat
  identity。
- Updates from other users are rejected and consumed so they cannot pin the bot's global update queue；they never reach
  info-base persistence。
- On the first collect，`getMe().id` verifies the credential and atomically pins `bot_id` before fetching updates。Later
  collection requires the same bot identity；a token rotation resolving to that bot continues，while a different bot fails
  rather than inheriting its cursor。
- Empty Source state is the only unpinned initial state。A state containing `last_update_id` without `bot_id` is a legacy or
  inconsistent cursor whose bot scope cannot be proven；collection fails before `getUpdates` and requires a newly configured
  Source instead of guessing、resetting or inheriting that cursor。
- Telegram exposes one confirmation cursor for one bot identity，not one queue per Source。Deployment guidance therefore
  requires one bot identity to be configured for at most one Telegram Source。MVP does not enforce this through cross-Source
  queries、database constraints or distributed locks；doing so would contaminate Source topology for a visible、recoverable
  operator misconfiguration with low marginal harm。A future setup UI should warn or prevent the duplicate locally。
- MVP has no rebind/reset state machine；a different bot or sender uses a new Source。
- Username admission and “bind the first sender during collect” are outside MVP。A Telegram username is optional and mutable，
  while first-sender binding can admit the wrong identity and makes collection perform setup。

## Accepted polling execution and persistence

Collection uses bounded `getUpdates` batches through the ordinary typed Source Job path；the Extension does not run a
process-lifetime Telegram polling loop。

```text
getMe -> verify exact bot_id
  -> getUpdates(offset=last_update_id + 1, allowed_updates=["message"])
  -> process update_id order
       -> classify semantic text and attachment metadata
       -> lock and recheck Source cursor
       -> persist primary semantic graph + attachment metadata + cursor
       -> commit
       -> optionally materialize attachment bytes outside the primary transaction
       -> react 👍 on complete acceptance；reply only for qualified outcomes
```

- Each update is one progress boundary。Earlier committed updates remain accepted when a later update fails；a retryable
  failure stops the batch so the cursor never skips the failed update。
- Unauthorized and deterministically unsupported updates write no graph but still advance the cursor atomically so they
  cannot pin later owner content。
- With no existing cursor，the first collect starts from Telegram's earliest still-unconfirmed update and admits every
  retained bound-user message。It does not drop the queue or infer a Source-creation timestamp horizon。Telegram retains
  incoming updates for no longer than 24 hours；collection frequency and resulting expiry loss remain user/deployment
  scheduling consequences，not a Source completeness promise。
- `allowed_updates=["message"]` is still an admission optimization rather than an exhaustive queue invariant：Telegram says
  the setting does not affect already-created updates immediately。Any returned non-message update is consumed as
  unsupported so it cannot pin the bot cursor。
- The primary transaction locks the live Source，rechecks that the update is still unprocessed，then coordinates semantic
  text、attachment metadata、Relations and `last_update_id`。It does not hold a database transaction across Telegram file I/O。
- Each attachment metadata Block is reachable from the Source anchor so later materialization can recover the one current
  bot credential that owns its `file_id` without copying Source identity into canonical attachment content。Materialization
  resolves and validates that live Source，requests a fresh `getFile` location，downloads outside the transaction，then locks
  and rechecks the attachment before atomically writing bytes and its single `content` relation to the Source's writable
  Storage。Missing/deleted/rebound Source access is an explicit materialization-unavailable result；metadata remains useful。
- `download_attachments=true` invokes that same idempotent materialization path after the primary update commit。A materialize
  failure is recorded as enrichment diagnostics and may produce a correlated partial reply，but the accepted cursor and
  metadata are not rolled back or replayed。With the default `false`，metadata-only collection is a complete configured
  outcome and receives 👍 without a warning。
- A concurrent runner that loses the cursor recheck performs no duplicate primary effect and sends no duplicate
  acknowledgement。
- Complete success acknowledgement is one ordinary 👍 emoji reaction on the originating private message，sent only after
  commit through Telegram's native reaction method。A reaction failure is recorded in Job diagnostics and does not replay
  durable content。A retryable primary failure may send a best-effort failure reply but does not advance cursor。
- Telegram applies a reaction addressed to any media-group item to that group's first non-deleted message。MVP accepts this
  provider-owned visual correlation and does not introduce album buffering or a Telegram envelope solely to manufacture one
  check per item；a failed/partial item still receives its explicit reply qualification。
- Partial、unsupported or retryable-failure outcomes reply to the originating private message when Telegram permits it，
  providing natural per-update correlation。A partial outcome may carry both 👍（the valuable primary content is durable）and
  a reply naming what was not materialized。Exact prose is presentation detail；the response must state what was saved and
  whether anything will be retried。Updates without a message destination remain Job diagnostics only。
- Fetch up to 100 `message` updates。A full page continues from the newly committed cursor；a shorter page ends the Job。
  Edited messages、channel posts and other update families remain outside MVP。
- Materialization classification uses detected bytes，then Telegram declared MIME，filename extension，Telegram attachment
  kind and finally `core.file.v1`。Caption is an independent text/HTML Block；filename is exposed by the metadata Resolver。
- A file that the current Bot API deterministically refuses to expose，including one beyond its standard download limit，is
  materialization-unavailable rather than an unsupported attachment。Its metadata/caption remain durable and retrievable；
  automatic materialization reports a partial outcome，while explicit materialization reports its own failure。Transient
  provider failure has the same separation from the already accepted primary collection and can be retried explicitly。
- The current PostgreSQL writable Storage participates in the caller-owned transaction。A future external writable Storage
  may leave unreferenced bytes after graph failure，but such cleanup residue cannot advance cursor or reshape the normal
  completion result。

## Recovered implementation evidence

The repository already contains an early `extensions/telegram` implementation and a published `0.1.0` Extension package。
It is requirement and failure evidence，not the target design：

- polling and webhook paths both exist，but `collect_method` does not control execution；
- text/caption are wrapped in `extensions.telegram.message.v1` JSON；sender、chat and forward origin are discarded；
- media is reduced to a type label and actual bytes are not retained；
- polling advances `last_update_id` before graph commit，so a persistence failure can lose updates；
- an empty bot token silently completes；
- the webhook inherits Core Peer authentication and therefore is not directly callable by Telegram；making it public
  without Extension-owned admission would instead expose an untrusted graph-write path；
- no Telegram acknowledgement tells the sender whether accepted content was durably saved。

The published boundary also means compatibility is asymmetric：the old exact message decoder stays readable，while legacy
Source rows cannot silently become ready because they lack both the new exact sender binding and a bot-scoped cursor。The
operator creates a new Source under the accepted config；confirmed/lost Telegram updates cannot be reconstructed by a schema
migration。

The existing generic mechanisms already cover the likely MVP foundations：typed Source collect Jobs and optional
user-configured global Cron，
Source state，caller-owned graph persistence，writable Storage selection，nine semantic content Resolvers and ordinary
retrieval over their projections。No generic Resolver or Source framework change is currently justified。

The Telegram unit neither creates nor recommends a schedule as part of the MVP Source contract。Users independently choose
manual collection or configure global Cron frequency；resulting collection latency is therefore deployment configuration，
not Telegram Source behavior or acceptance authority。

The existing schema-driven client-web Source form can submit the exact Telegram config，so this operator-configured MVP does
not require direct API use or a new Web contribution。Discovering the numeric Telegram user ID remains explicit setup cost，
accepted here to keep pairing workflow and UI outside the first delivery。

Telegram's Bot API confirms that long polling and webhook delivery are mutually exclusive and that `getUpdates(offset)`
confirms older updates。Therefore the accepted cursor must advance only after the corresponding primary graph effect is
durable。D-427 freezes bounded polling through the ordinary Source Job path because it avoids a new public callback lifecycle。

## Implementation-plan probe evidence

The probe tested whether the accepted model fits current production seams without promoting a plan：

- `python-telegram-bot` is already locked at `22.8` and directly supplies bounded `Bot.get_updates()`、`Bot.get_file()` and
  `Bot.set_message_reaction()` behavior。The unit does not need a process-lifetime `Application`、a second bot framework or a
  hand-written HTTP client。
- Source instance config and state already have the required variation grains。`download_attachments` belongs only to Source
  config；there is no demonstrated need for a collect-Job override、Extension default or new scheduler parameter。
- One extension-owned database transaction can lock the live Source row，recheck `last_update_id`，ensure its lazy
  `core.source.v1` anchor and persist all primary Blocks/Relations plus state。No generic Source Manager transaction API or
  info-base atomic-graph abstraction is required。
- Mail and RSS already expose production extension-owned remote-content materialization commands。Telegram can use the same
  deep boundary：one protocol metadata Resolver、one idempotent materialization operation and one existing core semantic
  `content` child。It does not justify a generic remote-attachment Resolver or capability framework。
- Ordinary Block reads、Organization and lexical/semantic projection may request Resolver output with
  `materialize_missing=True`。Telegram attachment text/label/solved projection must therefore remain metadata-only even under
  that flag；network I/O occurs only through the explicit extension command or Source collection when
  `download_attachments=true`。This follows the RSS enclosure boundary rather than Mail's solve-triggered MIME fetch。
- Existing Job state can carry bounded per-update and enrichment diagnostics，while Job terminal status continues to report
  command-level completion。Reaction、reply and attachment enrichment remain lower-value post-primary effects and need no
  generic Job lifecycle change。
- The likely implementation authority remains inside `extensions/telegram`：schema、Source collection/persistence、exact
  Resolvers、extension route/lifecycle and operator documentation。Current evidence does not require a migration、Core API、
  client-web contribution or shared durable-doc mutation。Exact file decomposition remains preflight work，not an accepted
  architecture layer。
- There is no admitted Telegram automated regression suite today。Acceptance remains real-bot plus scripted/manual and
  deterministic doubles；adding recurring automated tests still requires the task's separate Human approval rather than
  being smuggled in by the implementation probe。

## MVP non-goals

- Telegram history import、general chat/channel synchronization or a complete Telegram client；
- exhaustive preservation of Telegram users、chats、forward origins、entities、replies、edits or deletion history；
- a generic bot/source、message-envelope or media-ingestion framework；
- collection-time OCR、ASR、summarization or other Organization behavior；
- both polling and webhook transports in the first delivery；
- joining、observing or synchronizing Telegram chats/groups/channels，open-inbox admission，and more than one bound Telegram
  sender per Source；
- a core terminal-user、tenant or per-user ownership/ACL domain；
- specialized Telegram presentation when ordinary info-base browsing and retrieval suffice。

## Common-pattern candidates for peer reconciliation

**Collection should preserve use-relevant semantic information，not maximize source-object reconstruction.** A source-native
transport object does not automatically deserve a canonical Block or Resolver。Persist its semantic content directly through
existing generic contracts；retain source-specific metadata or an envelope Block only when it independently supports
identity、provenance、association、lifecycle or later interpretation required by the accepted user journey。

This candidate sharpens the existing metadata/semantic-content boundary but is not task-wide authority yet。The unit will
reconcile implementation and acceptance evidence directly with any affected peer before promotion into the pressure ledger、
decision register or durable Product TDD。

The attachment behavior adds a more precise instance of that pattern：**collection completeness is defined by the configured
primary information contract，not by optional enrichment。** A durable source locator plus useful metadata can be a complete
collection result；downloaded bytes、full text、OCR or other enrichments attach as separately retryable semantic children。
Positive acknowledgement therefore means the configured primary contract is durable，while an enrichment failure is
qualified without rolling back or replaying that primary fact。

A second unit-local candidate follows the same marginal-utility rule：**externally owned configuration exclusivity should be
guidance rather than a runtime invariant when enforcement requires cross-owner coordination and violation remains visible and
operator-recoverable.** This does not weaken cheap local invariants such as config validation、same-Source cursor locking or
checking a pinned bot identity。

## Missing evidence and peer placement

- This peer is registered in the parallel roster with D-421–D-460。It must create the recorded isolated implementation
  worktrees/bases before source execution and directly notify any peer whose active surface or baseline intersects。
- Runtime acceptance needs a real bot、ordinary Source Job、committed graph、bot acknowledgement and retrieval journey。
  Current lint/type shape checks do not provide that evidence。
