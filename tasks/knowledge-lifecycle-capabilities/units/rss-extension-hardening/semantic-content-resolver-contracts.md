# Semantic Content Resolver Contracts And Solved Content

## Control

- **Status**: confirmed by D-075；this supporting design records the accepted boundary but is not a durable owner。
- **Pressure**: D-057–D-075 已固定 content kinds、metadata block/semantic content block/storage/resolver
  authority、per-extension
  classification、optional text capability 与 resolver effect vocabulary；本设计关闭 exact resolver IDs、
  resolver contract version 与 minimum solved/use-facing shape。
- **Scope**: shared persisted resolver identities and solved-content contracts across peers。Python/TypeScript
  class hierarchy、rendering component、parser dependency and transport implementation remain peer-local。

## Recommendation

### Exact resolver IDs and version axis

New text/HTML/image/audio/video/document/file semantic content blocks use nine flat，versioned core resolver IDs：

| Information kind | Resolver ID |
| --- | --- |
| Plain text | `core.text.v1` |
| HTML document | `core.html.v1` |
| Image | `core.image.v1` |
| Audio | `core.audio.v1` |
| Video | `core.video.v1` |
| PDF document | `core.pdf.v1` |
| EPUB publication | `core.epub.v1` |
| ZIP archive | `core.zip.v1` |
| Unknown/unsupported file | `core.file.v1` |

`core` means InKCre-owned shared semantics，not “execute in core-py” and not a client/server hierarchy。The IDs stay
flat because `media`、`document` and `archive` are useful conceptual groupings but do not currently own shared
persisted union schemas。A second format may later prove a reusable runtime helper；it must not retroactively turn
these exact decoder identities into a god object。

Resolver contract version tracks a persisted decoder/solved/graph contract change，not a file-format minor version，parser
package release or newly populated nullable fact。For example，`core.epub.v1` may interpret supported EPUB 3.x files
and expose their actual EPUB version；only an incompatible InKCre contract creates `v2`。

### Persistence and authority

The semantic content block persists only the already-confirmed block shape：

- `resolver` is one exact resolver ID above；
- inline `content` is actual content，or storage-backed `content` is the storage's opaque pointer；
- `storage` selects access mechanics；
- filename、protocol-declared MIME/length/URL/timestamps remain on the related metadata block；
- byte-derived facts remain resolver projections unless organization has a proven reason to materialize them。

The metadata block and semantic content block remain connected by the accepted `content` relation。A metadata block
is an ordinary block whose canonical content owns protocol/source-authored facts about related semantic content；it is not a wrapper
runtime type and is unrelated to a source module abstraction。Neither block duplicates the other's authority merely
to make a standalone DTO convenient。

## Solved Content Model

### One resolver contract，peer-local runtime representation

A resolver exposes typed，resolver-specific solved content。The stable cross-peer part is the meaning and
nullable facts。`core.text.v1` solves to a Unicode string；`core.html.v1` solves to an HTML source string。For
byte-oriented content，the actual-content handle is peer-local：Python may retain bytes/memoryview，while a browser may create
a `Blob`/object URL and own its disposal。Object URLs，Vue components and Python Pydantic class names are not shared
protocol fields and are never persisted。

The seven byte-oriented solved-content shapes（image/audio/video/PDF/EPUB/ZIP/file）expose these base facts：

- `byte_size: int`；
- `detected_media_type: str | None`，which never overwrites a metadata block's declared media type。

They do **not** include a generic metadata map，filename，source declaration，storage pointer，checksum，parse-status
object or duplicated `kind` field。Kind is already exact in the resolver ID；invalid content raises an explicit
resolution error。Checksum remains a future opt-in projection until a real identity/invalidation/use requirement
justifies its full-byte cost。

### Minimum resolver-specific facts

All parser-derived fields are nullable unless the format contract and a successful bounded parse prove them。
Unknown is not encoded as zero，empty string or `False`。

| Resolver ID | Minimum solved content/facts | Explicitly outside the minimum |
| --- | --- | --- |
| `core.text.v1` | Unicode text string | formatting/layout model，pretend byte size for inline text |
| `core.html.v1` | decoded HTML source string | persisted DOM，render component，sanitized-output authority，fetched source URL |
| `core.image.v1` | `format`，`width`，`height`，optional `frame_count` | raw EXIF map，GPS/capture-time exposure，OCR/vision caption |
| `core.audio.v1` | `container`，`codec`，`duration_ms`，`channels`，`sample_rate_hz`，optional `bitrate_bps` | lyrics，transcript，cover extraction，unbounded tags |
| `core.video.v1` | `container`，`video_codec`，`duration_ms`，`width`，`height`，optional `frame_rate` | full stream manifest，subtitle/chapter graph，transcript，poster generation |
| `core.pdf.v1` | `pdf_version`，`page_count`，`is_encrypted`，optional typed `title` / `author` | raw PDF/XMP map，full text，OCR，page graph |
| `core.epub.v1` | `epub_version`，`title`，`creators`，`languages`，`modified_at`，`manifest_count`，`spine_count`，`has_navigation` | raw package map，resource graph，chapter text/cover extraction |
| `core.zip.v1` | `member_count`，`total_compressed_bytes`，`total_uncompressed_bytes`，`compression_methods`，`encrypted_member_count` | extraction，unbounded member list，filesystem paths，member child graph |
| `core.file.v1` | no additional required fact | guessed filename，pretend text，format-specific optional fields |

This is deliberately not a universal media DTO。A shared runtime helper may carry the two base facts，but each persisted
resolver contract retains its own exact typed solved content and evolves independently。

## Application Capabilities

Solved content is not synonymous with text：

1. **Open/render**: every successfully hydrated block can expose a peer-local actual-content handle。A peer may render
   image/audio/video/PDF or only offer open/download for EPUB/ZIP/file；missing local capability is explicit。
2. **Text**: optional as an outcome，but explicit in the class contract。`ResolverBase.get_text()` remains abstract。
   Every concrete resolver must implement it；a resolver without text capability raises
   `UnsupportedResolverCapability`，while a capable resolver may return `None` when this particular block has no
   meaningful text。It never returns fake `""` merely to satisfy a base class。Protocol-authored alt/caption/title facts are preferred through graph
   relations。OCR，vision caption and speech transcription are derived capabilities，not root solved facts。
3. **Embedding text**: optional and distinct from solved content。The sink skips blocks with no embedding projection；
   it must not treat an empty string as successful indexing。A typed feature/index may consume dimensions，duration，
   page count or other solved facts without converting them to prose。
4. **Derived graph**: a resolver may support materializing transcript，caption，page/chapter/member or other graph。
   D-074 applies only when that capability exists：ordinary resolution may create a missing derivation，
   `materialize_missing=False` is read-only，and `refresh` alone never requests regeneration。

Capability is requested directly on a resolver instance，not through `ResolverManager` and not through a persisted
capability/status field：

- `ResolverBase` declares `get_text()` and `get_str_for_embedding()` as abstract；this makes every concrete
  resolver state its behavior explicitly and lets type/static checks enforce the method surface；
- an unsupported implementation raises `UnsupportedResolverCapability`（the Python error may derive from
  `NotImplementedError`）；
- a supported implementation may return `None` / `null` when this particular block has no meaningful value；
- `ResolverManager` only selects/constructs a resolver by exact resolver ID and may offer shared registration or MIME
  matching mechanisms；it does not own instance capability dispatch；
- `""` remains a valid authored empty string only where the owning content contract permits it；it is never a
  substitute for unsupported or absent output。

The minimum RSS/Memos vertical therefore does not have to implement OCR/STT or explode PDF/EPUB/ZIP into child blocks
to truthfully support these resolver contracts。It must implement bounded root inspection，actual-content use and honest
absence of unsupported projections。

## Why The Nine Resolver IDs Stay Separate

- Plain text and HTML remain distinct because HTML owns markup/document semantics and a derived text projection；
  silently treating HTML source as plain text would leak markup into use/embedding。
- Image/audio/video have different parsers，rendering behavior and typed facts even though all are commonly called
  media。
- PDF and EPUB are both documents but have incompatible document structures：PDF is page-oriented and may be scanned
  or encrypted；EPUB is a publication package with manifest，navigation and an ordered spine。
- EPUB is physically a specialized ZIP container，but its member order is not its reading order；the EPUB spine is。
- Generic ZIP owns archive/member/compression semantics，not document semantics。ZIP permits duplicate member names，
  so any future member materialization must use a central-directory entry identity/ordinal，not path alone。
- `core.file.v1` is the honest fallback for bytes whose stronger semantic decoder is unknown or unsupported。It is not
  a persistent parent class of every specialized resolver。

Primary evidence：

- [W3C EPUB 3.3](https://www.w3.org/TR/epub-33/) — current Recommendation；package metadata，manifest，navigation and spine/default reading
  order；
- [Python 3.12 zipfile](https://docs.python.org/3.12/library/zipfile.html) — ordered central-directory entries，
  duplicate names and decompression/resource hazards；
- [Python 3.12 mimetypes](https://docs.python.org/3.12/library/mimetypes.html) — suffix mapping is filename/URL evidence，
  not byte detection；
- [Pillow concepts](https://pillow.readthedocs.io/en/stable/handbook/concepts.html) — image size/mode and
  format-dependent auxiliary metadata；
- [Mutagen MP3 info](https://mutagen.readthedocs.io/en/latest/api/mp3.html) — duration/channels/bitrate/sample rate；
- [pypdf text extraction](https://pypdf.readthedocs.io/en/latest/user/extract-text.html) — scanned/OCR distinction and
  potentially high extraction cost；
- [IANA media types](https://www.iana.org/assignments/media-types/media-types.xhtml) — registered PDF/EPUB/ZIP and
  image/audio/video media types。

## Hard Cut-off And Peer Compatibility

- Existing bare `image`、`video`、`html` and `text` implementations are removed rather than retained or
  reinterpreted。Their current contracts mix URL/content/storage/AI concerns and are not a compatibility baseline worth
  extending，or lack the methods currently forced by the abstract base。The same coherent implementation pass updates
  every in-repo producer，consumer and test to the exact replacement IDs above。Old persisted rows become explicitly
  unsupported；D-075 accepts this hard cut-off without legacy decoders or a data migration。
- core-py already fails an unknown resolver ID explicitly；client-web's current fallback to the first/default resolver
  must be removed。Unavailable/unknown resolver ID becomes an explicit unsupported state，never silent text rendering。
- Installed resolver lifetime remains separate from extension enabled/running lifetime。The shared IDs above are core
  resolvers available in each capable peer；a peer without one reports unsupported capability rather than delegating
  implicitly to core-py。
- client-web graph preview and fallback must stop displaying a storage pointer as content。It may request a bounded
  text/feature projection or show a typed unavailable state，but must not eagerly hydrate every graph node。
- Twitter's image/video use and Memos attachment metadata-block behavior are rewritten and regression-tested in the
  same pass；they are not reasons to retain the old IDs or weaken the new contract。

## Technical Decisions Intentionally Deferred

D-075 accepts this Product/Technical boundary。Preflight still decides：

- exact parser/runtime dependencies and licenses（for example HTML text extraction，charset handling，Pillow，audio
  probing，ffprobe/pure-library trade-off，pypdf，EPUB parser）；
- bounded parse limits，encrypted/protected input behavior and proportional ZIP/PDF resource controls；
- exact Python/TypeScript type names and actual-content handles；
- optional embedded metadata privacy/exposure policy；
- derived relation grammar，materialization idempotency/provenance and child cleanup；
- an operational preflight proving that the accepted hard cut-off does not hide a concrete data-preservation need；
- browser render/open components and PostgreSQL binary transport execution details。

## Acceptance Consequences

The future execution baseline must prove at least：

- each new byte-oriented resolver ID resolves a storage-backed real sample through PostgreSQL bytes into its typed
  minimum facts and peer-local usable content；plain text and HTML also prove inline content，and storage-backed
  decoding is accepted only after its charset authority is frozen；
- Memos/RSS/Atom metadata-block facts remain authoritative and are not copied into semantic-content-block content；
- declared/observed MIME conflicts follow D-070–D-072 without rewriting the metadata block；
- unsupported MIME selects `core.file.v1`；unknown resolver ID and missing local storage/resolver fail explicitly；
- no-text blocks are skipped by embedding rather than indexed as empty strings；
- client-web does not expose opaque pointers and does not silently render unknown resolver IDs as text；
- no in-repo producer emits a retired resolver ID，and reads of those IDs fail explicitly rather than silently
  changing meaning。
