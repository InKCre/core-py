# Semantic Retrieval

- **Unit ID**: `semantic-retrieval`。
- **State**: **Implementation authorized；baseline commit pending**。Product/Technical contracts，including Peer routing/capability landings
  and HTTP inbound address authority，are approved through D-196；corpus judgments and quality thresholds are approved
  through D-188。
  Freshness/maintenance and Peer runtime Acceptance are approved through D-190。Implementation plan、preflight and Impact
  Handshake were approved for execution。Sir then requested one clean task-state commit before I0 begins；no code/schema
  mutation has occurred yet。
- **Objective**: let a deployment owner submit a natural-language intent and receive ranked existing Block/Relation
  matches，while a minimum organization rumination path can improve an info-base whose collected roots are too coarse for
  useful retrieval。
- **Guardrails**: graph rows remain information authority；retrieval returns Blocks/Relations rather than transient chunks
  or generated answers；organization stops at ordinary graph materialization；embedding/profile/records are use-owned
  derived support。Existing embedding/query/RAG code is evidence and failure material，not a compatibility surface。
- **Primary evidence**: real Memos and RSS graphs，exact resolver/hydration/storage contracts，current pgvector and AI
  split-brain implementation，and the relation-producer audit。
- **Active mode**: Baseline commit。Commit the reviewed task packet/local diagnostic-doc state，confirm a clean worktree，
  then begin I0 without reopening the approved design。
- **Next step**: create the explicitly requested baseline commit，then implement I0 ConfigContract/configs/timestamps。

## Control Gates

| Gate | State | Exit condition |
| --- | --- | --- |
| Product | Approved through D-185 | explicit BlockDetailsPanel action and empty completion response |
| Technical | Approved through D-196 | exact Resolver text/label matrix and clean shared-database rebuild close compatibility pressure |
| Acceptance | Approved through D-190 | corpus、quality、freshness and local/delegated Peer journeys closed |
| Implementation Plan | Approved | [exact dependency-ordered implementation plan](implementation-plan.md) maps code、migrations、cross-repo consumers and verification |
| Preflight | Closed for start | topology、SDK、Resolver、production、artifact、corpus and reset branches inspected；generated DDL is an execution-time evidence gate |
| Impact Handshake | Approved | [bounded cross-repo/runtime state diff](impact-handshake.md) names objects、blast radius、invariants、verification and uncertainty |
| Explicit Start / Execute | Granted | Sir said “开始”；execution resumes immediately after the requested clean baseline commit |
| Verify / Promote | Pending | pass Acceptance，then reconcile code、Hub/shared docs、local TDD and deployment owners |

Only this packet owns unit phase、gate and next step。Topic files own current task-state contracts；the
[decision register](../../decisions/index.md) alone owns decision history。

## Design Discussion Taste（guidelines，not contracts）

These are local steering reminders extracted from repeated corrections。They help frame discussion but cannot override
evidence、an approved contract or a concrete requirement。

- **Authority and coordination before transport**: first identify the shared fact、its owner and how equal Peers coordinate
  through the database。HTTP is an optional projection or an explicitly required request-response delegation protocol，not
  the default architecture frame for creating/configuring durable facts。
- **Approved signatures are anchors**: later diagrams and prose must reuse exact confirmed names/signatures，not casually
  paraphrase them。The current Agent entry is `AgentManager.run(agent_id, initial_message)`。
- **Separate owner schema from generic config mechanics**: an owner-defined Pydantic model owns the config value's shape。
  ConfigContract supplies generic model-driven mechanics；DeploymentConfigManager resolves the exact schema contract and
  persists deployment-scoped rows。Do not describe the generic manager as owning the business schema。
- **Do not strengthen invariants without value/evidence**: input constraints should match the actual authority and useful
  product invariant。A referenced bigint Agent identity is `int` here；do not invent `PositiveInt` when neither the
  database contract nor behavior requires that stronger rule。Existence remains a use-time reference check。

## Unit-local Anti-patterns

- Do not create a `RuminationManager` or organization-approach registry for the currently small rumination operation；keep
  it as `OrganizationManager.ruminate()`。This is a judgment about this unit's present topology，not a general discussion or
  module-design rule。

## Product Contract

### Semantic retrieval

- `SemanticRetrievalManager.retrieve()` is the single domain entry。It returns one bounded、globally ranked list of real
  Blocks/Relations plus score metadata；it does not generate an answer。
- Direct search、Chat InKCre or another Agent may consume the same capability。The client-web landing-page natural-language
  search is not the primary journey or Acceptance authority。
- Query is text。MVP uses one explicitly selected or deployment-default EmbeddingProfile、exact cosine comparison、optional
  score threshold、a maximum result bound and no pagination。
- A local peer may execute exact capability `core.semantic_retrieval.v1`；a peer without a local implementation delegates
  that same capability through PeerManager。Discovery and invocation remain separate，and no generic capability invocation
  endpoint or delegation job is introduced。

### Organization pressure

- Semantic granularity matters，but this unit does not create a BlockSegment/chunk information layer。A concrete
  `rumination` approach reconsiders one focal Block in its direct graph context and may add useful ordinary Blocks and
  Relations。
- The source Block and existing Relations remain unchanged。MVP does not replace/delete the source，retry、roll back、run a
  fallback pipeline or promise that every rumination mutates the graph。
- `breakdown` is historical/product shorthand，not a code/domain abstraction。`interpretation` is only the fallback
  persisted relation from the source to a representative derived-graph entry。
- MVP rumination uses resolver `get_text()` plus a bounded direct-relation snapshot，Resolver-owned on-demand schema /
  rooted GraphForm drafting Tools and one mutating `submit_graph(GraphForm)` Tool。It does not expose graph-reading/
  navigation Tools。
- `OrganizationManager.ruminate()` awaits the active Agent Turn and exposes shallow `None` completion rather than the
  internal Thread。Cannot-understand/no-write completes normally；budget exhaustion is one high-level organization failure；
  caller cancellation propagates to the Turn without a job/run entity。
- Repeated rumination is an independent additive attempt over the latest direct-relation snapshot and may duplicate graph
  facts。That snapshot may reveal a prior result but cannot prove its freshness or whether rerumination is needed；MVP adds
  no run record、fingerprint、freshness dependency or pre-execution skip。
- Rumination is triggered only by an explicit request for one focal Block。MVP has no collection hook、new-Block event、
  periodic scan、batch candidate selector or organization job。

## Confirmed Technical Topology

```text
                           deployment configs
                                  |
AIProvider -> AIModel -> EmbeddingProfile
      |          |              |
      |          +-> AIManager.chat/embed()
      |                         |       \
      |                         |        -> AgentManager -> Thread -> rumination -> GraphForm -> InfoBaseManager
      |                         |
Block/Resolver + RelationManager projection
                -> EmbeddingRecord maintenance
                -> SemanticRetrievalManager local retrieve
                                      |
                                      +-> PeerManager.delegate(exact capability)
                                                -> Peer Protocol outbound -> provider inbound -> local retrieve
```

| Design surface | Confirmed owner/boundary | Current source |
| --- | --- | --- |
| AI routing | shared AIProvider/AIModel facts；peer-local AIManager + dialect adapters；typed `embedding`/`chat` capabilities | [AI and projection](technical-design/ai-and-projection.md) |
| Semantic projection | Resolver owns Block `get_text()`/`get_label()`；RelationManager owns directed endpoint-label + content projection | [AI and projection](technical-design/ai-and-projection.md) |
| Resolver execution | exact in-scope IDs、complete text、Block-local label and producer obligations | [Resolver execution checklist](resolver-execution-checklist.md) |
| Vector space/records | mutable EmbeddingProfile + Block/Relation EmbeddingRecords；timestamp-based best-effort freshness | [Embedding profiles](technical-design/embedding-profiles.md) |
| Maintenance/config | SemanticRetrievalManager maintain/rebuild；`ConfigContract` mechanics + deployment-scoped `configs`/DeploymentConfigManager | [Maintenance and config](technical-design/maintenance-and-config.md) |
| Retrieval | ranked Block/Relation result、score、filters and bounded top-k contract | [Retrieval contract](technical-design/retrieval-contract.md) |
| Peer delivery | Peer capability snapshot + per-peer lease + protocol descriptor + one-shot HTTP delegation/failover | [Peer delegation](technical-design/peer-delegation.md) |
| Exact-target consumer migration | `PeerManager.delegate(..., route_to_peer=PeerRef)` constrains one exact Peer；`core.extension.management.v1` replaces known remote `Client.request()` consumers without alternate-Peer failover | [Peer delegation](technical-design/peer-delegation.md#exact-target-delegation-and-extension-management-approved-through-d-192) |
| Graph commands / rumination | Resolver/extension StarsGraphForm authoring；Agent runtime validates once，`draft_graph` adapts，Resolver creates，InfoBase normalizes/submits，PostgreSQL owns FK integrity | [Rumination and graph boundary](technical-design/rumination-agent-graph.md#current-boundary-ledger) |
| Agent runtime | persisted Agent definition、in-memory Thread persistence backend、cancellable per-turn Task、concurrent ToolCalls and single-writer closed message pairs | [Agent runtime](technical-design/agent-runtime.md) |
| Rumination selection | organization-owned deployment config references one AgentDefinition；`OrganizationManager.ruminate()` resolves it at use time and calls exact `AgentManager.run(agent_id, initial_message)` | [Rumination and graph boundary](technical-design/rumination-agent-graph.md#rumination-selection) |
| Shared timestamps | selected shared protocol rows use PostgreSQL `BEFORE UPDATE` timestamps | [Row timestamps](technical-design/shared-row-timestamps.md) |

The dependency-ordered implementation decomposition is tracked separately in the
[delivery map](delivery-map.md)；it is a design probe，not an execution baseline。

## Active Review Queue

Discuss one question at a time in this order。

1. **Implementation plan review**: inspect the exact increments、migration sequence、cross-repo handoff and remaining
   preflight list。
2. **Final preflight / Impact Handshake**: close provider、runtime database、artifact/corpus and production-read branches，
   then present the complete bounded state diff before requesting explicit start。

Producer grammar is closed through D-179。Base Forms omit database-managed state；flat GraphForm uses signed IDs for one-
command creation/reference；StarsGraphForm remains the recursive Resolver/extension authoring representation；the current
[boundary ledger](technical-design/rumination-agent-graph.md#current-boundary-ledger) owns validation/create/normalize/write
responsibilities。D-175–D-177 are correction history，not contracts to merge。

Thread/Tool lifecycle is no longer open：D-171 makes the Turn Task the structured-concurrency owner；individual ToolCalls
run concurrently，ordinary failures are isolated，abort cancels unfinished calls，and only a closed AssistantMessage +
ToolResultMessage pair is atomically committed。

## Acceptance Direction

- Corpus authority is deterministic source data exercised through real producers/runtime into disposable PostgreSQL：real
  Memos API journeys，real RSS/Atom served by a protocol double and a real Resolver/rumination compound document。Do not
  hand-insert the target graph as an internal fixture；production/demo data is supplementary exploration only。
- Prefer authentic、substantive and approachable software/AI/knowledge-systems material that the intended user might
  genuinely save；toy prose is not the primary semantic-quality authority。
- Invoke semantic retrieval directly，not through generated Chat/RAG answers。
- Use committed PostgreSQL Memos/RSS graphs plus a long/compound source that requires rumination to expose useful semantic
  units。Expected matches are judgments about entity identity/rank/coverage，not one provider's exact floating score。
- Each query classifies explicitly named real entities as `primary`、`relevant` or selected `distractor`；unjudged entities
  remain unjudged。Readable corpus references are Acceptance-harness aliases resolved to actual IDs only after real
  ingestion；they must not appear in production schemas、models、payloads、domain APIs or runtime code paths。
- Every accepted query must place at least one `primary` in the global top three and above every explicit `distractor`。
  `relevant` entities are not mandatory recall。Aggregate metrics and exact provider scores may diagnose but do not own
  pass/fail；one rumination journey additionally proves that its new specific entity enters the top three and outranks the
  coarse source。
- Candidate maintenance is explicit：after real Block/Relation dependency updates，stored stale records must be excluded
  until `maintain` replaces them；`retrieve` never repairs candidate records implicitly。Unavailable projection must not
  starve later candidates，and failed provider execution must not write an invalid record。Scheduler evidence verifies
  wiring to the same maintain operation rather than waiting on wall-clock time。
- Peer Acceptance proves local bypass and exact-capability delegation through real HTTP/JWT/codecs，plus expired/ineligible、
  pre-dispatch、`not-executed` and outcome-unknown branches。Both capabilities conservatively stop after possible execution；
  no retrieval-specific replay policy is added。Standards evidence plus application-boundary header/CORS assertions are
  sufficient；do not add a real reverse-proxy smoke deployment solely for this unit。
- Prove resolver projection、record freshness/invalidation、maintenance and retrieval through real runtime boundaries；use
  static checks for schema/type/registration invariants。
- Exercise both local execution and one delegated peer path through the real protocol/proxy boundary，including the exact
  protocol-guaranteed non-execution failover distinction。
- Keep the result bound small。A need for pagination or routinely useful results beyond the bound is retrieval-quality or
  graph-preparation pressure，not an automatic pagination requirement。

## Supporting Material

- [Evidence](evidence.md): current code/runtime facts and failure topology。
- [Technical design index](technical-design/index.md): current topic contracts and active technical edge。
- [Relation producer audit](relation-producer-audit.md): repository-owned directed-relation corrections that must occur at
  producer/migration boundaries，never inside retrieval or organization runtime。
- [Delivery map](delivery-map.md): dependency topology and provisional implementation increments。
- [Implementation plan](implementation-plan.md): exact dependency-ordered increments、migration/cross-repo sequence and
  preflight ledger；draft until final review。
- [Program packet](../../packet.md): program boundary and delivery loop。

## Explicit Non-Decisions

- No transient chunks/segments、ANN/HNSW index、cross-profile fusion、generic AI service proxy or global registry service。
- No answer generation、Chat InKCre product behavior、feature retrieval or graph-navigation retrieval in this unit。
- No generic `/capabilities/{id}/invoke`、delegation job、readiness advertisement or capability-aware PeerManager。
- No persistent Thread backend、Turn/ToolCall/ToolResult tables、checkpoint/resume or Agent-owned exactly-once guarantee。
- No claim that every Block/Relation can produce a text embedding；availability is profile/executor-relative。
- No legacy `Client(rest_api_url).request()` escape path after Peer delegation lands；direct database Active Records may
  remain where they own shared facts，but callable business capabilities route through their domain facade + PeerManager。
