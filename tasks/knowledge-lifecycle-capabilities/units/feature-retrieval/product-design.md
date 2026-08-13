# Lexical Retrieval Product Design（Preflight-refined Review Contract）

## Product Job

Lexical retrieval serves the case where a person or Agent remembers an explicit textual clue but does not know which
Block contains it or where that Block sits in the graph。The clue may be prose、a phrase、a name、filename、URL、identifier、
error token or a textual projection of media metadata。The operation locates existing information；it does not answer a
question、interpret synonyms or start graph traversal on the caller's behalf。

The source modality is not the boundary。A Mail MIME-part filename、PDF title/page count or audio codec can be lexical
evidence even though the underlying Block is not a text Block。OCR/transcription output can also become lexical evidence once
another owner produces it。Pixel/audio similarity remains perceptual retrieval；cross-modal meaning similarity remains
semantic retrieval。

## Retrieval Family Boundary

| Need | Owner |
| --- | --- |
| Match explicit textual features projected from one Block | lexical increment of `feature-retrieval` |
| Match visual/audio/video perceptual features | later perceptual increment of `feature-retrieval` |
| Match meaning or paraphrase | semantic retrieval |
| Locate/explore graph-visible dynamic properties and paths | graph-navigation retrieval |
| Combine several primitive retrieval modes | later hybrid composition |

Ownership follows current representation。A PDF page count embedded in Resolver-understood content may participate in a
lexical projection；after Organization externalizes that fact as Blocks/Relations，graph-navigation can locate it。The
lexical projection remains rebuildable support and does not become a second information authority。

## MVP Query Semantics

One request contains one non-empty plain query and a result limit from 1 through 20。It has no filters、query-language mode、
language/profile selection、threshold or pagination。

The fixed V1 matcher uses two explainable signals：

1. case-insensitive literal occurrence of the complete query in the Resolver label or lexical text；
2. all lower-cased lexical terms from PostgreSQL's `simple` text configuration occurring in the projected record。

Literal matches rank before terms-only matches；within those classes，label evidence is stronger than body evidence and
cover-density rank orders the remaining candidates。Stable Block ID is the final tie-breaker。This supports exact phrases、
punctuation-heavy identifiers and Chinese/no-space fragments without promising stemming、synonyms or spelling correction。
`pg_trgm` may accelerate literal `ILIKE` matching，but trigram similarity/fuzzy matching is not part of V1 behavior。

The plain query deliberately does not expose PostgreSQL `tsquery` or web-search operators。An actor asking for semantic
variation should use semantic retrieval；an actor needing graph facts should use graph-navigation。Hybrid syntax is deferred
until the primitive modes have real use evidence。

Lexical indexing may request missing Resolver materialization。This permits retrieval support to drive organization，例如 an
image Resolver may create an OCR text child before returning its lexical projection。The permission does not make every read a
write：a Resolver that already has sufficient filename/MIME/text evidence returns it without creating anything，and ranked
retrieval itself never runs maintenance。

Metadata is additive，not a substitute for document body recall。For a PDF with an available text layer，its body remains
searchable。If an existing or newly materialized semantic-content child owns that text，the child Block is indexed independently
and the root PDF record does not recursively duplicate the body；otherwise the exact Resolver may include Block-local available
body text in the root lexical projection。Scanned pages require an available OCR path，and encrypted/unsupported content may
remain metadata-only without pretending that the document was fully projected。

## Multimodal Textualization

Perceptual retrieval is not a prerequisite for recalling language carried by non-text media。The lexical increment includes
faithful modality-to-text paths：visible written text from images、spoken text from audio、and subtitle/spoken/on-screen text from
video。An exact Resolver may materialize these as ordinary `core.text.v1` Blocks；the resulting Blocks then use the same lexical
maintenance and query contract as authored text。

The product must distinguish faithful textualization from model-authored interpretation：

- OCR、speech transcription and source-native subtitle/caption extraction aim to preserve language actually present in the
  source，even though their derived text may contain recognition errors；
- a generated scene description、object list or summary adds an interpretation that was not literally authored in the source。

Both classes must be produced and become searchable in this increment，but through different lifecycles。Faithful textualization
is Resolver-owned missing materialization；description、summary and other model-authored interpretation are Organization-owned
effects。Lexical maintenance triggers only the former，then independently indexes the output of either lifecycle。The lexical
result claims only that the query matched the derived text Block；it does not claim perfect recognition or direct byte-level
proof of the original media。

Faithful signals remain separate graph children rather than being flattened into one aggregate text：visual written language is
linked as `text`，spoken language as `transcript`，and source-native subtitles as `subtitle`。A video may therefore have several
text children when it genuinely carries several kinds of language。These predicates describe the information role，not whether
OCR、ASR or a particular provider produced it。Each child is independently searchable；the parent does not recursively copy its
body，and the retrieval layer does not silently aggregate or deduplicate the signals。

Media interpretation is system-driven rather than gated by a per-Block user request。It is a distinct Organization approach
that selects media candidates，consumes their Resolver solved content plus bounded graph context and persists additive
`interpretation` graphs。This supersedes D-184's automatic-execution exclusion only for media interpretation；ordinary focal
rumination remains explicit。The approach is still independent of lexical query/maintenance and collection success。

The MVP automatic selector is missing-only：an image/audio/video Block with the approach's outgoing `interpretation` Relation is
not selected again。That Relation is presence evidence，not freshness authority；the system does not claim the interpretation is
current or optimal and does not automatically recompute it。A candidate that fails or produces no graph remains missing and may
be reconsidered by a later scheduled Job without introducing an attempt ledger。

Media interpretation uses a dedicated reusable AgentDefinition rather than the explicit rumination Agent。Its prompt can focus
on scene/content explanation and summary while retaining the existing validated graph-submission behavior。Deployments may bind
both Agents to the same model，but changing one approach's prompt/tools/budget does not silently redefine the other。

The approach routes by source modality to independent image、audio and video Agents。This permits modality-appropriate models、
prompts and budgets；a deployment may still reuse one Agent ID in several slots when one model is genuinely suitable。No
cross-modality Agent fallback is implicit。

## Result Contract

V1 returns at most 20 existing Blocks in authoritative order。Each match includes：

- the actual persisted Block；
- its Resolver-qualified label from the indexed snapshot；
- one bounded plain-text excerpt；
- an exact evidence kind：`label_exact`、`label_substring`、`text_substring` or `terms`；
- the within-class lexical rank used for deterministic ordering。

The result does not return Relation matches in V1。Current Relation content is a directed dynamic property，and finding those
facts belongs to graph-navigation。This avoids returning an edge that the current UI cannot route to and avoids flooding a
lexical query with every Relation whose endpoint label contains the term。A later concrete case involving material authored
text on Relations may reopen this boundary。

The excerpt is display text，never trusted HTML。A match explains why it appeared without requiring the caller to hydrate or
re-run a Resolver。Numeric rank is ordering detail only，not a cross-query probability or stable threshold。

## User Surface

The existing client-web start-page input becomes a lexical info-base lookup，not Chat InKCre and not a semantic question box。
Submitting updates the URL query so browser Back restores the result set。That page becomes the first real
`InfoBaseListView`：the lexical result list is its persistent base surface，and its route-destination outlet owns the existing
`BlockInspectorPopup` and `SolvedContentPopup` just as GraphSurface owns its own outlet。Selecting a result therefore opens the
Block inside the current List view；it does not discard the result context by navigating to GraphSurface。

`InfoBaseRouter` remains one app-bound、stateless Block/Relation route-to-UI-state mapping。The client-web adapter projects the
same domain `overview`、`block` and `solved-content` routes into whichever InfoBaseView currently hosts navigation。Vue Router
and browser history remain the sole history authority，including the lexical query。This does not create a second router、a
List-owned domain route vocabulary or a Mail/RSS/Memos-specific search page。

## Explicit Non-Goals

- fuzzy spelling、stemming/language dictionaries、synonym expansion or query suggestions；
- semantic/perceptual score fusion、graph predicates or arbitrary JSON field filtering；
- Relations、pagination、Chat/RAG answers or automatic Organization approaches beyond the exact media-interpretation path；
- perceptual similarity or direct object matching；
- claiming OCR/transcription is source authority or error-free；
- claiming that every fact present inside binary/structured content is already lexically projected。
