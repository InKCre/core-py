# Lexical Retrieval Implementation Plan（Provisional）

> This is an execution preflight，not implementation authorization。The plan is revised after product/technical review and an
> Impact Handshake。

## I0 — Freeze Contracts

- confirm product matching/evidence semantics and the Resolver projection-context choice；
- reconcile both current feature branches with their latest `main` before layering new implementation，resolving ownership
  conflicts rather than assuming the old PR heads remain executable baselines；
- promote accepted shared PRD/Product-TDD deltas through the Hub workflow at the implementation/promotion stage；
- freeze exact schema、capability、route and cross-peer names。

## I1 — Resolver Projection Parity

- add stable lexical text context to Python and TypeScript Resolver contracts；
- implement bounded lexical projections across built-in and in-scope extension Resolvers，with media metadata remaining plain
  derived text；
- close the current PDF metadata-only gap so a real text-layer PDF body remains searchable，while semantic-content child Blocks
  are indexed independently under a Block-local、non-recursive projection contract；
- remove client-web `getStrForEmbedding()` and keep semantic consumers on default `getText()`；
- verify no direct `Block.content` retrieval path；lexical maintenance permits only Resolver-owned missing materialization and
  does not construct organization graph itself。

## I2 — Provider-Neutral Multimodal Textualization

- extend canonical AI User messages with non-empty text/image/audio/video content parts carrying actual bytes + MIME；derive
  requested modalities in AIManager，verify model/dialect support，and translate bytes only inside the exact dialect adapter；
- extend `core.openai-compatible.v1` only with OpenAI-standard Chat image/base64-audio parts，and add the proposed
  `core.alibaba-model-studio.v1` cross-capability dialect for documented Alibaba video/audio-URL extensions；do not route
  audio/video through Responses or silently widen the generic dialect；
- add an optional Storage-owned transfer-URL hint without changing lazy hydrated bytes as the semantic/default input；prefer
  bounded inline bytes，then use an accepted URL only when inline transfer is unavailable，with no hidden retry/staging；
- aggregate Alibaba streaming multimodal text/ToolCall deltas behind the existing complete AssistantMessage result；
- preserve the Thread message-only contract and keep Block/Storage refs、provider URLs and Resolver-specific solved types out of
  AI/Agent schemas；
- register exact image/audio/video Resolver deployment configs with role-scoped direct AI Model references；keep prompts
  code-owned，references use-time validated and AIManager free of automatic Model selection/failover；
- implement image、audio and video missing-text materialization as separate ordinary `core.text.v1` child graphs using exact
  `text`、`transcript` and `subtitle` information-role Relations，with idempotent reuse per role；
- page maintenance by increasing Block ID without a frozen upper bound，while enforcing the invocation's hard `max_records`
  limit so newly materialized child Blocks can be indexed immediately without an unbounded self-extending scan；
- implement a system-driven media-interpretation Organization path that consumes Resolver solved content，runs a configured
  per-modality independent Agent，selects missing-only candidates and persists additive interpretation graphs through existing
  validated Tools，without routing that effect through `materialize_missing` or adding attempt/freshness records；
- register one parameterless `core.organization.media_interpretation.v1` convergence Job；keep candidate/modality selection
  inside Organization，keep candidate/diagnostic bounds code-owned，and use Job state only for bounded outcome reporting；
- add best-effort AIModel/Agent local-executability predicates for Job `can_handle` without remote probes or fallback；
- verify a credentialed real-media path and bounded unavailable outcomes without adding perceptual matching。

## I3 — Derived Record And Migration

- add `pg_trgm` plus `block_lexical_records` table、FK/timestamps and GIN indexes；
- update SQLModel/Alembic metadata、application-table/readiness manifest and generated client database projection；
- keep one Block-keyed record with no profile/config/independent sequence。

## I4 — Local Maintenance、Jobs And Retrieval

- implement bounded lexical maintain/rebuild、freshness and diagnostics behind exact
  `core.feature_retrieval.lexical.{maintain,rebuild}.v1` Job Handlers；
- add `core.semantic_retrieval.{maintain,rebuild}.v1` Handlers around existing profile/options contracts，project reports to Job
  state，and delete the peer-local direct timer；
- implement escaped literal + plain all-term matching、evidence classification、ranking and plain excerpt construction；
- verify missing/stale/oversized/unknown projection branches without creating a retry/job/dirty lifecycle。

## I5 — Exact Peer Capability

- add `core.feature_retrieval.lexical.v1` typed request/result and fixed non-delegating core inbound；
- register/publish the inbound with existing runtime lifecycle；
- add `@inkcre/core` facade and `routeToPeer` delegation while keeping capability payload opaque to PeerManager。

## I6 — Client-Web User Journey

- turn the start placeholder into the first URL-backed InfoBaseListView with loading/empty/error/result states；
- render label、plain excerpt and match reason；
- host BlockInspectorPopup/SolvedContentPopup as the List view's route-destination outlet；
- extend the app's InfoBaseRouter projection so Block navigation preserves the active List/Graph host and browser Back semantics。

## I7 — Acceptance、Hardening And Promotion

- build J1–J7 from real Memos/RSS/Mail/Storage producers、pinned article and real multimodal corpus；
- run focused checks，then full `pdm run check` and `pnpm check`；
- after separately authorized owner-scoped commits/pushes，wait for the exact core-py PR database/application preview and
  client-web PR preview to pass，then run J7 against the matching core preview；
- update core/client local architecture and exact shared Hub owners，publish Hub first，then bump each Spoke separately；
- close the lexical increment without claiming perceptual or hybrid retrieval complete。

## Concrete Change Map（Preflight）

- **Resolver contract**：`app/business/info_base/resolver/main.py` + every Python exact Resolver；client-web
  `packages/core/src/info-base/resolvers/**`。Add lexical context consistently and hard-cut TypeScript embedding-only projection。
- **AI/Agent seam**：`app/schemas/ai/chat.py`、`app/business/ai/{main,contracts}.py`、generic OpenAI translation helpers、
  `app/business/ai/dialects/{openai_compatible,alibaba_model_studio}.py` and Agent Thread tests。No InfoBase imports
  enter AI/Agent contracts；Alibaba protocol extensions do not leak into the generic dialect ID。
- **Organization**：split the growing `app/business/organization.py` only if implementation size justifies a package；retain
  `OrganizationManager` as public owner and reuse existing graph Tools。Register the parameterless Handler through ordinary
  runtime import/bootstrap。
- **Lexical capability**：new schema/business package + fixed route/inbound，then register table/readiness/capability facts in
  existing catalog owners；do not put ranking in a PostgreSQL RPC。
- **Semantic cutover**：wrap existing manager methods with exact Job Handlers，remove `run.py`'s direct timer and its Settings/
  runtime-composition tests，preserving direct manager calls for internal/test use。
- **Database**：one append-only migration for `pg_trgm`、`block_lexical_records` and indexes；update metadata/readiness/role
  projection and client-web generated database types through existing generators。
- **Browser**：add `@inkcre/core` lexical facade/Peer codec；replace the Start placeholder with InfoBaseListView and let that
  navigation host own its popup outlet。Selection continues through the bound stateless `InfoBaseRouter`，with no second
  navigation/history authority。
