# Mail Extension Implementation Plan

## Execution Status — 2026-08-11

- Slices 0–6 are implemented and accepted。Global Job/Cron、Source anchor/writable-Storage policy、protocol-neutral IMAP
  Mail collection/reconciliation、exact MIME materialization Peer capability、generic InfoBase routes/popups and the Mail
  remote have passed their full static/type/build repositories gates。
- A disposable PostgreSQL baseline passed fresh head upgrade、head→previous→head and DB-owned Job lifecycle timestamp
  checks。The published migration digest is
  `8eda54520a7099c957ee6a1b5e6e48d5ee2b3dbe18b0dea4b6a5246dbef04bd2`。A full downgrade through the oldest historical
  revision still exposes that revision's pre-existing enum-cleanup defect；the accepted unpublished-schema gate remains fresh
  baseline plus head↔previous rather than expanding this unit into historical migration repair。
- The repeatable blocking harness starts a real Dovecot 2.4.4 built under WorkSSD，installs only acceptance-owned `.eml`
  artifacts through IMAP APPEND and passes J1–J3 through production Source/Job/InfoBase/Resolver/Storage paths。
- J4 passes with the graph produced by J1–J3 through built client-web、built Mail remote、PostgREST、core-py Peer HTTP and a
  real browser。It exposed and fixed an iframe browsing-context history bug rather than weakening the literal-back contract。
- Slice 7 code/local-doc cleanup is complete；Hub shared truth is applied in the Hub source worktree but remains uncommitted
  and unpublished pending explicit owner-separated authorization。

- **Status**: R5 execution complete；J1–J4 accepted；owner-separated delivery pending。
- **Authority**: D-201–D-315、the frozen technical-design files in this unit and the four blocking journeys in
  [Acceptance](acceptance.md)。
- **Delivery shape**: retain the `mail-extension` identity and replace its PoC behavior。This is one implementable unit，not
  a release unit；cross-cutting Source、Job/Cron、Storage、Peer and InfoBase changes remain in scope only where the Mail
  vertical has already proved their need。

## Derived Seams Exposed By Preflight

### Exact remote MIME materialization capability

client-web cannot open an IMAP socket，and the accepted Peer architecture removed `Client(rest_api_url).request()`。The only
non-duplicative path from `SolvedContentRenderer` to the Resolver-owned remote materialization command is therefore one exact
request-response Peer capability：

```text
client-web MailMimePartResolver
  -> PeerManager.delegate("extensions.mail.mime_part.materialize.v1")
  -> POST /mail/mime-parts/materialize on one live provider Peer
  -> provider-local MailMimePartResolver.get_solved_content(materialize_missing=true)
  -> content Block + Relation committed
  -> caller resolves the returned child Block through its own database/Storage peer
```

- Request body carries only the MIME-part metadata `BlockRef`。
- Success returns the resulting semantic child `BlockModel`，not bytes and not `created/existing` mechanics。The caller then
  solves that Block locally，including PostgreSQL binary hydration through PostgREST。
- The provider inbound calls a non-delegating local path，so recursion is impossible。
- This is not generic Resolver delegation、`/capabilities/{id}/invoke` or a Job。It is one Mail-owned exact command whose
  need is already observable in J3/J4。
- `ExtensionBase` gains one minimal declarative Peer-inbound hook。`ExtensionManager` registers/unregisters those inbounds
  with extension start/close and republishes the current Peer capability snapshot after the matching routes have changed。
  No separate registry service or extension lifecycle is introduced。

### IMAP implementation boundary

- Use `IMAPClient` 3.1.x over the standard-library email parser。It already owns UID operation、SELECT response、recursive
  BODYSTRUCTURE、ENVELOPE/FETCH parsing、ENABLE and CONDSTORE modifiers。
- Keep the synchronous client behind one fresh async-context `IMAPAdapter` per domain command。Blocking calls run outside the
  event loop and remain serialized per adapter instance；Job cancellation is best effort under D-306。
- QRESYNC SELECT is a narrow adapter-internal extension because IMAPClient has no public QRESYNC selector。It may use the
  pinned library's low-level command/response seam，but it must continue to use IMAPClient/imaplib parsing rather than
  implementing an IMAP wire parser。The Dovecot J1 journey proves this seam black-box。
- If the server advertises no QRESYNC，the adapter follows the already frozen CONDSTORE then new-occurrence-only degradation；
  capability absence is not parser failure or guessed deletion evidence。

## Implementation Slices

### Slice 0 — Restore the already implemented client-web peer/content baseline

1. Selectively transplant `93090d2`、`c25b0c7` and `3d95b03` from `feat/synchronized-core-v3` onto the current
   `feat/organization-git-workflow-phase-6` branch。
2. Preserve the current governance commits and current `docs/_shared` reference；do not transplant `41137d5` or remove the
   completed governance packet。
3. Verify PostgreSQL binary CRUD/hydration、exact semantic Resolvers、Peer HTTP delegation and removal of legacy Client HTTP
   execution before adding Mail changes。

### Slice 1 — Evolve the shared PostgreSQL contract

1. Append a reviewed Alembic revision to the retained chain；do not squash the baseline。
2. Add `storage_types.writable` and the D-290 constraint-trigger closure for nullable `sources.storage -> storages.id`
   (`RESTRICT`)。Registry bootstrap derives writable from the concrete Storage class once。
3. Add database-owned `sources.created_at` / `updated_at`、nullable unique `sources.block -> blocks.id` and nullable
   `sources.storage`；remove `sources.collect_at` and its process-timezone representation。
4. Extend `sources_types` with independently generated ordinary-collect and nullable backfill parameter schemas。
5. Replace `sources_collect_jobs` with:
   - `job_types(id, description, parameters_schema, default_timeout_seconds)`；
   - `jobs(id int8, type, parameters, state, timeout_seconds, status, created_at, started_at, closed_at)`；
   - `crons(id int8, schedule, enabled, job_type, job_parameters, job_timeout_seconds, last_job,
     last_scheduled_for, created_at, updated_at)`。
6. Preserve creator direction：Cron references its last Job；Job has no Cron provenance。Use positive-timeout checks、terminal
   status/timestamp checks and ordinary FKs，without a retry/attempt table。
7. Register `core.source.v1` and project the Source deployment config `core.source / core.source.config.v1` with
   `default_storage=-4`。Register `core.cron` timezone config with UTC fallback。
8. Update the database contract profile/catalog/readiness、migration integrity manifest、PostgREST schema artifact and
   synchronized client-web generated database types in the same schema wave。

### Slice 2 — Build deep Source、Job and Cron runtimes in both peers

1. Replace `SourceCollectJobManager` with a global `JobManager` whose local Handler Registry owns exact parameter validation、
   `can_handle`、async handling and default timeout projection。Claim remains a single conditional
   `pending -> running` update after validation/eligibility；close and timeout recovery conditionally affect only `running`。
2. Register separate `core.source.collect.v1` and `core.source.backfill.v1` handlers。They resolve the Source row/type，then
   validate command config through that Source class；backfill eligibility requires an explicit implementation。
3. Refactor `SourceBase`/`SourceManager` so setup、ordinary collect and optional backfill schemas are independent。Remove the
   obsolete `_organize` obligation and legacy cached schedule setup。Existing RSS/Memos/Twitter/GitHub/Telegram Sources are
   mechanically migrated to the new ordinary command without changing their closed product behavior。
4. Add `SourceManager.ensure_block(source, session)` and `core.source.v1`；the locked Source row creates/reuses one lazy
   anchor and refreshes only the `{id,type,nickname}` projection in the caller transaction。
5. Add Python `CronManager.check()`：application code evaluates the current deployment-timezone minute；a locked Cron row
   compares `last_scheduled_for` and terminality of `last_job`，then creates one Job and advances both fields atomically。
   Missed minutes remain missed and run-now bypasses Cron progress。
6. APScheduler remains only a local wake-up timer for `CronManager.check()` / `JobManager.check()` and unrelated existing
   maintenance。It no longer interprets persisted per-Source schedules。
7. Add equivalent `JobManager`、handler registration、Source runtime registry and conditional claim/close/timeout paths to
   `@inkcre/core`。An open client-web starts/stops its worker with application lifecycle；Mail registers no browser Source
   implementation，so the browser never claims IMAP Jobs。
8. Replace source-specific client models/views with generic Job/Cron models and schema-driven Source collect/backfill forms。
   A Source view may present Crons whose typed template references that Source，but Source persistence does not own or point
   to them。

### Slice 3 — Rewrite Mail collection around one protocol-neutral adapter

1. Delete the PoC Newsletter Source/Resolver and `/mail/imap` / `/mail/newsletter` creation shortcuts。Retain one Source type
   `extensions.mail.source.Source` created through the generic shared-database Source surface。
2. Add canonical Mail schemas and exact Resolvers:
   - `extensions.mail.email.v1`；
   - `extensions.mail.mailbox.v1`；
   - `extensions.mail.email_address.v1`；
   - `extensions.mail.flag.v1`；
   - `extensions.mail.mime_part.v1`。
3. Add `MailProtocol = Literal["imap"]`、typed IMAP parameters and the shallow
   `create_mail_adapter(protocol, parameters)` factory。Both Mail Source and remote-I/O MIME Resolver open their own fresh
   adapter context；neither calls the other。
4. Adapter outputs protocol-neutral mailbox、message/header、participant、MIME-tree、flag、change/removal and exact-part
   facts plus typed next-checkpoint proposals。It owns protocol capabilities/checkpoint interpretation but no Source state、
   Block/Relation/GraphForm、Storage or transaction。
5. Implement source-owned reconciliation in one linear utility-assisted path:
   exact local locator -> comparable cross-Source locator -> scoped EMAILID -> Message-ID -> create；every rung is
   `zero continue / one reuse / many stop-and-create`，with null completion and non-null contradiction rules unchanged。
6. Persist the accepted graph in bounded per-occurrence transactions：Source anchor `manages` Mailbox；Mailbox `contains`
   Email with UIDVALIDITY/UID；independent text/HTML Blocks；MIME metadata；EmailAddress occurrences；reply/reference anchors；
   Mailbox-owned MailFlags and plain `tags`。
7. Ordinary collect uses Source creation time only for the first horizon，then QRESYNC -> CONDSTORE -> new-only checkpoints。
   It advances a Mailbox checkpoint only across accepted graph facts，merges state without overwriting newer progress and
   performs configured Seen mutation after commit。Backfill uses an exact date range and never reads/writes ordinary
   checkpoints。
8. Materialize a null Source exclusion policy once from current extension defaults；later extension changes do not mutate the
   Source snapshot。Persist/validate the non-secret access binding before Mail graph effects and reject silent rebind。

### Slice 4 — Complete Resolver-owned MIME materialization and Peer delivery

1. Add `InfoBaseManager.get_related_block(...) -> BlockModel | None` as the non-stable singular graph read frozen by D-291。
2. Make the Resolver base docstring explicit：solving returns semantic completion，not created/reused/raced mechanics。
3. Implement `MailMimePartResolver` existing-child short circuit；only absence derives owner Email、eligible exact occurrence、
   live Source binding and effective writable Storage。
4. Fetch/decode the exact `part_id` through `IMAPAdapter`，classify by declared media type -> byte signature ->
   `core.file.v1` fallback，then lock/recheck and atomically write PostgreSQL bytes、semantic child and `content` Relation。
5. Register/unregister the exact Peer inbound with Mail extension lifecycle。The client-web Resolver delegates only when its
   local graph has no child and `materializeMissing` permits creation，then resolves the returned child locally。

### Slice 5 — Realize Mail through the generic client-web InfoBase UI

1. Rename resolver rendering to `SolvedContentRenderer` and pass the complete exact Resolver plus solved content。Move
   generic persistence/rumination facts into `BlockInspector`；remove its unused relations prop and embedded solved content。
2. Add the `InfoBaseRoute` contract and singleton-bound `InfoBaseRouter(current, push, back)` to `@inkcre/core`。client-web
   implements it with Vue Router/browser history and the accepted three GraphSurface URLs。
3. GraphSurface becomes the route realizer and removes local selected-Block authority。Its outlet mounts
   `BlockInspectorPopup` or `SolvedContentPopup`，each owning Block load/missing/error and literal-back close；the solved popup
   additionally owns Resolver generation guards、refresh and disposal。
4. Add the client-web Mail extension package/remote。Its Resolvers assemble `SolvedEmail`/`SolvedMimePart` from graph facts；
   its Email renderer presents bodies、participants、Mailboxes/flags、references and MIME actions，with all cross-Block
   navigation routed through `InfoBaseRouter`。
5. Sanitize authored Email HTML with DOMPurify，strip passive remote-fetch surfaces and style URL authority，rewrite only
   already-materialized CID parts to owned object URLs，and render inside a sandboxed iframe without script/form/same-origin
   capability。Only normalized user-initiated HTTP(S) navigation remains active。

### Slice 6 — Prove the four accepted journeys

1. Replace PoC Mail helper/schema tests with `tests/extensions/mail/acceptance/` and a small acceptance-owned `.eml` corpus；
   corpus content remains useful professional reading and production code contains no fixture aliases/IDs。
2. Run a temporary real Dovecot instance on loopback，install the corpus only through IMAP APPEND，and exercise production
   Adapter/Source/Job/InfoBase/Resolver/Storage paths for J1–J3。
3. Run client-web Playwright against the database produced by J1–J3 and the built Mail remote for J4，including route
   history、target navigation、explicit materialization、script isolation and zero passive remote-resource requests。
4. Keep the optional provider smoke environment-gated and diagnostic。Do not add the explicitly deferred negative-path suite
   or a test-only browser Source handler。

### Slice 7 — Close ownership and remove obsolete surfaces

1. Remove `CollectAt`、`sources_collect_jobs` models/routes/components、legacy Client execution remnants、PoC Mail schemas/
   parsers and schema/helper-only Mail tests。No compatibility aliases or dual persistence remain。
2. Update core-py Unit TDD/deployment/security docs and client-web local architecture from implemented truth。
3. Promote stable business and cross-unit technical truths through the Hub shared-doc workflow，then update each Spoke's
   shared reference separately。Do not mix Hub docs、shared-ref bumps and code/local-doc commits。
4. Reset disposable local/preview/production application data only through the D-195 guarded workflow when required；take
   the authorized external WorkSSD dump/digest and Neon recovery branch before production reset。

## Verification Ladder

1. Static boundaries：Ruff/format/Pyrefly，TypeScript/Vue type-check，JSON/Pydantic/Zod schema checks，migration metadata and
   generated database contract drift。
2. Focused implementation checks：Job claim/close algorithms、Cron current-minute materialization、Source-anchor transaction、
   Resolver singular relation query and extension inbound lifecycle。These prove deep common seams，not Mail negative paths。
3. Core black box：J1–J3 against real Dovecot and a disposable PostgreSQL baseline。
4. Browser black box：J4 with built client-web + Mail remote + PostgREST + core-py Peer。
5. Repository gates：full `pdm run check` and client-web `pnpm check` after all vertical journeys pass。
