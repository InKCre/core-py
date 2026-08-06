# Semantic Retrieval Evidence

本文记录 Product/Technical 讨论所需的现状事实与失败证据，不把既有实现提升为设计 authority。

## Current Topology

```text
text query / block ID
  → core-py /blocks/query/by_embedding
  → hard-coded embedding provider/model call
  → block_embeddings cosine-distance query
  → raw BlockModel list

core-py /sink/rag
  → same embedding candidate query
  → optional nominal rerank
  → resolver.get_text() for prompt context
  → hard-coded chat model
  → generated answer

block fetchsert / 60s scheduler
  → resolver.get_str_for_embedding()
  → hard-coded embedding provider/model call
  → one block_embeddings row per block
```

client-web `packages/core` mirrors the resolver `getStrForEmbedding()` contract but does not own a shared retrieval
operation。client-webext separately calls core-py HTTP through `Block.vectorSearch()`；its local `Root.RAG()` is already
marked deprecated in favor of client-local generation。

## Proven Existing Surfaces

| Concern | Current evidence | Pressure, not decision |
| --- | --- | --- |
| User/API query | core-py accepts text or block ID and returns raw blocks | no explicit result contract、score、matched projection、graph context or stable pagination |
| Semantic projection | every resolver must implement `get_str_for_embedding()` in Python and TypeScript | resolver contract is coupled to one application mechanism；many implementations merely duplicate `get_text()` |
| Projection identity | embedding row is keyed only by block/relation ID | model、provider、dimensions、projection contract version and source snapshot are not represented；only one vector can exist |
| Model selection | query and write paths instantiate `text-embedding-v3` directly；database vector dimension is fixed at 1024 | runtime compatibility and migration behavior are implicit |
| Lifecycle | fetchsert embeds eagerly；ordinary create relies on a 60-second scan；edit leaves an existing embedding row in place | missing-row scan cannot repair stale rows；storage-backed bytes can change independently |
| Unsupported content | scheduler process-local set quarantines unsupported/unknown block versions | policy is not durable、peer-shared or tied to a named projection/index |
| Relations | every missing relation row embeds `relation.content` directly | no proven retrieval consumer or semantic-selection contract |
| Query parameters | server owns `max_distance`；client-webext sends `distance_threshold` | client control is silently ineffective under ordinary FastAPI extra-query handling |
| Reranking | current reranker re-queries the same vector distance and sorts it again | it is not independent reranking evidence |
| RAG | core-py joins retrieval、resolver text projection、prompt assembly and answer generation | client-webext already treats core generation as deprecated；Hub only claims retrieval/RAG as possible downstream uses |
| Acceptance | resolver tests cover unsupported/unknown skip behavior | no real semantic query corpus、relevance judgments、ranking/freshness contract or peer-level black-box acceptance |

## Hub Evidence Boundary

Current shared PRD/Product TDD only says collected information should support retrieval/indexing/embedding/downstream
use，and that embedding remains sink-owned even when ingestion triggers it。It does not define semantic retrieval as RAG，
does not require a resolver method named for embedding，and does not define a result or index lifecycle contract。

## AI Provider / Model Split-Brain Evidence

core-py `libs/ai.py` constructs one OpenAI-compatible client from `settings.llm_sp_base_url` and `llm_sp_ak` at import
time。`Chat(provider, model)` and `Embedding(provider, model)` retain `provider` in their object shape but execution uses
the same global client regardless。Embedding and language call sites then hard-code `text-embedding-v3` and `qwen-plus`。

client-web independently persists browser-local `LLMProviderConfig` values with provider `type`、API key、base URL and a
flat `models[]` list。client-webext has the more useful separation of `ProviderFactory` dialect strategies and an AI SDK
provider registry，but that registry is local to the browser and LLM-named；it is not a shared provider/model protocol and
does not describe model capabilities or modalities。

Mature AI SDK registry behavior supplies useful library evidence rather than InKCre authority：one registry can resolve
provider-qualified model IDs and exposes capability-specific language、embedding and image model lookup；an
OpenAI-compatible provider adapter owns base URL、API key、headers/query parameters and capability-specific model
factories。This supports separating provider instance、dialect adapter and typed model capability，but does not decide
InKCre persistence or peer ownership。

## Current `updated_at` Ownership Is Split

The database currently does not provide one general row-update timestamp contract：

- `server_default=CURRENT_TIMESTAMP` initializes values on insert only；it does not touch later updates。
- SQLAlchemy `onupdate=datetime.now` appears on blocks、relations and embedding models，but applies only to ORM-authored
  update statements and therefore cannot govern equal peers writing through PostgREST/direct SQL。
- one PostgreSQL trigger exists only on `blocks` and only changes `updated_at` when `content` changes。It does not cover
  resolver/storage changes、relations、embedding records or future AI registry/profile relations。
- the helper is now internal-schema runtime machinery，but its generic name obscures its block-content-specific behavior。

New shared protocol relations therefore need an explicit choice。For database-row mutation time across equal peers，a
selected-table PostgreSQL `BEFORE UPDATE` touch trigger is the smallest common authority；source-authored timestamps、job
event times and storage-content freshness remain separate semantics and must not receive that trigger mechanically。

## Existing Application Scenarios

| Existing surface | Actual user/downstream action | Existing expected result |
| --- | --- | --- |
| client-web start view | deployment owner could type a query into “Find information helps you here” | business logic is still a placeholder；Sir does not use InKCre this way and rejected it as the unit's primary journey |
| client-webext Explain agent | agent asks the info-base vector-search tool for knowledge relevant to an explanation | current tool expects knowledge-base `Block` values；answer generation stays in the client-local agent |
| client-webext Writing Assist | each replaceable word is queried within `learn_english.lexical` | current consumer expects ordered lexical `Block` values and reads the first block's canonical content |

Memos and RSS add realistic candidate shapes：a memo/comment is a block；feed、feed item、enclosure metadata、full-text
semantic content and attachment semantic content are blocks connected by relations。A hit on a child block can remain that exact block；
following an incoming/outgoing relation is graph navigation，not evidence for an invented retrieval “subject” layer。

Relations are also authoritative info-base entities，but these scenarios alone did not prove that every relation—or any
relation in the MVP—needed semantic indexing。That pressure drove the later D-097–D-102 review：MVP now permits Relation
matches through a RelationManager-owned endpoint-aware projection，while blind embedding of raw `relation.content` remains
rejected。

## Client-Web Rumination Trigger Evidence

The current client-web graph view already loads real Blocks/Relations，lets the user select one Block and opens a right-side
`BlockDetailsPanel` containing its ID、resolver、timestamps、storage and rendered content。That panel is the smallest coherent
UI point for an explicit focal-Block organization action；a global toolbar would first need another selection/context model。
On completion the parent graph view already owns one `loadData()` boundary capable of refreshing newly added graph facts。

The current `@inkcre/core` still has legacy `Client(rest_api_url).request(...)` and no approved Peer capability routing
implementation。It also assumes successful responses contain JSON，so it is failure evidence rather than a reusable path
for a `204` rumination result。The accepted Client→Peer hard cut and PeerHTTPOutbound must supply discovery、peer JWT、
normalized envelope、execution-marker and outcome-unknown semantics；the Block panel must call an organization-domain
facade rather than select a Core URL/provider itself。

Core-py's corresponding legacy publication path is `Settings.client_base_url / CLIENT_BASE_URL` →
`ClientManager.initialize()` → `clients.rest_api_url`。Local Compose currently supplies it from `CORE_PUBLIC_URL` with a
localhost fallback。The value demonstrates a real deployment-owned public-address requirement，but its Client/global-Peer-
field projection is rejected；the Peer HTTP protocol needs a renamed peer-local runtime authority from which concrete
inbounds derive their advertised absolute URLs。

Sir corrected the replacement authority：the needed public base belongs in the already approved owner-specific
`peers.config`，which deployment or client-web administration can edit directly。The runtime's capability snapshot remains
the derived routing projection。No new environment-only public-address authority is needed。

## Chunk And Breakdown Pressure

No current InKCre path creates a transient search chunk。The earlier proposal incorrectly added one as a result-layer
concept。Sir clarified that semantic granularity is nevertheless central to vector retrieval quality and that organization
breakdown partly exists to solve this problem without a second `block segment` information model。

The accepted direction is therefore：

- breakdown creates reusable ordinary blocks/relations at useful semantic granularity；
- semantic retrieval ranks and returns blocks/relations；
- this unit must exercise both sides through a long/compound corpus rather than assume one embedding per collected root is
  sufficient。

D-081 closes the earlier owner question：organization owns the graph breakdown；embedding records and vector retrieval
remain use-side derived support。

## Candidate Eligibility Correction

“Select which blocks/relations are searchable” was too close to an allowlist。The stronger default is to consider every
persisted block/relation as a graph entity candidate。For one embedding profile，an entity may still have no useful
embedding input：for example untranscribed audio/image bytes or structural relation labels such as `attachment:0` and
`full_text`。That is profile capability/availability，not exclusion from the info-base or from every future retrieval mode。

The later design closes this question through Resolver-owned general Block projections and RelationManager-owned directed
Relation projection，without restoring a resolver method coupled to embedding。

## Initial Diagnosis

`get_str_for_embedding()` is not an isolated naming defect。It is the visible seam where four currently unnamed
responsibilities meet：

1. **semantic selection**：which authored/solved/graph information represents a candidate；
2. **projection policy**：how that information is shaped for one retrieval strategy；
3. **model execution**：which provider/model turns an input into a vector；
4. **embedding-record lifecycle**：which projection/profile/source snapshot one durable derived row represents。

This diagnosis supplied the review order rather than a still-open question。D-079 onward fixed the result/consumer
boundary，and the current contracts place these responsibilities without preserving the old coupling。
