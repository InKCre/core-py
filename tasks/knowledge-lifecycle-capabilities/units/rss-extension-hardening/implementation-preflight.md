# Semantic Content / RSS Implementation Preflight

## Control

- **Status**: replayed against the now-approved
  [implementation plan](implementation-plan.md)；D-076 closes the Memos data branch。This file does not authorize or
  sequence implementation。
- **Input**: D-057–D-076，
  [semantic-content-resolver-contracts.md](semantic-content-resolver-contracts.md) and
  [implementation-plan.md](implementation-plan.md)。
- **Purpose**: challenge the implementation plan's addresses、dependencies、runtime assumptions、migration paths and
  acceptance seams before it becomes an execution baseline。The plan owns intended steps；this file owns evidence and
  early fault discovery。

## Resolver Capability Boundary

Capability execution belongs to a resolver instance：

```python
resolver = ResolverManager.get(block)
text = await resolver.get_text(materialize_missing=False)
```

`ResolverManager` owns exact-ID registration/selection and optional shared MIME normalization/detection helpers。It
does not proxy `get_text()`、`get_str_for_embedding()` or other instance capabilities。The Python and TypeScript base
classes keep those two methods abstract；every concrete resolver implements them explicitly：

- unsupported capability raises `UnsupportedResolverCapability`；
- supported capability with no meaningful value for this block returns `None` / `null`；
- authored empty text remains `""` only when the exact content contract permits it；
- embedding callers skip `None` and do not translate unsupported into an empty embedding input。

The new common implementations are imported/registered by explicit core bootstrap，not accidentally through an
extension package import。Extension resolver registration remains extension-owned and installed-lifetime scoped。

## Proposed Core Runtime Dependencies

These are implementation choices，not shared protocol fields。Peer runtimes may use different parsers while
preserving the exact resolver IDs and nullable solved-fact meanings。

| Resolver | core-py implementation | client-web implementation |
| --- | --- | --- |
| `core.text.v1` | inline Unicode；storage-backed bytes use deterministic Unicode BOM handling then strict UTF-8 | `TextDecoder` with the same minimum policy |
| `core.html.v1` | decoded source；Unicode BOM / bounded in-document charset declaration / strict UTF-8；existing HTML-to-text library only for text projection | decoded source and text-only preview；no unsanitized `v-html` authority |
| `core.image.v1` | direct Pillow dependency；header/verification without pixel decoding | Blob/Object URL plus browser image metadata；dispose URLs on refresh/eviction |
| `core.audio.v1` | direct PyAV dependency；inspect stream/container metadata without decoding frames | Blob/Object URL + native media metadata；unavailable codec/container facts stay null |
| `core.video.v1` | the same PyAV dependency；inspect the deterministic primary video stream without decoding frames | Blob/Object URL + native media metadata；unavailable codec/frame-rate facts stay null |
| `core.pdf.v1` | direct pypdf dependency；root metadata/page tree only，no text/OCR | native open/render handle；unavailable parser facts stay null in the MVP peer |
| `core.epub.v1` | `zipfile` + existing hardened lxml configuration；read only container/OPF/navigation metadata | open/download handle；a future direct parser may populate more nullable facts |
| `core.zip.v1` | stdlib `zipfile` central directory only；never extract | open/download handle；parser facts may be null until a direct bounded runtime dependency is justified |
| `core.file.v1` | direct puremagic dependency for optional bounded byte-signature detection | generic Blob/open/download；detected MIME may remain null |

PyAV is preferred over a new `ffprobe` deployment dependency in this project: one Python dependency covers audio and
video，Python 3.12 wheels are available，and the implementation can consume hydrated bytes directly。It still carries
native FFmpeg parser risk，so resolution inspects metadata only and source/application download limits remain the first
resource boundary。This choice does not make PyAV or FFmpeg part of the persisted resolver contract。

No compatible mature EPUB library satisfies the current Python 3.12 and licensing boundary：current `epublib`
requires Python 3.13，while EbookLib adds an AGPL boundary。The narrow ZIP/container/OPF reader is therefore the
smaller long-term dependency，and must not grow into an EPUB object model or chapter extractor。

Statistical charset detection is intentionally excluded from the v1 authority path。A protocol/source adapter may
decode bytes before persistence when it owns a trustworthy external charset declaration；otherwise storage-backed
text uses the deterministic minimum above and fails explicitly when it cannot be decoded。This avoids introducing a
generic metadata map or making a heuristic detector cross-peer authority。

## Bounded Inspection And Failure Semantics

- Storage hydration returns actual `bytes` / `ArrayBuffer` and never decoded semantic objects。
- Source/application download limits bound whole-content residency；resolver parsing adds format-specific work bounds
  only where a central directory、page tree or native parser can amplify work。
- Image inspection does not decode pixels；audio/video inspection does not decode frames；PDF does not extract text；
  ZIP/EPUB never extract members。
- Encrypted PDF/ZIP is valid solved content with encryption facts and nullable inaccessible facts。Malformed claimed
  content raises an explicit resolution error；missing local parser/runtime raises unsupported capability；an
  unavailable optional fact is null。
- Embedded raw EXIF、media tags、PDF/XMP maps and archive member lists are not exposed by v1。Only the accepted bounded
  typed facts leave the parser boundary。

Exact numeric feed、article and enclosure download limits remain source-config fields/defaults in the RSS slice，not
resolver contract versions。Parser helpers may apply generous defense-in-depth caps without introducing streaming or
S3 acceptance into this unit。

## Storage Cut-over

The five current HTTP storage types (`http_image`、`http_video`、`http_html`、`http_json`、`http_text`) incorrectly own
semantic decoding/Accept behavior。The proposed hard cut replaces their in-repo semantic uses with one mechanics-only
`http` storage that returns bytes；resolver ID owns interpretation。PostgreSQL binary keeps its opaque JSON pointer
shape (`{"blob_id":"..."}`) and storage row owns bytes only。

The same implementation pass must：

1. add `BlockModel.get_hydrated_content(refresh=False)` and the corresponding client-web method/cache；
2. add writable-storage update and change `blocks.storage -> storages.id` deletion from `SET NULL` to `RESTRICT`；
3. implement client-web PostgreSQL binary create/read/update/delete through the admitted PostgREST/RPC surface；
4. remove client-web raw-pointer fallbacks from block content、graph preview and editor；
5. make unknown resolver/storage IDs explicit errors in both peers。

Storage deletion still does not infer block ownership from its pointer。Memos/RSS application services prove
exclusive graph ownership before deleting a semantic block/blob；the storage handler itself does not query or mutate
blocks。

## Propagated Hard-cut Surface

This is one coherent cut-over，not nine isolated class additions：

- core-py：replace the four retired resolver implementations and their import-time image AI side effect；make core
  registration explicit；update text/embedding callers for unsupported/null；
- client-web：exact registry with no default fallback，abstract instance capabilities，runtime content-handle disposal，
  nine IDs and safe unavailable/open/render states；
- Twitter：replace bare image/video/html/text producers，repair its currently untested API/persisted attachment-shape
  gap，and add collection → graph → resolver regression coverage；
- RSS/Atom：new namespaced versioned feed/feed-item/enclosure contracts，real enclosure metadata blocks and
  idempotent metadata → semantic materialization；
- Memos：attachment metadata remains the Memos protocol identity，but its storage pointer moves to one related
  semantic content block；download/delete/list/read assemble through resolvers and relations；
- tactical docs、fixtures and static retired-ID checks change in the same pass。

Proposed exact extension resolver IDs are：

- `extensions.memos.attachment.v2`，because the existing `v1` persisted/graph contract contains `blob_id` and
  `storage=-4` on the metadata block；
- `extensions.rss.feed.v1`、`extensions.rss.feed_item.v1` and `extensions.rss.enclosure.v1`，because the current RSS
  IDs are unversioned rather than an existing v1 contract。

Twitter's resolver version is intentionally not frozen here。Its root can remain relation-oriented without copying
attachment metadata into Tweet content；the RSS implementation plan should not redesign that extension beyond the
hard-cut producer/consumer regression needed for the shared IDs。

## Confirmed Memos V1 Data-preservation Branch

Sir accepts the one-time atomic data migration。A later read-only query through the local Neon CLI credential found
that canonical production is still at Alembic `d9f4e2a1b7c3`，has no `storage_blobs` table and has zero
`extensions.memos.attachment.v1` rows。The current public demo will therefore take the empty migration path，but the
migration still protects another database that has already run the Memos/PostgreSQL-binary implementation。

The confirmed migration is：

1. keep the existing attachment block ID as Memos protocol identity；
2. extract `blob_id` into the storage handler's minimal opaque pointer JSON on a new `core.<kind>.v1` semantic child，
   without changing the UUID or copying blob bytes；
3. rewrite the attachment root to inline `extensions.memos.attachment.v2` metadata without `blob_id`；
4. add one `content` relation from metadata to semantic block；existing `attachment:<order>` owner relations remain；
5. do not register the v1 decoder after migration；migration failure rolls the row conversion back。

This preserves actual user content while still ending with one current contract and no permanent compatibility
decoder。A clean-database/historical-row-loss branch is no longer part of the implementation plan。

The same production snapshot contains retired bare resolver rows：`html=1`、`image=28`、`text=8` and `video=3`。
D-075's accepted hard cut applies：they receive no compatibility decoder or data migration and become unsupported。

## Plan Replay

| Plan batch | Preflight result | Exposed correction / branch |
| --- | --- | --- |
| B0 dependencies | viable | PyAV is preferred to a new ffprobe deployment；EPUB uses a narrow ZIP/lxml reader because current compatible library candidates fail Python-version、maturity or license return |
| B1 storage/protocol | viable with an explicit generator change | core protocol currently publishes `functions: {}` and client generation hardcodes empty Functions；the plan now names both owners and does not hand-edit generated TypeScript |
| B2 resolver base | viable only as a whole-repository batch | making methods abstract affects every Python/TypeScript extension resolver；the plan updates all concrete classes before treating the batch as green |
| B3 nine resolvers | viable | core registration currently relies on incidental package imports；the plan adds explicit bootstrap outside extension sync and removes the image resolver's import-time AI credential side effect |
| B4 Memos v2 | viable and approved | production has no v1 rows，but another database may；D-076 keeps the reversible one-time migration and no permanent decoder |
| B5 producer cut-over | viable with a Twitter repair | Twitter's API DTO and persisted Tweet schema currently drop attachment fields and lack collection graph coverage；the plan makes this a regression prerequisite rather than blaming the new resolvers |
| B6 RSS primary | viable after plan review | production has no RSS/Atom source instances，but both source type catalog IDs exist；thin wrappers preserve those durable IDs while sharing the rewrite，avoiding an unnecessary source-row migration |
| B7 enrichment/materialization | viable | random storage pointers defeat content-based fetchsert；the plan uses enclosure identity + existing `content` relation + row re-check for idempotency |
| B8 acceptance | viable | current white-box RSS tests are replaced only after real HTTP→job→PostgreSQL→resolver scenarios exist；client-web already has a PostgREST E2E seam but no resolver/storage unit baseline |

The replay found no reason to split a separate foundation unit，add S3/streaming acceptance，retain old resolvers or
delegate client-web capability to core-py。It did show that the earlier document's seven-line “execution order” was not
an implementation plan；[implementation-plan.md](implementation-plan.md) now owns the real sequence。

## Verification Baseline

- Current read-only baseline：PDM lock is current；legacy resolver/storage targeted tests pass（3）；Memos attachment
  unit/backend tests pass（19）；client-web core and app type-check pass。
- New behavior is accepted through real-format samples and black-box/runtime journeys，not schema/helper tests that
  merely repeat static types。
- Required scenarios include PostgreSQL byte-exact CRUD/hydration，inline and storage-backed text/HTML，real image/
  audio/video/PDF/EPUB/ZIP samples，malformed/protected samples，Memos upload/read/download/delete，RSS and Atom
  collect/update/retry，enclosure manual/automatic materialization and missing local capability。
- A final repository-wide static assertion proves no current producer/documentation example emits retired resolver or
  content-specific HTTP storage IDs；historical task evidence may name them only as explicitly retired facts。
