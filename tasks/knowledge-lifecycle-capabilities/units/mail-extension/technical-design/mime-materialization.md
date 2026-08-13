# Mail MIME Materialization

- **Status**: D-271 freezes reconciliation eligibility required for exact remote-part access；D-272/D-273 freeze one Mail
  Source and one protocol-neutral Mail Resolver family as sibling clients of a selected extension-owned protocol adapter；
  D-274 freezes adapter-owned checkpoint interpretation/proposal versus Source-owned durable lifecycle；D-275 separates
  the public one-protocol-per-Source fact from its code adapter；D-276 separates `protocol` from typed `parameters`。
  D-277 narrows the current protocol type to `Literal["imap"]`；D-278 retains one small shared
  `create_mail_adapter(protocol, parameters)` construction seam；D-279 freezes one async-context adapter instance per domain
  command；D-280 freezes canonical Mail operations instead of protocol primitives。Collection streaming/checkpoint
  details are delegated by D-281 after reserving `collect` for Source。D-282 promotes writable materialization Storage
  selection to a Source-wide explicit → deployment default → built-in PostgreSQL fallback policy。D-283 persists the
  explicit selection as nullable `sources.storage`。D-284 corrects the tentative defensive getter：Storage
  registry/bootstrap owns code/catalog capability consistency；D-285 places its derived projection on
  `storage_types.writable` and constrains `sources.storage` to writable target types。D-286 freezes one outgoing `content`
  Relation as the initial durable materialization authority；D-287 corrects exact-one enforcement—any existing content child
  short-circuits remote routing and benign duplicates remain usable graph facts。D-288 promotes shallow semantic completion
  to the Resolver base contract。D-289 keeps SolvedMimePart's content singular；D-290 freezes database enforcement of
  writable Source targets。D-291 corrects D-289's tentative stability rule：InfoBaseManager returns any one matching child
  without uniqueness、ordering or repeat-read stability guarantees。This surface is closed for implementation planning。
- **Product boundary**: Collection persists text/HTML bodies and attachment/inline metadata but not non-text bytes。A later
  durable semantic content child is additive enrichment behavior executed by the Mail MIME-part Resolver；transient
  streaming remains use。

## No-Guess Occurrence Invariant

Remote MIME `part_id` is positional inside one occurrence's MIME tree。A Message-ID alone does not prove that two
occurrences have identical bytes or structure，so materialization must not compare metadata and silently choose the first
plausible UID。

Collection therefore applies this candidate guard before canonical Email reuse：

1. known/comparable exact occurrence or scoped EMAILID may reuse；
2. a sparse Message-ID reference anchor may be completed by its first occurrence；
3. any other Message-ID-only match involving attachment/inline MIME metadata creates another Email Block。

Consequently，a canonical Email with remote MIME components can have several live locators only when collection evidence
already establishes equivalent immutable content。Resolver may select an operational one for availability，not as a semantic
guess。No per-part remote binding、metadata fingerprint or user-facing “try another UID” recovery interaction is introduced。

## Frozen Dependency Boundary

```text
Mail Source ----------------------> selected protocol adapter -----> remote Mail server
Mail Resolvers needing remote I/O -> selected protocol adapter -----> remote Mail server
       |
       +--------------------------> WritableStorage + InfoBaseManager
```

Both callers resolve and validate typed access config before constructing/calling the adapter。Resolver may resolve the
live Source row behind provenance as data，but does not call the Source behavior。There are no parallel protocol-specific
Source/Resolver domain families。The adapter remains free of graph and Storage ownership。IMAP is the current concrete
protocol；the boundary permits a future POP3 adapter without pre-designing its locator grammar now。The selected adapter
declares/interprets typed protocol checkpoint state and returns a next-state proposal；Mail Source alone decides whether and
when to persist it。The Source persists public protocol choice，not an internal/versioned adapter ID；a shared explicit code
factory derives the corresponding implementation。

## Approved Command

Exact Adapter request/result/batching shapes are implementation-owned under D-281's boundary。

## Command Input and Graph Context（proposal）

The domain input is one MIME-part metadata BlockRef whose resolver is `extensions.mail.mime_part.v1`。The Resolver first
reads outgoing `content` Relations。When at least one exists，it resolves those children immediately and does **not** traverse
Email/Mailbox/Source provenance or choose a target writable Storage。Each child may still hydrate its own persisted
`block.storage` through its ordinary Resolver；that is content reading，not materialization routing。

Only when no child exists does the Resolver derive，rather than ask callers to supply：

1. the unique owning Email → MIME-part Relation and its `{role, part_id}`；
2. eligible exact Email occurrences from Mailbox `contains` Relations；
3. each Mailbox's owning Source anchor/binding and live protocol config；
4. the effective Source-wide writable Storage policy。

This keeps exact locator、credentials and target Storage routing out of the public call。An existing semantic child can be used even
after the Source is deleted/disabled because no remote access is then required。If creation is needed，one or more
D-271-eligible，proven-equivalent exact occurrences may supply an operational locator；unresolved owner/identity ambiguity or
absence of live Source config is materialization-unavailable。The Resolver never guesses from metadata；exact failover order
among equivalent locators is implementation-owned。

## Read versus Materialize（proposal）

```text
SolvedMimePart {
  root: CanonicalMimePart
  content: SolvedContentChild | null
}

SolvedContentChild {
  block: BlockModel
  solved_content: object
}
```

The child wrapper carries the actual result of the child Resolver，not only a BlockRef。Keeping its Block alongside the
solved content preserves resolver identity、graph navigation and future actions without confusing storage-backed
`Block.content`（an opaque pointer）with hydrated/solved content。The Resolver asks InfoBaseManager for one matching related
Block；the manager may implement this as one graph join/filter plus `LIMIT 1` without `ORDER BY`。When redundant Relations
exist，the chosen child need not be stable across reads。Graph multiplicity remains available to ordinary all-Relations
queries and Organization but does not change the singular use-facing meaning。

- `materialize_missing=false` reads graph state only and may return null `content`。
- `materialize_missing=true` permits creating the missing child；it does not require recreation when a child exists。
- `get_text` and `get_label` use filename、description、media type and other semantic metadata without materializing bytes。
- Email Resolver asks component Resolvers for read-only projections，so opening an Email does not download every attachment。
- `refresh` bypasses/replaces local Block hydration、Relation and solved snapshots only。It neither redownloads remote bytes nor
  migrates/replaces an existing child；that would require a future explicit command with different effects。

Per D-288，the success result omits `created/existing` status because Resolver solving returns semantic completion，not
command-mechanics status。This belongs in the Resolver base docstring and peer-equivalent contract，not a repeated Mail-only
rule。

## Concurrent Creation Sequence（proposal）

```text
Resolver                 MailAdapter             PostgreSQL / Storage
   |-- read content edges ----------------------------->|
   |<-- existing children? -----------------------------|
   |  get/solve any one if present                       |
   |-- fetch exact part ------->|                         |
   |<-- decoded bytes ----------|                         |
   |-- lock metadata Block ----------------------------->|
   |-- re-read content edges -------------------------->|
   |<-- concurrent children? ----------------------------|
   |  get/solve any one if present                       |
   |-- write bytes + child + content Relation ---------->|
   |<-- committed SolvedMimePart ------------------------|
```

- Remote I/O happens outside the row lock；slow IMAP cannot block graph writers。A rare race may download the same transient
  bytes twice，but the losing command discards them before Storage write。
- `SELECT ... FOR UPDATE` on the metadata Block reduces cooperating-producer duplicates。The generic Relation table is not
  distorted with a Mail-specific unique index and correctness does not rely on exact-one enforcement。
- After the lock，any existing Relation short-circuits creation regardless of which Storage the current Source policy would
  now choose。If a race still leaves several children，all remain ordinary usable graph facts；the Resolver uses any one
  without detecting multiplicity or promising stable selection，and Organization may later remove redundancy。
  Materialization does not fail or create another child。
- If still missing，resolve the selected exact occurrence's Source policy：`sources.storage` → deployment default → `-4`。
  Changing that policy affects future materializations only。
- Current PostgreSQL binary Storage writes bytes、semantic child and Relation through one caller transaction。This current
  guarantee does not invent cross-system rollback/exactly-once semantics for a future S3/Nextcloud Storage。

## Classification and Content Effect（proposal）

- Mail owns the evidence ladder：protocol-declared MIME type，then byte signature，then `core.file.v1` fallback。Existing
  `ResolverManager.match_media_type()` maps each candidate to an installed resolver and common `detect_media_type()` supplies
  signature evidence。RSS already composes the same primitives in its own protocol order and Memos calls the matcher during
  graph creation；there is no universal ordering method because evidence precedence remains extension-owned。
- image/audio/video/PDF/EPUB/ZIP select their exact existing core semantic Resolver；unknown content remains a file and keeps
  source-authored MIME metadata on the root。
- text/plain and text/html use the declared charset to transcode into the encoding expected by the core semantic Resolver；
  Storage still owns only actual bytes and never owns MIME parsing。
- Materialization adds only the semantic child and `content` Relation。It does not mutate CanonicalMimePart、Email identity、
  occurrence locator or Source checkpoint。

## Failure Boundary（proposal）

| Failure | Durable effect | Public meaning |
| --- | --- | --- |
| no exact eligible occurrence / Source binding | none | materialization unavailable |
| remote authentication/fetch/part missing | none | materialization failed with domain cause |
| multiple existing `content` Relations | none | get/solve any one；no uniqueness/order/stability promise；Organization may later reduce redundancy |
| explicitly selected/configured Storage is missing or read-only | none | Source/deployment configuration failure；do not hide the bad choice |
| Source and deployment Storage both absent | use built-in `-4` | ordinary fallback，not failure |
| PostgreSQL bytes/graph write failure | transaction rolls back | materialization failed |
| concurrent command created child first | winner remains；loser writes nothing | ordinary success with existing child |

There is no internal retry、alternate-part guessing、created/existing public status or eager duplicate repair。Errors matter to
an explicit download/view operation，so they surface to the calling capability/UI rather than becoming a silent no-op。
