# Media Resolver And Storage Evidence

## Purpose

记录 RSS enclosure vertical 暴露的横向 current-state evidence。这里不是独立 unit，也不是 durable
owner；confirmed cross-unit contracts 仍由 program decisions 与 later Product TDD promotion 拥有。

## Resolver Evidence

- Core `Resolver` 要求 `get_text()` 与 `get_str_for_embedding()`；runtime introspection 证明现有
  `TextResolver`、`VideoResolver` 仍是 abstract class，不能形成完整 resolver path。
- `ImageResolver` 把 Tencent LKE client/credential construction 放在 module import，且只接受固定
  `http_image` storage ID；stored PostgreSQL/S3 bytes 无法走同一路径。
- `ImageResolver.get_text()` 会执行 remote AI workflow 并直接写 derived blocks/relations；read/resolve 与
  enrichment/organization side effects 没有清晰边界。
- `VideoResolver` 只提供 URL graph factory；没有 solved/text/embedding contract。Audio、PDF、EPUB、ZIP、
  generic file resolver 不存在。
- `HTMLResolver` 把固定 HTTP storage、HTML fetch、text conversion 与已有 text relation fallback 混在一起；
  它不是 RSS full-text extraction 的可信 reference implementation。
- Existing resolver IDs `image` / `video` / `html` / `text` 未 version/namespace；Twitter bookmark source
  直接依赖 image/video/html factories，因此 common media rewrite 需要 Twitter regression proof。

## Storage Evidence

- `HTTPStorage._fetch_url()` 从 `ClientSession` / response context 返回 response object，调用方在 context
  已退出后读取 body；response lifetime ownership 不成立。
- HTTP variants 重复 transport code 并混入 media `Accept` preference；`HTTPJsonStorage` 对任意 decoded
  JSON 调用 `.strip()`，image docstring 声称 base64 但返回 bytes，HTML docstring/return type 也不一致。
- HTTP storage 没有 response-size、streaming、content-type/provenance 或 partial-download contract。
- `WritableStorage.write_raw_content()` 接受完整 `bytes`、是 synchronous、并强制 caller DB session；这能
  支撑 PostgreSQL small blobs，但不能证明 S3/multipart/large enclosure lifecycle。
- Writable storage 返回任意 pointer value，block caller 自行把 pointer 编入 resolver content；没有
  stable pointer envelope/capability contract。
- `blocks.storage` foreign key 当前 `ON DELETE SET NULL`。删除 storage 会让原 pointer string 被 resolver
  当成 inline content，保存 block row 却破坏 raw-content interpretation。
- Storage type/instance tables 与 config schema 已存在，但 core 没有 storage create/update route；若加入
  S3-compatible storage，需要明确 provisioning/config authority。

## Memos Attachment Evidence

- `extensions.memos.attachment.v1` block 同时承担 Memos attachment identity、filename/media-type/size/
  created time 与 PostgreSQL `blob_id` pointer。
- Repository hard-codes built-in storage ID `-4` for create/read/delete；canonical schema 直接依赖 UUID blob
  pointer，不能换 target storage。
- Memo graph、owned deletion、list/download/delete 和 v0.29.1 adapter 都要求 exact attachment resolver。
  直接把 resolver 字符串改成 `image` 会破坏 unattached uploads 与 Memos attachment listing。
- Memos protocol permits upload before memo ownership；therefore attachment role/identity must remain
  recoverable even when no `memo --attachment:<order>--> ...` relation exists。

## Confirmed Product Pressure

- Materialized information uses exact semantic content resolver IDs：image、audio、video、PDF、EPUB、ZIP；
  unknown/unsupported falls back to file with best-effort MIME type。
- RSS enclosure remains source-authored authority；download creates a related local materialization。
- Memos attachment behavior must migrate to the same semantic media/storage path within the RSS unit loop。
- Actual-content bytes remain storage-owned；storage representation never determines block information kind。

## Open Design Branches

1. Parser/runtime dependency，charset-authority and bounded-inspection preflight for D-075's nine exact IDs。
2. Resolver-version/hard-cut-off consequences for existing `extensions.memos.attachment.v1`；the accepted common
   bare-ID cut-off retains neither compatibility decoders nor a migration。

## Closed Design Branch

- D-075 fixes nine exact `core.<kind>.v1` resolver IDs，resolver-instance capability calls，mandatory abstract
  text/embedding methods with explicit unsupported errors，and hard cut-off of bare `text/html/image/video`。
- D-059 keeps a MemosAttachment metadata block and relates it to media/file semantic content；direct media identity was
  rejected because unattached protocol resources，list/delete/download identity and ordered ownership would
  otherwise require hidden provenance/index conventions。
- D-060 keeps one persisted `content` column：inline blocks store actual content there，storage-backed blocks
  store an opaque pointer。`BlockModel.get_hydrated_content()` hides that conditional read and caches actual
  content in non-mapped `_hydrated_content` without replacing the persisted pointer；storage deletion is
  RESTRICT while referenced。
- D-067 closes media metadata authority without adding `blocks.metadata`；protocol/source facts stay on the metadata block，storage
  mechanics stay in pointer/config，semantic and byte-derived facts stay with resolver projection，and useful
  durable derivations may become organization graph enrichment。
- D-068 closes the current S3/streaming scope branch：S3-compatible storage is sequenced with the future Nextcloud
  Files extension；RSS uses PostgreSQL writable storage with explicit bounds and does not add speculative streaming
  abstraction or very-large-file acceptance。
- D-069 closes the global-ladder branch：extensions own classification policy，while core may offer reusable
  `ResolverManager` mechanisms without adding a media module。Memos type，RSS enclosure type and Atom link type keep
  their protocol-specific semantics。
- D-070 closes Memos classification：required normalized `Attachment.type` selects the exact resolver ID，
  unknown MIME falls back to file，and byte sniffing neither gates upload nor replaces the metadata-block declaration。
- D-071 closes RSS classification：valid，specific `enclosure.type` is primary；fallback evidence participates only
  when the declaration is unusable and never rewrites the metadata-block field。
- D-072 closes Atom classification：specific dereferenced HTTP type precedes advisory link type，then adapter-owned
  fallback；no observed/detected result rewrites the metadata-block declaration。
- D-073 corrects the earlier pure-read inference：resolver is the application-facing graph interpretation boundary，
  may lazily materialize missing derived graph through AI/organization，and exposes optional text/embedding
  projections。The missing contract is caller control plus effect correctness，not a universal side-effect ban。
- D-074 makes missing materialization the ordinary resolver default with an explicit read-only override。`refresh`
  only bypasses/replaces a reusable local snapshot；`materialize_missing`，organization `recompute` and cache
  `invalidate` retain orthogonal effects。Existing client-web resolver `force` cache options become migration
  pressure，not durable vocabulary。

## Client-web Cross-runtime Evidence

`client-web/packages/core` independently implements the same domain seam rather than merely consuming generated
database types：

- `src/info-base/block.ts` models the conditional `storage` / string `content` row but has no content-read
  method or hydrated cache。
- `src/info-base/resolvers/base.ts` owns `_rawContent`，branches on `block.storage` and dynamically instantiates a
  browser `Storage` handler。This duplicates the responsibility D-060 moved onto block and preserves the retired
  raw/real terminology。
- `src/info-base/storages/base.ts` and `storages/http.ts` expose `getRawContent(block)` and interpret
  `block.content` as the pointer。The HTTP handlers are browser implementations，not a portable contract for
  PostgreSQL binary or future S3-compatible server-owned storage。
- The canonical topology makes core-py and client-web equal peers over the admitted database protocol；core-py
  schema/migration ownership does not make its REST API the content data plane for other peers。No existing
  core-py storage-backed-content API contract was found。
- The generated client-web database types currently include `storage_types` and `storages` but omit
  `storage_blobs`，while the current core-py executable peer contract admits `storage_blobs`。That is a concrete
  contract-sync/handler prerequisite if client-web must support PostgreSQL binary hydration，not a reason to
  proxy through core-py。
- Resolver-level caching is timestamp-invalidated through `ResolverCache`，but actual-content cache is per
  resolver instance。Multiple resolvers for one `Block` can therefore repeat hydration；moving the cache to
  `Block._hydratedContent` aligns the two runtimes and leaves `ResolverCache` responsible only for resolver
  interpretation/relations。
- `Resolver.getRelations()`、`getRawContent()` and `getSolvedContent()` currently name cache bypass `force`，while
  `ResolverCache.invalidate()` only deletes an entry。This is concrete evidence for distinct `refresh` versus
  `invalidate` vocabulary；it is not evidence for preserving an unqualified `force` boolean。
- Current graph preview and fallback UI render `block.content` directly，so storage-backed blocks visibly expose
  pointers；the generic block editor can also present a pointer as editable text。These are downstream use/UI
  consequences，not reasons to change the persisted contract。

### Cross-runtime implementation pressure

- Add `Block.getHydratedContent()` and an unloaded-`Symbol`-backed ECMAScript private
  `#hydratedContent` cache in `@inkcre/core`；invalidate it on controlled `content`/`storage` updates。A normal
  TypeScript `private _hydratedContent` property is insufficient because it remains enumerable at runtime and
  `Block.update()` serializes the instance for PostgREST writes。
- Make browser resolvers consume block hydration and remove their `_rawContent` cache/storage branching。
- Preserve the generated `blocks.content: string` shape；the core-py FK action change does not alter TypeScript
  generated row fields。
- Keep hydration local to the peer：`Block.getHydratedContent()` selects a locally registered storage handler。
  A missing handler is an explicit unsupported-capability failure。If the product later needs one peer to execute
  hydration on behalf of another，design generic capability discovery and explicit peer delegation；do not
  privilege core-py or hide network forwarding inside the ordinary block-read contract。
- Implement browser handlers only for storage types required by this unit's accepted client-web behavior。
  PostgreSQL binary can use the admitted database protocol once generated types/coverage are aligned；future S3
  requires its own browser/runtime feasibility and deployment contract rather than automatic server fallback。
- Treat graph preview，fallback rendering and storage-backed edit affordances as acceptance surfaces when the
  client-web slice executes；do not eagerly hydrate every graph node merely to avoid displaying a pointer。

### Corrected inference

An earlier probe proposed a core-py block-content endpoint primarily to avoid storage-capability divergence。
That rationale is rejected：it imported a conventional client/server hierarchy that the peer topology explicitly
denies。Peer equality concerns authority and admitted protocol；runtime capability availability may differ and
must be represented honestly。

## PostgreSQL Binary / PostgREST Evidence

- `storage_blobs` is not a storage type。`storage_types.id = postgresql_binary` names the implementation family；
  `storages.id = -4` is its configured built-in instance；`storage_blobs(id, data)` is that implementation's
  current backing object relation；a block selects instance `-4` and carries the blob UUID in its opaque pointer。
- The current core contract exposes `inkcre.storage_blobs(id uuid, data bytea)` and describes `data` as protocol
  `string/bytea`。The client-web contract pin predates that migration，so `contract:sync --local-core ...` would
  add the relation to generated TypeScript rather than hand-editing `generated.ts`。
- The deployed/test PostgREST artifact is pinned to `v14.15` and exposes the `inkcre` schema to authenticated
  peers。No custom raw-media configuration is currently present。
- PostgREST 14 officially accepts `application/octet-stream` request bodies only through an RPC function with one
  unnamed `bytea` parameter。This gives create a natural raw path，but update also needs the target `blob_id`；an
  all-raw update would therefore require a custom request header，a binary envelope or another InKCre-specific wire
  convention。
- PostgREST 14 media-type handlers provide a native raw read path：an RPC function can take a normal UUID query
  parameter and return an `application/octet-stream` domain over `bytea`。The browser can then consume the response
  as `ArrayBuffer` without passing it through the normal JSON decoder。
- Older official PostgREST documentation explicitly supports selecting one `bytea` column with
  `Accept: application/octet-stream`；current v14 documentation instead emphasizes database media handlers。
  Therefore direct table raw-binary response is a candidate to prove against the pinned v14.15 image，not a
  contract to assume from old documentation。
- A stable v14-native alternative is an admitted PostgreSQL function/media handler that takes a blob UUID and
  returns an `application/octet-stream` domain over `bytea`。That remains PostgREST peer transport，not a core-py
  service endpoint，but it would require migration/ACL/contract-function generation work。
- JSON row selection would expose PostgreSQL's textual `bytea` representation and require browser decoding with
  roughly two hex characters per byte。It is the smallest schema change but a poor default for media-sized data。
- Direct relation C/U/D remains technically available because authenticated peers already have complete protocol
  table privileges。Create/update would send PostgreSQL's accepted `\\x...` hex `bytea` string through JSON，while
  delete can filter by UUID；this avoids a custom binary-update protocol at the cost of roughly 2× upload
  representation size。A hybrid of direct relation C/U/D plus a media-handler RPC for raw read is therefore the
  smallest coherent candidate，not yet a confirmed decision。
- `@supabase/postgrest-js` 2.110.8 allows setting request headers but its response path reads successful bodies as
  text and JSON-decodes them except for a few named formats。A binary handler therefore needs a small authenticated
  raw PostgREST transport in `packages/core` rather than pretending the normal typed row decoder can return bytes。
- Read hydration can return browser bytes (`ArrayBuffer`/`Uint8Array`) without storage owning MIME。MIME remains
  a semantic-media metadata decision。
- Sir has confirmed complete client-web PostgreSQL bytes lifecycle ownership。Raw upload via PostgREST generally
  requires an admitted bytea RPC with `Content-Type: application/octet-stream`，and deletion requires a narrowly
  admitted backing-object operation；their exact v14.15 shapes still require black-box proof。
- The current `WritableStorage` contract has create/read/delete but no update。Complete CRUD therefore requires a
  real pointer-scoped update operation in core-py and client-web；for PostgreSQL，updating `storage_blobs.data` under
  the same UUID is the natural implementation。
- `blocks.updated_at` only records mutation of the block row。A storage-backed object may be external and mutable，
  so neither this timestamp nor an instance-local hydrated-content cache can claim generic content freshness。
  Storage remains independent of block；refresh/reconciliation must be expressed above the CRUD contract。
- D-065 closes the local cache branch：ordinary hydration reuses the block instance snapshot，while an explicit
  refresh option bypasses and replaces it。No TTL，polling or cross-peer invalidation is inferred。
- D-066 closes the browser wire branch：Create and Read use admitted raw octet-stream RPC/media handlers；Update
  PATCHes hex bytea on the exact relation row；Delete uses exact relation DELETE。No custom update header or binary
  envelope is added。

## Opaque Bytes / Semantic Resolver Consequence

- Storage-backed actual content is logically bytes regardless of whether the physical mechanism is PostgreSQL
  `bytea`，S3，HTTP or another store。Streaming is an execution representation of those bytes，not a new semantic
  content kind。
- Resolver owns decoding/parsing and use-facing representation。Image/video/audio/PDF/EPUB/ZIP/file are resolver
  exact resolver IDs or graph information kinds，not storage types。
- Current `BlockModel` has no generic metadata column；its persisted information surface is resolver，conditional
  content/pointer，storage reference and record timestamps。The absence of a metadata field does not by itself prove
  that one should be added。
- Current Memos `CanonicalAttachment` combines filename，declared media type，size，source-created time and
  `blob_id` inside the same storage-backed block content。That conflicts with D-059/D-060：the protocol attachment
  attachment metadata block should retain protocol/source facts，while a related media/file semantic content block owns only its
  storage pointer as persisted `content`。
- Current image/video/html resolvers choose `http_image` / `http_video` / `http_html` storage instances and branch
  on those storage IDs。That makes storage selection carry semantic information-kind meaning and is direct rewrite
  evidence under D-062。
- Candidate authority split for review：source-declared filename/MIME/length/URL/timestamps stay in the canonical
  metadata block；storage retrieval/version mechanics stay private to its pointer/config；exact resolver ID plus
  hydrated bytes owns detected media kind and byte-derived solved content；organization may persist useful derived
  facts as graph enrichment。This candidate would not add `blocks.metadata` in the MVP。
- Memos v0.29.1 `Attachment.type` is the protocol MIME field。The upstream server accepts a provided normalized
  value and only falls back to filename extension then content detection when it is empty；the current MoeMemos MVP
  upload contract requires it。This is a stable Memos declaration，not a universal byte-truth rule。
- RSS 2.0 requires enclosure `url`，`length` and MIME `type`。Atom permits link `type` as an advisory MIME hint and
  says the media type returned on dereference is authoritative。The current RSS schema's URL-only enclosure tuple
  loses these protocol distinctions and cannot survive the rewrite。
- Current Python and TypeScript HTTP storage families both mix transport with content parsing/shape：JSON storage
  parses JSON，HTML storage sanitizes/extracts title，video storage returns a URL/MIME projection instead of bytes，
  and type IDs are content-kind-specific。They are rewrite evidence，not the target abstraction。
- The generic target is a small number of mechanics-named storages plus semantic resolvers。Exact HTTP storage
  split（for example one generic byte-fetcher versus policy-specific transports），PostgreSQL naming and legacy
  compatibility remain open until implementation preflight。
