# RSS Extension Hardening Implementation Plan

## Control

- **Status**: implemented and verified；Sir authorized implementation on 2026-08-02，and B0–B8 completed the same
  day。Durable owner projections followed verified implementation；commit、push、Hub publication、shared-ref bump
  and production migration remain separate gates。
- **Unit**: `rss-extension-hardening`，including the accepted horizontal core/storage/resolver and Memos propagation
  required by the RSS vertical。
- **Inputs**: D-049–D-076 and the accepted
  [semantic-content resolver contracts](semantic-content-resolver-contracts.md)。
- **Validation evidence**: this plan was written first，then its addresses、dependency order、migration branches and
  runtime assumptions were replayed in the plan-specific
  [preflight report](implementation-preflight.md)。Preflight may reject or revise this plan，but is not an input that
  invents its steps。
- **Start gate**: satisfied；each batch still receives its repository-specific Impact Handshake before mutation。
- **Durable gate**: unresolved discussion pressure stays in the packet；verified stable contracts are projected to
  their durable owners during unit completion。Hub publication、shared-ref bump、commit/push and production migration
  remain independent operations。

## Outcome And Completion Boundary

The unit is complete when one configured RSS 2.0 or Atom source can travel through the real public path：

```text
source schedule/manual command
  -> traceable collect job
  -> bounded HTTP fetch + feedparser adapter
  -> exact feed/item reconciliation
  -> committed feed/item/enclosure graph
  -> resolver-instance use projection
  -> deterministic source state advance
  -> optional full-text and enclosure materialization
```

At the same time，the nine common semantic content resolver contracts work in core-py and client-web，PostgreSQL
binary storage is a complete peer-local CRUD capability，Memos attachments use metadata → semantic content → storage，
and no current producer emits retired bare resolver or content-specific HTTP storage IDs。

This plan does **not** deliver a feed-reader UI、OPML、S3、organization child expansion、OCR/STT、semantic retrieval or
production deployment。

## Dependency Topology

```text
B0 freeze contracts / baselines
 ├─> B1 database protocol + storage + hydration ─┐
 └─> B2 resolver base + exact registry/bootstrap ├─> B3 nine semantic resolvers
                                                  │     ├─> B4 Memos attachment v2
                                                  │     ├─> B5 existing producer cut-over
                                                  │     └─> B6 RSS primary collection
                                                  │              └─> B7 enrichment/materialization
                                                  └────────────────────> B8 integrated acceptance
```

No batch is a publication or commit boundary。An edit pass inside B1/B2 may temporarily make the worktree non-green，
but every batch must end green before its dependent batch starts；B2 therefore updates all concrete resolver classes
before completion，rather than deferring breakage to B3。B4–B7 are separately verifiable verticals and must not be
merged into one debugging pass。

## Plan-wide Invariants

1. `block.content` remains actual inline content or an opaque storage pointer；hydrated content never overwrites it。
2. A configured storage returns actual bytes and never decides image/video/HTML/PDF semantics；inline block content
   may already be a Unicode string without passing through storage。
3. Resolver capability execution occurs on a resolver instance；Manager owns exact registration/selection and shared
   matching helpers only。
4. Protocol/source-authored facts remain on metadata/root blocks；byte-derived facts remain solved projections unless
   a separately justified organization command materializes them。
5. `refresh` replaces a local snapshot；`materialize_missing` permits an absent derivation；neither is a synonym for
   recompute、redownload or `force`。
6. Existing user-authored/unrelated worktree changes are preserved。Cross-repo edits are reviewed and verified in
   their owning repository。
7. Implementation and tests use disposable PostgreSQL/Neon-compatible databases。Canonical production remains
   read-only evidence until a separately authorized delivery/migration operation。
8. Runtime compatibility is explicit：Memos v1 receives the accepted one-time migration；retired bare core IDs do not
   receive aliases、decoders or row migration。

## Frozen Interfaces Used By The Plan

### Core-py block and resolver surface

```python
class BlockModel:
  async def get_hydrated_content(self, *, refresh: bool = False) -> str | bytes: ...


class Resolver(ABC, Generic[SolvedT]):
  async def get_solved_content(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> SolvedT: ...

  @abstractmethod
  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None: ...

  @abstractmethod
  async def get_str_for_embedding(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None: ...
```

- `UnsupportedResolverCapability` means the resolver contract does not provide the requested projection。
- `UnknownResolverError` means no exact decoder is installed/registered for the block's resolver ID。
- `None` means the capability exists but this block has no meaningful result。
- Hydration caches `(storage, content) -> hydrated value` in Pydantic private state。A changed pointer/key misses the cache
  naturally；`refresh=True` bypasses and replaces it。No ORM event hook or cross-instance invalidation is added。
- Resolver solved/relation caches follow the same `refresh` spelling。The old raw-content cache disappears；resolver
  hydration delegates to its block。
- `ResolverManager.match_media_type()` normalizes a candidate media type and returns an exact registered semantic
  resolver ID or `None`。Extensions still own evidence order and fallback policy；`core.file.v1` is selected by the
  extension only after its own ladder fails。

### Client-web peer projection

```ts
abstract class Resolver<RawT, SolvedT> {
  abstract getText(options?: ProjectionOptions): Promise<string | null>
  abstract getStrForEmbedding(options?: ProjectionOptions): Promise<string | null>
}

type ProjectionOptions = {
  refresh?: boolean
  materializeMissing?: boolean
}
```

- `Block.getHydratedContent({ refresh })` returns inline `string` or storage-backed `ArrayBuffer`/`Uint8Array`。
- Browser `Blob`、Object URL and renderer handles are private runtime state，revoked on refresh/dispose/cache eviction。
- Unknown exact resolver and unsupported capability are different typed errors；there is no default resolver fallback。
- Parser-derived solved fields may remain `null` when the browser peer lacks a proportionate local parser。Open/render/
  download remains a real local capability rather than a call to core-py。

### Shared relation vocabulary introduced by this unit

| From | Relation content | To | Meaning |
| --- | --- | --- | --- |
| feed item | `feed` | feed | exact feed membership and identity scope；not deletion ownership |
| feed item | `enclosure` | enclosure metadata | unordered native enclosure component |
| feed item | `full_text` | `core.text.v1` | optional fetched main-text enrichment |
| enclosure metadata | `content` | semantic content | downloaded bytes interpreted by an exact core resolver |
| Memos attachment metadata | `content` | semantic content | uploaded bytes interpreted by an exact core resolver |

RSS enclosure order is not promoted because no current use requires it。Memos keeps its already accepted ordered
`attachment:<order>` owner relation。

## B0 — Freeze Working Baseline And Contract Cases

### Changes

- Pin the selected dependency ranges in the root and RSS extension manifests before implementation：Pillow、PyAV、
  pypdf、puremagic、feedparser and Trafilatura；regenerate the owning PDM locks through PDM。
- Add an exact resolver-ID/type case table consumed by core registration/matching tests and static retired-ID checks。
- Record licensed provenance for repository-generated real-format acceptance samples（image、audio、video、PDF、
  EPUB、ZIP）without committing derived outputs。
- Capture current green commands and the existing dirty-worktree boundary in the packet；do not stage unrelated files。

### Primary addresses

- core-py：`pyproject.toml`、`pdm.lock`、`extensions/rss/pyproject.toml`、`extensions/rss/pdm.lock`
- tests：`tests/assets/semantic-content/` source manifest/generator、ignored generated real-format files and shared
  on-demand pytest fixture
- client-web：no parser dependency is added merely to make nullable solved facts non-null。

### Verification

- `pdm run check:lock`
- import probe for each selected direct dependency under Python 3.12
- container build/import probe proving PyAV's selected wheel works in the production Python image
- license/source manifest contains no copied sample with unknown redistribution status

### Execution evidence — complete 2026-08-02

- Root and RSS locks resolved with prior pins reused where compatible；the selected exact versions are Pillow 12.3.0、
  PyAV 18.0.0、pypdf 6.14.2、puremagic 2.2.0、feedparser 6.0.14 and Trafilatura 2.2.0。
- Repository-generated、Git-ignored real-format assets cover the nine-ID case table with no third-party payload
  provenance；the shared pytest fixture rebuilds them from a clean checkout。
- Local Python 3.12 and the production `python:3.12-slim` Dockerfile both imported every selected direct dependency。
- New B0 code/task-plan surfaces pass targeted Ruff lint/format and lock checks；the repository-wide formatter reports
  unrelated pre-existing Markdown/Memos-test drift recorded in the unit packet。

## B1 — Database Protocol、Storage Mechanics And Block Hydration

### State diff

```text
content-kind HTTP storages + C/R/D writable storage + resolver-owned raw cache
  -> one bytes-only HTTP storage + C/R/U/D writable storage + block-owned hydration cache
```

### Core-py changes

1. Make `HTTPStorage` the concrete `http` bytes handler；remove semantic subclasses from current exports/registration。
   Built-in `-1` becomes the generic HTTP instance。Its config owns timeout/redirect/maximum-response-byte mechanics
   only，and its chunked HTTP read enforces the byte limit without creating a streaming storage contract。Retired
   `-2/-3` records may remain historical database rows but no current code emits them。
2. Add `WritableStorage.update_raw_content()` and implement pointer-stable PostgreSQL byte replacement。
3. Add `BlockModel.get_hydrated_content(refresh=False)` with private value+source-key cache；move resolver hydration to
   that method and remove `real/raw` ambiguity from current code/docstrings。
4. Change `blocks.storage -> storages.id` deletion to `RESTRICT` in SQLModel metadata and an append-only Alembic
   revision after `f2c8a6d1e4b7`。
5. Add admitted `inkcre.create_storage_blob(bytea) -> uuid` and
   `inkcre.read_storage_blob(uuid) -> bytea` functions for raw PostgREST transport。They are invoker-rights functions；
   role reconciliation grants only the normal authenticated peer surface。
6. Extend the core protocol document with function signatures and ensure `storage_blobs` remains bytes-only。

### Client-web changes

1. Extend database-contract generation for `Functions` instead of hand-editing `generated.ts`。
2. Add a narrow authenticated raw PostgREST fetch utility adjacent to `DBAPIClient`；it reuses the current dynamic JWT
   and origin config but returns `ArrayBuffer` for octet-stream calls。
3. Implement PostgreSQL binary create/read/update/delete：raw RPC create/read，exact UUID `bytea` PATCH update and
   exact UUID delete。Centralize `{"blob_id":"..."}` pointer parsing/serialization。
4. Move hydration to `Block.getHydratedContent()` and make the private cache non-enumerable/non-transported。

### Primary addresses

- core-py：`app/schemas/info_base/block.py`、`app/business/info_base/storage/{main,http,postgresql,__init__}.py`、
  `app/database_contract/{profile,protocol,roles}.py`、new migrations、migration integrity/tests
- client-web：`packages/core/src/{base/db-api,info-base/block,info-base/storages/*,database/*}`、
  `scripts/database-contract-lib.mjs`、generated contract artifacts、peer-database E2E

### Acceptance

- PostgreSQL bytes survive create → hydrate → same-pointer update → refresh → delete byte-exactly。
- Default hydration reuses its instance snapshot；refresh observes the updated blob；a second block instance is not
  promised invalidation。
- Missing blob/storage handler is explicit；deleting a referenced storage catalog row is RESTRICTed。
- Storage CRUD never queries or rewrites blocks and never owns MIME/filename/semantic facts。

### Execution evidence — complete 2026-08-02

- Both peer implementations now own block-instance hydration and generic HTTP/PostgreSQL byte mechanics；the complete
  client-web check proves the storage hard cut does not leave application imports or distribution output broken。
- Disposable PostgreSQL/PostgREST reached exact v2 readiness at `d0e3f4a5b6c7`，then passed authenticated raw
  C/R/U/D with byte-exact reads before and after pointer-stable update。
- Runtime replay rejected two plausible-but-wrong initial assumptions and fixed them append-only：the existing trigger
  helper was an internal function leaked into the exposed schema，and PostgREST 14 requires an explicit media-type
  domain for raw `bytea` responses。Readiness now checks function signatures as well as names/ACLs so the second defect
  cannot hide behind a green catalog projection。
- Verification：core-py `check:migrations`、typecheck、266 passed/6 skipped；client-web full `pnpm check`、47 tests and
  all builds。The client delivery pin remains unchanged until the B8 artifact-ordering step。

## B2 — Resolver Base、Exact Registry And Bootstrap

### Changes

1. Introduce shared Python/TypeScript error、options and exact core resolver-ID types。
2. Keep Python and make TypeScript resolver bases abstract for text/embedding methods；update every current concrete
   resolver in both repositories in the same batch so missing capability declarations are statically/runtime visible。
3. Add exact duplicate-registration checks and explicit unknown-ID errors；re-registering the same class is idempotent，
   while a different class claiming the same ID fails。Remove client-web's first/default resolver fallback。
4. Replace `force` with `refresh` on InKCre-owned resolver/relation/cache calls；keep third-party protocol parameters
   unchanged。
5. Add explicit `register_core_resolvers()` bootstrap before extension loading and outside `SKIP_EXTENSIONS_SYNC`。
   Core resolver availability no longer depends on importing an arbitrary extension package。
6. Make embedding/context consumers skip supported-null and handle unsupported capability explicitly rather than
   embedding `""` or aborting the whole missing-embedding scan。The periodic scanner also records/skips unknown retired
   IDs，while direct application resolution still raises the exact unknown-ID error；this prevents historical hard-cut
   rows from repeatedly failing the whole scheduler job。

### Primary addresses

- core-py：`app/business/info_base/resolver/{main,__init__,bootstrap,contracts}.py`、`run.py`、all concrete extension
  resolvers、`app/business/sink/{embedding,main}.py`、`app/schemas/info_base/block.py`
- client-web：`packages/core/src/info-base/resolvers/{base,cache,contracts,index}.ts`、all extension resolvers and
  resolver call sites

### Acceptance

- An unregistered ID fails as unknown in both peers；retired IDs are not reinterpreted。
- Every concrete resolver explicitly implements both abstract methods。
- unsupported、supported-null and authored-empty are three observable outcomes。
- Application boot with extension sync disabled still resolves all nine core IDs。

## B3 — Nine Semantic Content Resolvers And Peer-local Use

### Core-py changes

- Replace the old text/HTML/image/video implementations and delete the image resolver's import-time AI credential/
  remote side effect。
- Add exact `core.text/html/image/audio/video/pdf/epub/zip/file.v1` modules with the accepted solved shapes。
- Text uses inline Unicode or BOM/strict UTF-8 bytes；HTML additionally honors a bounded in-document charset
  declaration and exposes decoded source plus a derived text projection。
- Pillow reads image format/dimensions/frame count without pixel decode；PyAV selects the first default-disposition
  stream，or otherwise the first non-attached-picture stream of the requested kind，without frame decode；pypdf reads bounded root/page metadata without text extraction；EPUB and
  ZIP inspect only bounded central-directory/package metadata and never extract；puremagic supplies optional bounded
  detected MIME。
- Invalid claimed format is a resolution error；encrypted/protected valid content returns encryption facts and null
  for inaccessible optional facts。
- CPU/native parser inspection runs through bounded worker-thread calls so one Pillow/PyAV/pypdf/ZIP operation does
  not synchronously block the event loop；the parser does not gain an unbounded process/thread pool。
- `core.text.v1` and `core.html.v1` provide text/embedding projection。Image/audio/video/PDF/EPUB/ZIP/file v1 explicitly
  raise `UnsupportedResolverCapability` for those methods until a real caption/transcript/text-extraction capability
  exists；metadata/title facts in solved content are not misrepresented as the file's textual content。

### Client-web changes

- Register all nine exact IDs and provide local safe handles：text/HTML preview，image/audio/video/PDF object URLs or
  native elements，EPUB/ZIP/file open/download。
- Never use `v-html` without a separately admitted sanitizer；the MVP HTML component renders a text preview/source
  action。
- Remove raw `block.content` fallbacks from BlockContent、graph preview and editors；storage-backed blocks never expose
  pointer JSON as authored content。
- Revoke object URLs on refresh、resolver disposal and resolver-cache eviction。

### Acceptance

- Each ID resolves a real sample persisted through PostgreSQL binary storage in core-py。
- Browser peer hydrates and offers a usable local handle for every ID；unsupported parser-derived facts remain null。
- No resolver-specific solved model duplicates storage pointer、source filename or declared MIME authority。
- OCR、STT、PDF text、EPUB chapters and ZIP member graphs remain absent rather than faked。

## B4 — Memos Attachment V2 And One-time Migration

### Changes

1. Append the D-076 reversible data revision：for each exact v1 attachment，validate canonical JSON，extract `blob_id`
   into minimal pointer JSON on a new semantic child selected from normalized Memos MIME，rewrite the same metadata
   block ID to inline v2 content，and create one `content` relation。One migration transaction prevents partial row
   conversion。Downgrade is guarded：it reconstructs v1 for every v2 attachment only when each has exactly one
   exclusive PostgreSQL semantic child with the reversible pointer shape；otherwise it refuses before mutation rather
   than deleting shared or post-upgrade information。
2. Remove `blob_id` from `CanonicalAttachment` v2；add `content_block_id` only to the solved/runtime projection。
3. Rewrite attachment create/list/solve/download/delete to traverse metadata → semantic content through exact
   resolvers。Memos wire 0.29.1 continues to expose the metadata block ID/filename/type/size/create time。
4. Exclusive deletion removes blob + semantic child only when no other metadata block points to it；shared semantic
   content survives。Memo ordered ownership and unattached attachment behavior remain unchanged。

### Primary addresses

- migration + integrity entry
- `extensions/memos/family/{schema,graph,attachment,attachment_resolver,resolver}.py`
- Memos backend attachment adapter/tests and local Unit TDD candidate list（not durable mutation in this batch）

### Acceptance

- Fresh upload、unattached list、attach/reorder、native read/download and deletion traverse the new graph through real
  PostgreSQL bytes。
- Seeded v1 upgrade preserves metadata block ID、blob UUID/bytes and memo slot relations；a guarded downgrade
  round-trips every reversible v2 shape and rejects a non-exclusive/shared shape before mutation。
- A disposable database beginning at the current production head `d9f4e2a1b7c3` proves the empty v1 path through
  repository head；canonical production itself is not migrated by acceptance。

## B5 — Existing Producer/Consumer Hard Cut

### Changes

- Twitter Python collection emits exact core text/HTML/image/video IDs and uses generic HTTP bytes storage。Repair the
  API DTO → canonical root → attachment relation gap exposed by preflight；version the repaired root as
  `extensions.twitter.tweet.v1` and mirror it in the client-web Twitter resolver。
- Keep Twitter attachment source facts relation-owned rather than copying URL arrays into canonical Tweet content。
- Update webext Taking Note and Arcs Editor producers to `core.text.v1` / `core.html.v1` as appropriate；remove the
  unregistered `url` pseudo-resolver。
- Update all current tactical guides/examples and replace `tests/test_resolver_breakdown.py` with behavior that belongs
  to the new resolver/materialization contracts；do not retain the old AI-breakdown prototype as compatibility proof。

### Acceptance

- Twitter collection → graph → TweetResolver regression covers text、photo、video、link and reply without accessing
  dropped DTO fields。
- Repository-wide static scans find no current producer/example emitting bare `text/html/image/video` or
  `http_image/http_video/http_html/http_json/http_text`。
- Direct reads of old IDs fail explicitly in both peers。

## B6 — RSS Primary Collection Rewrite

### Product/graph shape frozen by this plan

- Keep extension ID `rss` and the two durable source type IDs `extensions.rss.rss.Source` and
  `extensions.rss.atom.Source`。Their modules become thin protocol-expectation wrappers over one shared source/service；
  parsing、HTTP、reconciliation and graph logic are not duplicated。
- New exact resolver IDs：`extensions.rss.feed.v1`、`extensions.rss.feed_item.v1` and
  `extensions.rss.enclosure.v1`。
- Canonical feed content owns source instance ID、optional source-native feed ID、declared self URL、configured URL
  and feed-authored title/home/description/language/update facts。The identity ladder derives from those exact facts；
  it is not copied into a second generic identity-value field。
- Canonical item content owns optional source-native ID + kind（Atom ID or scoped RSS GUID），optional alternate link，
  title/summary/feed-authored content、published/updated times、authors and categories。When native ID is absent，the
  alternate link itself is the fallback identity evidence；it is not duplicated into an identity-value field。The
  item excludes source instance ID because its `feed` relation provides the scope，and excludes enclosures/fetched
  full text because graph relations own them。
- Canonical enclosure metadata owns URL、declared media type/length and optional title；download result is graph-only。

### Source config/state

- Config validates non-empty HTTP(S) `feed_url`、timeouts/body limits、`fetch_full_text=True`、
  `download_enclosures=False`、enclosure size limit and target writable storage ID（default PostgreSQL `-4`）before
  effects。The initial bounded defaults are 30 seconds，8 MiB feed body，8 MiB article body and 64 MiB enclosure；
  source config may deliberately raise the byte limits without changing the resolver contract。
- Job config is typed and contains only source-specific supported overrides；legacy generic `full` is rejected rather
  than silently changing reconciliation semantics。
- State owns conditional HTTP ETag/Last-Modified and one last successful contentful snapshot observation time。That
  same timestamp is D-056's next unidentified-item admission watermark；it is not copied into a second state field。
  It does not retain unordered `seen_ids`。

### Collection command sequence

1. A manual request or schedule creates an ordinary PENDING collect job。The scheduler never calls `source.collect`
   directly；a shared `SourceCollectJobManager.create()` seam feeds the existing runner。Pending dispatch uses the
   database job ID as the deterministic scheduler job ID and an atomic claim/status transition，so repeated polling
   cannot run one collect job twice。
2. The source validates config/job config，captures `snapshot_observed_at` when the complete response is received，and
   sends response bytes/effective URL/headers to feedparser in a bounded worker-thread call。
3. Fatal transport、unsupported feed family or unusable feed document fails the job and does not advance source
   state。A parseable `bozo` feed may continue with a diagnostic；one malformed item is skipped with a diagnostic。
4. Feed reconciliation creates/updates the exact feed block。Each valid item primary graph is committed in its own
   transaction：same exact identity updates the existing root，new identity creates，missing old items are untouched。
5. Unidentified items obey create/discard config。Create uses D-056's source-time watermark only as an admission
   filter；it never becomes identity or document-order short-circuit。
6. After every valid primary item has been considered without a primary persistence failure，advance conditional/
   observation state once。Previously committed items may remain after a later primary failure；retry exact
   reconciliation makes that residue safe。
7. Job status is FINISHED when fetch/parse and all admitted primary item writes succeed。Skipped malformed items and
   optional-enrichment failures are structured diagnostics in `job.state`，not silent success；primary failure marks
   FAILED and preserves diagnostics/residue facts。

### Primary addresses

- shared runtime：`app/business/source/{main,collect_job}.py` and source tests
- RSS rewrite：`extensions/rss/{rss,atom,source,http,adapter,schema,repository,resolver,service,__init__}.py`
- replace `tests/extensions/test_rss.py` with black-box suites under `tests/extensions/rss/`

### Acceptance

- Hermetic HTTP double serves actual RSS 2.0 and Atom bytes through real transport into a real PostgreSQL graph。
- Cover create、same-content replay、same-ID update、new item、missing old item、unidentified create/discard/watermark、
  304、malformed item、fatal feed and process retry residue。
- Resolver text prefers feed-authored content in the primary slice；feed/item/enclosure authorities remain separately
  inspectable。
- Scheduled trigger produces one traceable job and follows the same runner/state semantics as manual collection。

## B7 — Default Full-text And Enclosure Materialization

### Full-text enrichment

- After primary item commit，default-on enrichment fetches the item link with the same bounded HTTP policy and passes
  already-downloaded HTML to Trafilatura in a bounded worker-thread call。
- Successful main text is an inline `core.text.v1` block related from the item by `full_text`。No extra metadata block
  is added because the item link already owns the source URL and the enrichment has no independent protocol identity。
- Existing full text is reused for unchanged item/link。An item/link change may replace the relation target in a new
  transaction。Failure records a diagnostic and does not fail primary collection or advance/rollback primary state。
- FeedItemResolver prefers the related full-text block for text/embedding use，then falls back to feed-authored
  content/summary/title；the feed-authored root remains authority and inspectable。

### Enclosure materialization

- `POST /rss/enclosures/materialize` accepts exact enclosure metadata block IDs plus target writable storage ID and
  returns one result per input (`enclosure_id`、existing/new semantic block ID or explicit error)。Each enclosure is an
  independent command transaction，so partial results are observable rather than disguised as all-or-nothing。
- The service obtains the exact enclosure resolver instance，derives a download command，performs bounded HTTP，runs
  the RSS/Atom-specific classification ladder，writes bytes to storage，creates the exact semantic block and one
  `content` relation。
- If a valid existing content relation resolves，manual/automatic materialization returns it idempotently；the MVP has
  no redownload/recompute flag。Concurrent attempts re-check under enclosure-row lock before creating the child。
- Automatic policy invokes the same application service after primary collection。Unavailable storage、download or
  resolver failure becomes an item/job diagnostic and does not erase enclosure metadata or fail primary collection。

### Acceptance

- Manual and automatic paths materialize real image/audio/video/PDF/EPUB/ZIP and unknown file samples through the
  same service，not test-only parser helpers。
- RSS declaration and Atom HTTP/advisory precedence follow D-070–D-072；observed/detected MIME never overwrites metadata。
- Replay/concurrency creates at most one current `content` relation/materialized semantic child per enclosure。
- Failed download leaves the enclosure metadata readable and no success relation；per-input API results expose any
  prior committed siblings。

## Execution Evidence — B2–B7 complete 2026-08-02

- B2/B3：exact resolver registry/bootstrap、typed capability outcomes、nine Python/TypeScript semantic resolvers、
  block-owned hydration and client render/open/disposal paths pass static and real-format acceptance。
- B4/B5：Memos attachment v2 migration/runtime and Twitter/webext exact producer cut-over pass their targeted and real
  PostgreSQL suites；the writable storage seam now returns storage-owned opaque pointer text without exposing
  PostgreSQL pointer grammar to RSS or Memos callers。
- B6：the scheduler and manual route share `SourceCollectJobManager.create()`，pending claims are atomic，and RSS/Atom
  source modules are durable-identity wrappers over one HTTP/parser/reconciliation service。State scopes conditional
  headers to the configured URL and the source-time watermark to an exact persisted feed root，so config/feed identity
  changes cannot reuse unrelated cursors。
- B7：default full text、resolver-preferred use projection、manual API、automatic enclosure policy and concurrent
  idempotency are implemented。The PostgreSQL black box materializes and resolves real image/audio/video/PDF/EPUB/ZIP
  and unknown file bytes；RSS declaration and Atom observed HTTP precedence remain inspectable without rewriting
  enclosure metadata。

## B8 — Integrated Verification And Promotion Preparation

### Core-py verification

- `pdm run check:lock`
- `pdm run check` and the repository's static/type/migration checks
- targeted semantic-content、storage、Memos、Twitter、RSS black-box/integration suites
- fresh database `base -> head` and seeded `f2c8... + Memos v1 -> head -> downgrade` migration journeys
- opt-in live RSS and Atom smoke against replaceable public endpoints；only stable collection invariants are asserted

### Client-web verification

- root `pnpm check`，package/app type-check and targeted Vitest resolver/storage tests
- PostgREST browser E2E for byte-exact PostgreSQL CRUD、JWT denial and missing UUID
- component proof for unknown resolver、unsupported renderer、object URL disposal and pointer non-disclosure

### Cross-repo completion review

- static retired-ID/storage-ID scan in both repositories
- code review of exact diff ownership and generated artifacts
- reconcile task-packet candidates into their Hub/core-py/client-web durable owners after implementation evidence
- no production migration、commit or push without a new explicit instruction

### Execution evidence — complete 2026-08-02

- core-py：Pyrefly zero diagnostics；293 passed/19 environment skips；migration suite 22 passed/2 skipped at
  `e1f4a5b6c7d8`；real PostgreSQL Memos+RSS run 15 passed。Repository lint and implementation-owned Ruff format/
  retired-ID scans are green。The repository-wide formatter retains four unrelated pre-existing Markdown guide
  drifts，recorded rather than silently edited。
- client-web：complete `pnpm check` passed all 56 unit/runtime tests，workspace type checks and production builds。
- live protocol acceptance：replaceable opt-in RSS/Atom tests consume URLs selected through
  `INKCRE_LIVE_RSS_URL` / `INKCRE_LIVE_ATOM_URL`；they skip rather than pinning an external endpoint when none is
  selected。
- delivery boundaries remain unchanged：no production mutation、commit、push or shared-ref bump was performed；
  Hub source and Spoke-local durable owner edits were prepared after Sir clarified the promotion timing。
- durable validation：Hub `git diff --check` + SVC `init` noop；45 relative links resolved；core-py owner docs targeted
  Ruff format and repository lint passed；client-web complete `pnpm check` passed 56 tests、types and builds。

## Implementation Loop Per Batch

For each B1–B7 batch：

1. restate a batch-specific Impact Handshake against the addresses above；
2. make one coherent edit pass，preserving unrelated worktree changes；
3. run static checks before adding tests that merely repeat types；
4. run the smallest black-box/integration scenario that proves the changed behavior；
5. inspect the diff and update this packet with new evidence/branch changes；
6. continue to the dependent batch only when the batch's acceptance is green or a newly exposed design decision has
   returned to Sir。

## Known Stop Conditions

Return to discussion instead of improvising if implementation evidence shows：

- the raw PostgREST byte RPC cannot provide the accepted octet-stream contract without a materially larger server
  extension；
- PyAV's selected wheel cannot run in the production image or metadata inspection requires frame decode；
- an existing Memos v1 row cannot be losslessly mapped to the accepted v2 graph；
- RSS exact reconciliation requires a generic binding table or a new persistent field not approved here；
- client-web needs a server delegation to satisfy a capability that was accepted as peer-local；
- a shortcut would reintroduce semantic storage types、pointer disclosure、silent resolver fallback or duplicate
  authority。
