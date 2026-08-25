# Lexical Retrieval Technical Design（Preflight-refined Review Contract）

## Topology

```text
LexicalRetrievalManager.maintain/rebuild
  -> Block + exact Resolver lexical projection
       -> optional Resolver-owned graph materialization
  -> block_lexical_records (Lexical Retrieval-owned derived state)

Organization media-interpretation Job
  -> interpretation graph only
  -> [later independent lexical maintain/rebuild]
  -> block_lexical_records

LexicalRetrievalManager.retrieve_local
  -> PostgreSQL literal + FTS over fresh block_lexical_records
  -> existing Block + lexical evidence

client-web LexicalRetrievalManager.retrieve
  -> PeerManager.delegate(core.feature_retrieval.lexical.v1)
  -> core-py fixed inbound
  -> retrieve_local
```

`block_lexical_records` has exactly one lifecycle owner：Lexical Retrieval。Only
`LexicalRetrievalManager.maintain/rebuild` creates or updates those rows。Resolver materialization and Organization
interpretation may change the authoritative info-base graph，but neither writes lexical records、invokes lexical maintenance or
receives a callback into retrieval。Their new/changed Blocks become candidates only when an independently invoked maintenance
Job later scans current graph state。

`feature-retrieval` is the Unit，not a mandatory god class。The Python application module may contain a deep
`LexicalRetrievalManager` because projection maintenance、ranking、evidence and delegation form one lifecycle。Future
perceptual retrieval receives its own manager/records/contracts unless implementation evidence proves a useful shared seam。

## Resolver Projection Evolution

Direct `Block.content` search is forbidden：inline content may be source JSON，storage-backed content is a pointer，and both
bypass exact Resolver interpretation。

The existing general `get_text()` remains the sole text projection method，but gains a stable optional `context` parameter。
The default context preserves current semantic/organization behavior；`context="lexical"` asks for a plain-text projection
optimized for explicit feature recall。Context describes the requested representation，not a query、tokenizer、ranking profile、
AI model or permission to mutate。This is the evidence-led context evolution anticipated by D-096，not a resurrection of
`get_str_for_embedding()` or a model/provider dependency。

The lexical context is Block-local and non-recursive。A Resolver may inspect the focal Block's own canonical/solved content and
metadata needed to express it，but it does not copy lexical text owned by adjacent Blocks merely because a Relation makes that
text reachable。Those Blocks receive their own records。This prevents parent/semantic-child duplication without turning the
retrieval manager into a graph-aware deduplicator。

- Text-like Resolvers normally return the same value in both contexts。
- Media/structured Resolvers may remain unsupported in the default context while formatting bounded lexical metadata in the
  lexical context，例如 PDF title/author/page count/media type or image format/dimensions。
- Resolver owns field selection and human-readable serialization；the retrieval owner must not recursively serialize arbitrary
  solved-content fields。
- The projection is plain text and may use field labels；it is not canonical content、a graph write or UI markup。
- Metadata projection must not displace available document body text。When semantic body text is represented by child Blocks，
  those Blocks are independently maintained and the root lexical projection must not recursively copy their complete text；when
  no such graph representation exists，the exact Resolver may project Block-local available body on the root record。
- `materialize_missing=true` independently permits the Resolver to create a derivation required by the lexical projection。
  The Resolver may still return existing metadata without mutation；when it performs OCR or another graph-producing derivation，
  that exact Resolver owns the write。It is a retrieval-triggered Resolver materialization，not an Organization-owned approach；
  feature retrieval still does not construct the graph itself。

Both Python and TypeScript Resolver contracts adopt the same context vocabulary。client-web's remaining
`getStrForEmbedding()` methods are a stale contract regression and are hard-cut in this increment；semantic embedding continues
to use default `getText()`。

The current `core.pdf.v1` is an observed implementation gap：it inspects metadata through `pypdf` but declares text projection
unsupported。The increment must add bounded PDF body projection/materialization using a mature parser path；the metadata-only
example is not sufficient completion evidence。

## Multimodal Text Materialization（Proposal）

```text
image/audio/video Block
  -> exact Resolver get_text(context="lexical", materialize_missing=true)
  -> configured provider-neutral AI text-capable path or source-native extractor
  -> Resolver-owned derived core.text.v1 Block + exact relation
  -> later/current bounded lexical maintenance scan
  -> child block_lexical_records row
```

The parent projection remains Block-local：after creating or finding the child，it returns only parent-owned metadata rather
than copying the derived body。The maintenance scan reaches the new child by ordinary Block ID paging；bounded runs may index it
in the same invocation or the next Job without a Resolver→retrieval callback。

The scan does not freeze a starting maximum Block ID。A child created after the current cursor is therefore ordinary later work
in the same scan when the invocation still has capacity；otherwise a later Job sees it。`max_records` remains the hard bound，so
a faulty graph-producing Resolver cannot make one invocation chase its own writes without limit。This is deliberately simpler
than a materialization callback or a second derived-work queue。

The AI schema already models model `input_modalities` and `output_modalities`，but current canonical Chat messages and
`AIManager.chat()` hard-code text input。The AI boundary therefore extends only `UserMessage` with a discriminated content-part
union：

```text
TextContentPart  {type: "text",  text: str}
ImageContentPart {type: "image", data: bytes, media_type: str}
AudioContentPart {type: "audio", data: bytes, media_type: str}
VideoContentPart {type: "video", data: bytes, media_type: str}

UserMessage.content: non-empty tuple[UserContentPart, ...]
```

Bytes are the provider-neutral actual input；`media_type` is the standard content description needed for exact wire encoding。
Content parts contain neither Block/Storage references nor provider URLs。Organization converts a core media Resolver's typed
solved value into the initial multimodal UserMessage；a faithful-extraction Resolver constructs the same AI input directly。
AIManager remains graph-blind and derives the complete requested input-modality set from Message history，then verifies both the
persisted model declaration and peer-local dialect implementation before execution。No redundant `multimodal` feature flag is
added because modalities already own that fact。

The exact dialect adapter owns wire translation。The existing `core.openai-compatible.v1` remains the generic OpenAI SDK-backed
multi-capability dialect。OpenAI Chat Completions itself defines `image_url` and base64 `input_audio` content parts，so those
standard shapes belong in the generic adapter when the selected Model declares the modalities。OpenAI Chat does not define
`video_url`。Alibaba adds `video`/`video_url` and widens audio data to URL or Base64 Data URL，so the same SDK's ability to send
that JSON does not make those fields generic OpenAI protocol facts。

The reviewed proposal adds `core.alibaba-model-studio.v1` as the exact Alibaba dialect。It may reuse internal OpenAI
message/Tool translation helpers and implement every supported capability exposed by that provider family，but owns the
Alibaba-specific video/audio-URL shapes、Omni streaming assembly and provider input bounds。It is deliberately not named
`core.openai-chat.v1` or `core.alibaba-model-studio-openai-chat.v1`：D-157/D-158 already establish that `chat` is one canonical
AI capability and that an AIDialect may implement it through Chat Completions、Responses or native APIs while spanning other
capabilities。Changing to endpoint-scoped dialect identities would be an explicit topology reversal，not a naming cleanup。

OpenAI Responses is not this dialect's transport：the current Alibaba Responses surface does not support audio/video input，so
choosing it would make the accepted multimodal scope impossible。Native DashScope is also not added merely for theoretical
completeness because the documented OpenAI Chat surface passed the exact image、audio、video + function-Tool wire journeys。

For bounded media，the exact dialect maps actual bytes to base64 data URLs/data and its supported content items；the canonical
schema preserves none of those protocol names。The Alibaba dialect uses `stream=true` with text-only output modalities
for current Omni calls and assembles content + incremental ToolCall deltas into the same complete `AssistantMessage` contract。
Streaming is dialect-internal execution，not an Agent/Thread state or a second public result type。System/Assistant text and
ToolResult JSON retain their existing forms。Thread continues to persist one canonical Message history；the current in-memory
backend holds bytes as part of the UserMessage，while a future persistence backend may optimize physical storage internally
without exposing InfoBase references or creating a separate media-input lifecycle。

Dialect support is an executable local fact in addition to the persisted AI Model declaration。`AIDialectAdapter` therefore
exposes a static input-modality support predicate used by AIManager's ordinary capability check；no dialect-capability table or
remote provider probe is introduced。The Alibaba dialect supports the exact set proved by its implementation/tests；the generic
dialect does not inherit Alibaba-specific video support。

An HTTP Storage pointer is not automatically content authority or a provider-reachable URL。The ordinary Resolver path still
hydrates actual bytes lazily and produces solved content without copying those bytes into PostgreSQL binary Storage。As a
transport optimization，Storage may optionally expose `get_transfer_url(pointer) -> str | None`；HTTP Storage may return its
validated origin URL while PostgreSQL binary Storage returns `None`，and a future object Storage may return a scoped URL。This
method describes an available transfer representation，not a promise that a third-party backend can fetch it。

The canonical media content part continues to carry actual bytes + MIME and may additionally carry an optional origin
`transfer_url` hint。It carries neither a Block/Storage reference nor a provider-upload URL。The exact dialect uses a shallow
MVP ladder：prefer inline bytes within its documented stable bound；only when inline transfer is unavailable/oversized may it use
an accepted transfer URL；otherwise report capability unavailable。It does not retry a possibly charged model call after remote
fetch failure，does not silently truncate/transcode media and does not stage objects。Thus small Twitter images remain reliable
through lazy hydration even when their durable Storage is HTTP，while a large public video can receive best-effort direct transfer
without pretending hotlink-protected URLs are reliable。

This shape is not promoted into a Resolver projection。Resolver-owned faithful extraction consumes its own solved content；
AIManager remains graph-blind。

Faithful extraction uses direct AI Model references，not Agents：the Resolver already owns the extraction prompt、the exact
derived role and the text-Block graph write，so Agent prompt/Tool/Turn lifecycle would duplicate that authority。Configuration
follows the exact behavior owner rather than creating one cross-Resolver “media” owner：

```text
key:    core.resolver.image
schema: core.resolver.image.config.v1
value:  {text_model: int}

key:    core.resolver.audio
schema: core.resolver.audio.config.v1
value:  {transcript_model: int}

key:    core.resolver.video
schema: core.resolver.video.config.v1
value:  {text_model: int, transcript_model: int}
```

The same AI Model may fill several fields。Source-native video subtitle extraction needs no Model reference。Each field is a
use-time reference：one dangling、disabled or modality-incapable Model makes only that exact missing derivation unavailable and
does not authorize AIManager to choose/fail over to another Model。Prompts remain code-owned Resolver behavior rather than
deployment config。Provider-backed corpus/model IDs remain acceptance-environment facts，not schema defaults。

Faithful materialization writes one `core.text.v1` child per distinct signal：

```text
image --text-------> text Block
audio --transcript-> text Block
video --subtitle--> text Block
video --transcript-> text Block
video --text-------> text Block
```

The predicates express the child's role relative to the media Block；extractor technology and provider identity remain outside
the graph vocabulary。A generated description/summary instead enters the separate `interpretation` graph path。Existing-child
reuse is therefore checked per exact relation role，not against one ambiguous “any derived text” marker。For video，subtitle、
transcript and visible-text attempts are independent：one unavailable role does not prevent existing/source-native/other-role
children from being returned or created，and the shallow Resolver completion contract does not expose created/existing details。

Model-authored interpretation uses a distinct path：

```text
system-driven Organization media-interpretation approach
  -> select candidate media Block
  -> Resolver.get_solved_content() + bounded graph context
  -> configured multimodal model/Agent
  -> additive Graph command
  -> additive interpretation Block/Relation
  -> ordinary lexical maintenance indexes the new text Block
```

`materialize_missing` does not enter this path。Organization consumes the existing typed solved value instead of inspecting
`Block.content` or asking `get_text()` to disguise media as text。It builds one initial UserMessage containing a bounded textual
focal/direct-relation context plus exactly the focal media content part。Agent/model selection remains deployment-owned and exact
graph production remains behind the existing Agent Tool boundary。

The automatic command is the exact typed Job `core.organization.media_interpretation.v1` with `{}` parameters，normally created
by one Cron template。At execution time Organization selects deterministic bounded pages across `core.image/audio/video.v1`
Blocks with no outgoing `interpretation` Relation，then routes each candidate through its modality Agent。One candidate failure/
no-output is diagnostic and does not stop later candidates；successful Relations make those Blocks absent from subsequent
missing-only scans。Job state may expose bounded per-modality counts/diagnostics，but there is no cursor、checkpoint、attempt/
freshness table、automatic retry/recompute or coupling to lexical Job state。

Because the Job parameters are intentionally empty，the candidate and diagnostic limits are implementation-owned bounded
policy，not a hidden dynamic schedule payload。A Peer is statically eligible when at least one configured modality Agent can run
locally。It processes every capable candidate and leaves unsupported-modality candidates missing for a later independent Job。
The Job does not claim that every currently missing medium converged，and it does not add a partial-progress cursor to simulate
that stronger promise。

The approach selects an independent persisted AgentDefinition through its own deployment config。AgentManager remains the owner
of model calls、message history and validated Tool execution；Organization owns candidate/context assembly and completion meaning。
The Agent may share a model or Tool IDs with rumination，but not its config identity or prompt lifecycle。A direct free-text
`AIManager.chat()` response parsed and persisted by Organization is rejected in favor of the existing graph Tool boundary。

Proposed exact config key/schema：

```text
key:    core.organization.media_interpretation
schema: core.organization.media_interpretation.config.v1
value:  {image_agent: int, audio_agent: int, video_agent: int}
```

Organization selects one reference from the focal media modality before `AgentManager.run()`。No `_id` suffix is used；the
field names describe Agent references rather than database column implementation。All fields are required，may hold the same
value，and are resolved defensively when used rather than reverse-restricting Agent deletion。

## Persisted Derived Record

One Block has at most one `block_lexical_records` row：

```text
block          integer PK/FK -> blocks.id ON DELETE CASCADE
label          text NOT NULL
text           text NULL
search_vector  tsvector NOT NULL
created_at     timestamptz NOT NULL
updated_at     timestamptz NOT NULL
```

The Block reference is the record identity；there is no independent sequence。No `LexicalProfile` or deployment config is
introduced because V1 has one fixed strategy and no independent selection/lifecycle/reuse pressure。The exact capability ID
and migration own the strategy version。

`label` is the concise、Resolver-qualified Block reference used for display and high-value recall。`text` is the fuller lexical
projection and may be null；it need not repeat the label。Both are stored so result evidence agrees with the exact indexed
snapshot。`search_vector` is a PostgreSQL `tsvector` derived from both：label lexemes receive weight A and text lexemes weight D，
with positions retained under the `simple` configuration。It is not an embedding/vector-space value and is never returned as
information authority。A GIN
index supports `@@` term matching。`pg_trgm` GIN indexes on label/text accelerate escaped literal `ILIKE` searches；the extension
is used as an index mechanism only，not as authorization for fuzzy product behavior。

The row stores the projection text because retrieval evidence must agree with the indexed snapshot and must not call a Resolver
or external Storage while answering。The duplication is rebuildable application support，not information authority。

## Maintenance And Freshness

`maintain()` scans deterministic Block-ID pages，projects outside a transaction，and upserts bounded complete batches in short
transactions。Unknown Resolver/projection/size failures become bounded diagnostics and do not stop the scan。`rebuild()` uses
its invocation timestamp as a cutoff，matching the proven semantic-retrieval pattern。

A record is queryable only when `record.updated_at >= block.updated_at`。The known limit remains explicit：externally mutable
storage bytes or Resolver projections depending on changed Relations do not necessarily advance the focal Block timestamp。
No trigger cascade、dependency graph、content hash or dirty queue is added before measured harm。Explicit rebuild is the current
recovery path。

Lexical maintain and rebuild are exact typed Jobs。A deployment may create them explicitly or use the existing Cron table as a
recurring Job template；one capable Peer claims each Job before a thin Handler calls `LexicalRetrievalManager`。Successful rows
are natural resumable progress，so no separate checkpoint/retry lifecycle is needed。Retrieval never runs hidden maintenance。

Semantic maintain/rebuild migrate to the same topology。The legacy `run.py` direct interval call to
`SemanticRetrievalManager.maintain_default()` is removed rather than retained as a second scheduling authority。

The exact Job contracts are：

```text
core.feature_retrieval.lexical.maintain.v1
core.feature_retrieval.lexical.rebuild.v1
  parameters: {options: LexicalMaintenanceOptions = defaults}

core.semantic_retrieval.maintain.v1
core.semantic_retrieval.rebuild.v1
  parameters: {profile: int | null = null,
               options: EmbeddingMaintenanceOptions = defaults}
```

`profile` is a true creator-selected semantic vector-space reference；`null` deliberately resolves the deployment default at
execution。The bounded options snapshot work/cost policy for one command and may be reused by a Cron template。Candidate IDs、
scan cursors and the current missing/stale set are manager-derived execution facts and never enter Job parameters。Handlers
project their bounded reports into `job.state` and do not duplicate domain logic。Maintain/rebuild remain separate exact intents；
Cron does not judge whether recurring rebuild is useful。

Pre-claim `can_handle` is static/best-effort eligibility，not a provider health probe。AIManager supplies a deep predicate over
persisted Model capability + enabled Provider/Model + peer-local dialect registration/config；AgentManager adds Agent existence、
bound Tool availability and requested input modalities。Semantic Jobs use the selected Profile's Model；media interpretation is
eligible when at least one configured modality Agent is locally executable，then records per-candidate failures for the rest。
Remote API policy/quota can still change after the check；that ordinary TOCTOU outcome belongs to Job execution and does not
introduce a preflight network request、fallback or claim rollback。

An execution-time provider rejection is therefore a candidate diagnostic rather than a model-selection signal。The Handler may
finish after bounded candidate failures；the graph remains the progress authority，and only successful `interpretation` Relations
remove candidates from later Jobs。If no configured modality is statically executable，`can_handle` is false and the Job stays
pending until some capable Peer/config appears。

PostgreSQL's documented `tsvector`/position limits are treated as projection-unavailable diagnostics in V1；the implementation
does not silently truncate content or invent durable Block segments。Organization breakdown remains the route for persistently
smaller information units。Internal derived segmentation is deferred until a real accepted corpus exceeds the engine bound。

## Matching And Ranking Execution

`retrieve_local()` builds an escaped case-insensitive literal predicate plus `plainto_tsquery('simple', query)` when that query
contains lexemes。It selects only fresh records and assigns the best evidence class per Block：

1. normalized label equals the complete query；
2. label contains the complete query；
3. lexical text contains the complete query；
4. weighted vector contains every parsed query term。

The query orders by evidence class，then `ts_rank_cd` over the weighted vector，then Block ID。It calculates a bounded plain
excerpt only for the final result set。No stored procedure/RPC owns this behavior：SQLAlchemy expresses the manager-owned query，
while PostgreSQL supplies indexed operators and ranking primitives。This differs from placing the business capability inside a
database function。

## Peer And API Boundary

- exact capability：`core.feature_retrieval.lexical.v1`；
- fixed inbound：`POST /feature-retrieval/lexical`；
- business facade：`LexicalRetrievalManager.retrieve(request, route_to_peer=None)`；
- provider seam：`retrieve_local(request)`，which never delegates；
- `route_to_peer` remains caller-local policy and never enters the capability payload。

Core-py advertises the inbound after route/runtime readiness。The static browser implements only the typed facade and delegates
through existing Peer HTTP。Although PostgREST exposes basic FTS filters，direct browser execution cannot preserve the accepted
ranking/evidence contract without database computed/RPC business logic，so it is not a second implementation path。

## Client-Web Boundary

`@inkcre/core` owns Zod request/result contracts and the delegating facade。The start view owns query state and result
presentation；it does not parse PostgreSQL syntax or hydrate results。The resulting `InfoBaseListView` is an InfoBase navigation
host：it keeps the result list as its persistent base surface and hosts its own `BlockInspectorPopup`/`SolvedContentPopup`
destination outlet。Result selection calls the app-bound `InfoBaseRouter` and stays within that List host。

The client-web adapter recognizes both List- and Graph-hosted URL projections of the same domain `InfoBaseRoute`。When pushing a
Block destination，it preserves the active host and current List query instead of hard-coding GraphSurface。The existing
GraphSurface remains the graph host and still loads the graph globally；that scaling pressure belongs to its own
InfoBase/graph-navigation work and is not imposed on List retrieval。
