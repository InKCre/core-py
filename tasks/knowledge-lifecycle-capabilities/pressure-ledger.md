# Capability Pressure Ledger

这里追踪具体 unit 如何传导出横切架构压力，不把候选 core change 自动升级为决定。每项遵循：

`上游需求 → 被打破的假设 → 候选 owner → 影响 → evidence → status`

active unit 是 [Mail extension](units/mail-extension/packet.md)，当前处于 design closure。Mail 的横切压力
必须从其 user journey 与 acceptance evidence 重新建立；不能把协议 feature checklist 或旧实现缺口直接升级
为 MVP blocker。下列既有 pressures 保留为已完成 units 的 provenance，不自动成为 Mail 的设计前提。

## Active-unit pressures

### P-018 — Mail cannot be permanently modeled as a read-only collection adapter

- **Upstream**: Mail should retain a practically complete communication record and ultimately make InKCre a complete email
  client/agent。
- **Broken assumption**: a Mail extension can finish at IMAP ingestion，or any write to the remote mailbox is an accidental
  source-side effect。
- **Candidate owner**: Mail extension owns the product vertical；exact collection、remote-action、Agent、Peer and client-web
  boundaries must be earned by successive delivery scopes rather than forced into SourceBase。
- **Impact**: mailbox coverage、state synchronization、outbound commands、authorization/approval、graph/query semantics and
  client-web interaction can all become relevant。The terminal direction does not approve them all for this iteration。
- **Evidence**: current `mark_as_seen` is already an intentional configurable write-back；Sir selected complete
  communication records and a complete email client/agent as the terminal product direction。
- **Status**: D-200 confirms the terminal pressure；D-201 fixes the current communication-record foundation、configurable
  `mark_as_seen` and compose/reply/send deferral；D-202 fixes one-account-per-Source coverage and extension-owned default
  exclusions；D-203 adds Source override；D-204 fixes ordinary post-setup collection and explicit bounded history。
  Continuous-update semantics remain an open Product question。

### P-019 — Source history needs specialized `backfill` collect semantics rather than overloaded `full`

- **Upstream**: a Mail account may contain years of history，but Source creation should begin cheap forward collection and
  must not silently trigger an unbounded import。
- **Broken assumption**: one boolean `full` can express history range、reconciliation、replacement and source-specific
  traversal effects。
- **Candidate owner**: the Source domain may own collect as the umbrella ingress action and backfill as a specialized collect
  intent，while each Source/extension owns whether history exists and the shape of its ordinary/history boundaries。
- **Impact**: legacy Mail、RSS、GitHub and Twitter job configs use or expose `full` with non-identical behavior。A hard cut
  requires per-source audit and cannot be inferred from Mail alone。
- **Evidence**: D-074 already refused to promote `full`；D-204 establishes exact Mail product semantics。Files/calendar-like
  current-state Sources demonstrate why “created before setup” is not universally historical data。
- **Status**: D-205 confirms the common mental model；cross-source interface remains a pressure for Technical audit，not a
  program-wide code change authorized by this Product decision。

### P-020 — Reserve `enrichment` for Organization rather than source acquisition

- **Upstream**: Mail can expand a URL from an already collected email into a useful connected graph；RSS currently obtains
  linked full text while collecting feed information。
- **Broken assumption**: every additive fetch is “enrichment”，or the mechanical act of network fetching determines the
  domain owner。
- **Candidate owner**: enrichment classifies additive Organization behavior but does not own its implementation。The domain
  Resolver may own a deep materialization capability；Source/extension owns collection-time or delegated remote acquisition，
  while Storage/InfoBase retain bytes/graph mechanisms。
- **Impact**: RSS task/durable docs and code vocabulary currently use `full-text enrichment` for a source-owned behavior。
  Rename pressure must preserve behavior and authority rather than silently redesigning RSS。
- **Evidence**: D-206 fixes post-collection Mail URL expansion as the canonical enrichment example and retains RSS linked
  full-text work as source-owned acquisition。
- **Status**: D-206 reserves additive Organization meaning；D-207 removes redundant `source-owned collection` wording；D-215
  corrects classification versus implementation ownership。Apply owner-specific durable/code naming corrections with an
  implementation unit after blast-radius audit，not by rewriting completed-unit history during discussion。

### P-021 — Mailbox deletion is a scoped external fact，not default info-base deletion

- **Upstream**: a collected email can later disappear from one remote mailbox while remaining valuable in the info-base or
  present through another folder/label。
- **Broken assumption**: Mail must mirror remote deletion，or one missing listing proves global message deletion。
- **Candidate owner**: Mail Source collection records mailbox-scoped presence/deletion facts and decides whether to issue
  graph deletion；InfoBase persists the submitted graph commands without understanding Mail policy。
- **Impact**: incremental sync capabilities、folder/label identity、move detection、optional graph deletion and Source config。
- **Evidence**: D-208 fixes default retention and permits opt-in synchronized deletion only with trustworthy protocol-native
  incremental evidence，not full traversal/diff emulation。
- **Status**: D-209 fixes relation removal/no tombstone and corrects the owner；D-210 fixes Mailbox/Flag Block pressure。
  Protocol feasibility and exact predicates/state representation remain preflight/Technical questions。

### P-022 — Scheduled collection is job creation；Mail execution must not remain core-py-only

- **Upstream**: current core-py can run Mail collection，while a future background-capable native InKCre Peer may act as a
  higher-frequency mail client and browser Peers may remain incapable。
- **Broken assumption**: scheduled collection is a second execution path，or Source/Extension runtime permanently belongs to
  the Python server because it is implemented there first。
- **Candidate owner**: Source job contract owns collection commands/results；scheduling creates jobs。Extension/Peer runtime
  capability determines who can execute，without requiring every Peer to be symmetric。
- **Impact**: scheduler placement、job claiming、future Peer capability advertisement/routing、cadence configuration and
  duplicate creation may eventually interact。
- **Evidence**: D-211 confirms one collect-job semantic、current core-py execution and future multi-Peer direction。
- **Status**: Product/topology direction confirmed；no distributed scheduler or native-Peer implementation is authorized in
  the current scope without Technical evidence。

### P-023 — Collect jobs must not absorb Source-internal work-unit semantics

- **Upstream**: one Mail collection invocation can visit multiple mailboxes and persist useful messages despite a local
  mailbox/item failure。
- **Broken assumption**: generic job success means every source-native sub-scope was synchronized，or jobs must own each
  mailbox cursor、transaction and partial outcome。
- **Candidate owner**: collect job owns invocation/runtime status；Source owns its deep collection algorithm、state、partial
  progress and public completion semantics。
- **Impact**: Mail、RSS、GitHub、Twitter and future Sources must not shape generic job statuses around their private traversal
  units。Observability may carry detail without turning it into job-domain completeness。
- **Evidence**: D-212 fixes the CronJob analogy and withdraws the proposed mailbox-failure → job-failure rule。
- **Status**: D-212 confirms the shallow invocation boundary；D-213 fixes one-shot/no-retry lifecycle。Technical audit must
  check current job/source boundaries without assuming a broad job schema expansion。

### P-024 — Mail attachment bytes become Organization enrichment after metadata-only collection

- **Upstream**: Mail collection can preserve attachment identity/metadata without eagerly downloading every MIME part；later
  use may justify durable local content。
- **Broken assumption**: a complete communication record or credible email client must persist all attachment bytes during
  collection，or every later attachment fetch still belongs to Source collection。
- **Candidate owner**: Mail collection owns attachment metadata/remote reference；Mail Resolver owns the materialization
  capability and may delegate remote acquisition to Source/extension；the resulting additive graph change can be classified
  as Organization enrichment。Use may perform transient fetch/stream without persistence。
- **Impact**: Mail canonical graph、authenticated part access、Storage、semantic content Resolver、Organization tools and
  client-web attachment behavior。
- **Evidence**: IMAP4rev2 selective fetch plus official Apple/Gmail configurable/lazy behavior；D-214 owns the product
  inference and the unit evidence file retains links。
- **Status**: D-215 corrects the owner topology；D-216 fixes textual body versus lazy non-text inline parts。Exact technical
  interfaces remain open。

### P-025 — Native Mail references and inferred linking have different owners

- **Upstream**: reply/reference headers can identify directed Email relationships，while missing targets or incomplete
  headers may tempt subject/time heuristics。
- **Broken assumption**: collection should create a generic Thread entity or infer every plausible conversation edge to make
  the graph useful。
- **Candidate owner**: Mail collection owns source-native reply/reference facts；Organization linking owns additive inferred
  relations over the existing graph。Use derives thread views from graph structure。
- **Impact**: Email canonical content、relation vocabulary、unresolved external references、later reconciliation、query and
  client-web thread navigation。
- **Evidence**: D-217 fixes native directed relations、no generic Thread Block and no collection-time inference。
- **Status**: Product boundary confirmed；unresolved-reference representation and exact relation grammar remain Technical。

### P-026 — Extension-specific Block rendering must not become an extension-specific browsing product

- **Upstream**: client-web must render rich Email content，but InKCre's Mail value is not yet expressed as a traditional
  inbox/folder/list workflow。
- **Broken assumption**: a rich source type requires a dedicated page and source-specific query UI，or a complete email
  client/agent direction implies copying ordinary email client information architecture。
- **Candidate owner**: Mail client-web extension owns Email Resolver/renderer；GraphSurface owns Block placement、selection
  and cross-Block navigation。Generic query owns any future cross-type query behavior。
- **Impact**: extension Module Federation artifact、Resolver registration、BlockContent/detail/graph surfaces and query UI。
- **Evidence**: D-218 plus current Twitter `TweetResolver.contentComp` → generic `BlockContent` implementation path。
- **Status**: Product boundary confirmed；D-219 closes the predefined-query edge，while exact Email renderer remains a
  Technical design question。

### P-027 — `contentComp` obscures solved-content presentation

- **Upstream**: an Email requires root content plus participants、mailbox/flag/reply Relations and attachment metadata to
  render；Tweet already loads attachment Relations and Blocks before rendering。
- **Broken assumption**: a Resolver component only renders the literal `Block.content` column，or UI components should query
  and reconstruct graph semantics themselves。
- **Candidate owner**: client-web Resolver owns focal-Block solved projection and registers its `SolvedContentRenderer`；a
  generic controller owns Resolver/view lifecycle。GraphSurface alone owns target transitions；`BlockInspector` owns only
  persistence facts and current-Block commands such as view content/rumination。
- **Impact**: `ResolverClass.contentComp`、`ContentCompProps`、`BlockContent`、`BlockDetailsPanel`/unused `relations` prop、
  Tweet solved type、future Email renderer、loading/error/refresh and navigation context。
- **Evidence**: D-220 and current Twitter resolver/component/BlockContent code path。
- **Status**: `SolvedContentRenderer`、`BlockInspectorPopup`、view-solved-content meaning and GraphSurface route realization
  confirmed；generic render context withdrawn。First-class `SolvedContentPopup`/InfoBaseRouter and complete
  Resolver + typed solved-content props are confirmed。D-226 corrects GraphSurface to current realizer rather than route；
  `overview` is accepted，while focal route shape/operations and Vue Router adapter remain Technical。

### P-028 — Mail does not justify generic query work without a reachability blocker

- **Upstream**: Mail needs generic rendering/use but its distinct query workflow is not yet understood。
- **Broken assumption**: every rich source unit must add source-specific browsing/filters or opportunistically expand generic
  query APIs。
- **Candidate owner**: preflight proves reachability through current generic surfaces；only a real blocker can pressure generic
  info-base query ownership。
- **Impact**: client-web graph/start surfaces、feature retrieval、query APIs and unit scope。
- **Evidence**: D-219 explicitly accepts no preplanned increment and a minimal blocker-driven exception。
- **Status**: confirmed scope guardrail；no query implementation is currently approved。

### P-029 — Resolver identity selects Block behavior；hydration and solving are different layers

- **Upstream**: Mail/Tweet rendering requires a focal Block's own payload plus local graph context，while the current
  `contentComp` interface suggests literal column rendering and current solved models inconsistently call the canonical
  focal value `canonical`、`root` or a repeated domain noun。
- **Broken assumption**: `block.resolver` is only a decoder/display type，hydrated content and solved content are synonyms，
  or a graph-derived projection may silently mutate/impersonate canonical root content。
- **Candidate owner**: shared PRD glossary owns product meaning；Product TDD owns exact Block → Resolver behavior selection
  and content-layer topology；client-web local architecture owns `BlockRenderer` and its host navigation contract。
- **Impact**: Python/TypeScript Resolver contracts、solved models、Tweet/Mail renderers、generic BlockContent/details/graph
  surfaces、refresh caching and durable documentation vocabulary。
- **Evidence**: D-221 plus current `TweetResolver` graph lookup、`MemoResolver`/RSS graph-aware solved projections and the
  existing shared hydration/Resolver contract。
- **Status**: behavior/content boundary、`SolvedContentRenderer`、`BlockInspectorPopup`、`.root` and surface-independent
  InfoBase view/router topology confirmed；exact focal route/adapter mechanics remain Technical。

### P-030 — Container ownership changes when its lifecycle becomes route-destination behavior

- **Upstream**: GraphSurface/ListSurface must host addressable Block-inspection and solved-content destinations without
  duplicating close/back logic or teaching presentation-neutral resolver content about client navigation。
- **Broken assumption**: every container must be assembled by the parent regardless of behavior，or any component may wrap
  itself merely because it currently appears in one Popup。
- **Candidate owner**: shared Product TDD owns the general container/content rule and exact exception criterion；client-web
  local architecture owns `InfoBaseView` navigation host、route destination outlet、`BlockInspectorPopup` and
  `SolvedContentPopup` composition。
- **Impact**: GraphSurface/ListSurface responsibilities、Popup ownership、route/back semantics、component naming、Resolver
  renderer portability and later UI implementation guidance。
- **Evidence**: D-235 establishes popup/back behavior；D-236 identifies presentation-neutral content、navigation host and
  route destination outlet as the stable explanatory model。
- **Status**: Technical vocabulary and ownership confirmed for implementation。Promote to Product TDD after evidence；a UI
  agent skill should later derive from durable truth，but its build/delivery infrastructure is explicitly outside this unit。

## Carried cross-unit pressures

### P-017 — Secret-safe observability is a shared boundary，not an adapter-by-adapter assertion

- **Upstream**: a real AI provider failure rendered dialect configuration in an exception path and exposed a plaintext
  credential。
- **Broken assumption**: marking one runtime field secret or testing its `repr` proves that logs、tracebacks、structured
  events and diagnostics cannot disclose secrets。
- **Candidate owner**: future shared observability/error-reporting infrastructure should define sanitization at its
  ingestion/rendering boundary；typed secret config remains the local producer-side baseline。
- **Impact**: AI、Source、Storage、Extension and deployment diagnostics can all carry database-owned credentials。
- **Evidence**: Pydantic `SecretStr` repairs ordinary model representation for the AI dialect，but an adapter-level test
  would only repeat Pydantic behavior and would not exercise any repository-wide observability path。
- **Status**: D-197 removes the false local proof and records the cross-cutting pressure。No observability subsystem is
  introduced by the semantic-retrieval unit。

### P-001 — Canonical content requires a decoder-generation contract

- **Upstream**: CanonicalMemo 直接持久化为 `block.content`，而 shape 未来可能演化。
- **Broken assumption**: resolver identifier 可以解释所有历史 content，但 registry 没有明确的
  generation retention / unknown-generation contract。
- **Candidate owner**: block resolver identity 选择 exact decoder；extension/resolver registry
  保留 live generations。
- **Impact**: backend write/read、migration、client-web parity、extension unload。
- **Evidence**: GitHubRepo、FeedItem、Tweet 等 JSON block contents 已有同类无版本压力；当前
  registry 只按 exact resolver string 发现实现。
- **Status**: D-026 已确认 versioned resolver identity，不在 payload 或 block column 重复
  version；retention 与 explicit failure 等待 Technical gate/preflight。

### P-003 — Persistence time is not memo-authored time

- **Upstream**: backend 必须 round-trip memo create/update time；future collector 还会导入历史
  memo。
- **Broken assumption**: block `created_at / updated_at` 可以同时代表 row persistence 与用户
  authored/source time。
- **Candidate owner**: CanonicalMemo root facts；block timestamps 继续只属于 persistence row。
- **Impact**: chronological retrieval、display、update response、future reconciliation。
- **Evidence**: BlockModel timestamps 由 insert/update 产生；GitHubRepo、FeedItem、Email 也另存
  source times。
- **Status**: D-032/D-042 confirm authority and exact CanonicalMemo v1 serialization。

### P-004 — Compatible backend reads need a semantic boundary

- **Upstream**: memo 客户端 write 后会 list/sync/read native resources。
- **Broken assumption**: backend 只需 collection endpoint，或 API adapter 可以直接解释 graph
  rows。
- **Candidate owner**: memo resolver owns graph → solved memo；generation adapter owns solved memo
  → native response。
- **Impact**: resolver output、API adapter、client compatibility、acceptance fixtures。
- **Evidence**: D-021/D-023；当前 Resolver 已承担 raw content + local relations 的联合解释。
- **Status**: ownership、D-042 root facts and D-047 exact native fixtures confirmed。

### P-005 — Graph-owned components must not be copied into root content

- **Upstream**: attachments、comments、parent 与 references 必须可独立保存、解析和更新。
- **Broken assumption**: 为 adapter 方便，可以同时把同一 component reference 放进 serialized
  root content 和 relations。
- **Candidate owner**: root CanonicalMemo 只持 root facts；component blocks/relations 持结构。
- **Impact**: mutation、resolver、native response、organization。
- **Evidence**: attachment 需要独立 storage；comment 是完整 memo；references 有独立 graph
  identity/use value。
- **Status**: D-012/D-013/D-017/D-022/D-044 confirmed。

### P-008 — Protocol user identity is not a core User

- **Upstream**: MoeMemos startup 需要 current user、GENERAL settings、Bearer token 和
  creator-scoped sync。
- **Broken assumption**: InKCre JWT / `ClientModel` 可以直接表示终端 memo user。
- **Candidate owner**: deployment-scoped memo backend configuration 投影一个 profile/settings；
  Memos extension ordinary config owns the credential（D-039）。
- **Impact**: auth、ownership、visibility/ACL、migrations、Hub、client-web administration。
- **Evidence**: current JWT authenticates peer claims；ClientModel 是 peer deployment；block /
  relation/source 没有 terminal-user owner。
- **Status**: D-033/D-039/D-047 confirmed。Profile/settings/credential/wire fixtures are closed。

### P-009 — Native mutation needs explicit coordination without completeness guarantees

- **Upstream**: create/update/delete memo 可能同时改变 root、attachments、comments、relations
  和 raw storage；客户端成功必须代表全部已持久化。
- **Broken assumption**: 多个各自 commit 的 convenience write paths 可以在没有 coordinator 的情况
  下自然表达 primary success、component order 与 cleanup。
- **Candidate owner**: memo application service coordinates graph/storage commands；D-041 explicitly
  rejects graph completeness as an observable guarantee。
- **Impact**: idempotency、owned deletion、storage residue、HTTP success and diagnosis。
- **Evidence**: current convenience create paths independently commit；relation FK cascade 不删除
  component blocks/raw storage。
- **Status**: D-041 closes failure completeness；D-046 closes minimum owned cleanup。

### P-010 — Namespaced extension routing is sufficient (resolved)

- **Upstream**: MoeMemos 2.0.4 accepts a user-provided host and declares `api/v1/...` as relative
  Retrofit paths；attachment URLs append `file/...` to that same host path。
- **Assumption tested**: API annotations containing `api/v1` do **not** imply that the backend must own
  server-root `/api/v1`。With base URL `https://<deployment>/memos/`, they resolve under the existing
  Memos extension namespace。
- **Owner**: current `ExtensionBase` `/{extension_id}` router remains the route owner；Memos adapter owns
  its relative protocol paths。
- **Impact**: no top-level mount/alias or external-protocol route registry。Existing duplicate-start、
  ineffective-close and post-disable reachability remain lifecycle defects, not a reason to change path
  ownership。
- **Evidence**: released client login normalization preserves the supplied path；V1 annotations have no
  leading slash；resource URI construction appends to the stored host。
- **Status**: resolved；O-017 withdrawn。D-036/D-039 assign peer and Memos authentication to composed
  route dependencies；the global middleware limitation is now an implementation pressure。

### P-011 — Memos PAT follows the current extension-config trust boundary

- **Upstream**: single-user MoeMemos needs a long-lived/revocable Bearer credential distinct from
  InKCre peer JWT。
- **Broken assumption**: upstream Memos' hashed multi-user PAT storage must be copied even though InKCre
  currently persists and returns other recoverable credentials through ordinary config。
- **Candidate owner**: Memos extension config owns the deployment-scoped credential；
  core/default-extension routes own peer-auth dependencies。Existing extension config surface owns
  peer-authorized setup/change/clear commands。
- **Impact**: token setup/read/rotation/revocation、config validation/update ordering、middleware error
  behavior、operator setup。
- **Evidence**: JWT middleware rejects non-peer tokens before handlers；extension config is JSONB，is
  returned by extension APIs and already includes Twitter/Telegram/IMAP/GitHub credentials。
- **Status**: D-039 confirms ordinary raw-PAT config persistence、exact public detection、immediate
  replacement/revocation and validated generic update ordering；D-036/D-037 own route composition and
  lifetime。No O-018 design remains open。
  D-033 continues to prohibit introducing core User/tenant ownership。

### P-012 — Memos attachments require writable raw storage

- **Upstream**: selected client journey requires attachment create/list/delete and authenticated raw
  download。
- **Broken assumption**: `Storage.get_raw_content()` plus remote-URL implementations are sufficient for
  all collected raw content。
- **Owner**: D-043：graph component owns attachment identity/role/metadata；a PostgreSQL BYTEA-backed
  generic storage owns only the pointer + raw bytes。
- **Impact**: storage interface/backend、schema/migration if needed、file serving、validation、graph +
  external side-effect failure/compensation。
- **Evidence**: no storage put/delete API, upload/file response route, multipart dependency or local raw
  backend exists。
- **Status**: D-043 confirmed one small DB raw table；filesystem compensation and inline graph base64 are
  excluded。D-041 means shared DB transactionality is available but not a product guarantee。

### P-013 — Native sync requires an addressable query contract

- **Upstream**: MoeMemos requests NORMAL and ARCHIVED lists with creator filter, stable ordering,
  `pageSize=200` and page tokens。
- **Broken assumption**: recent blocks by resolver is equivalent to a protocol list/query projection。
- **Candidate owner**: memo extension query repository consumes canonical/graph authority and exposes
  adapter-ready pages；a derived projection/index is optional application support, never a second memo
  authority。
- **Impact**: D-042 fact ownership、cursor stability、query performance、conditional migrations and
  client-web database projection。
- **Evidence**: current `BlockManager.get_recent` only filters resolver and limits rows；state/visibility/
  pinned owner remains open。
- **Status**: D-042 resolved the fact owner；do not add a memo table/index preemptively。

### P-014 — Route topology is not automatically a hot extension lifecycle

- **Upstream**: core-py and client-web currently expose same-process extension enable/disable intent；
  Memos backend would inherit that behavior if accepted。
- **Broken assumption**: `include_router()` route composition can be paired with a symmetric close/
  disable operation, or leaving routes installed behind per-request running guards is complexity-free。
- **Owner**: D-038 assigns same-process route availability to `ExtensionManager`。One retained
  extension-owned router/route-set handle bounds direct add/remove and prevents duplicate registration。
- **Impact**: core-py ExtensionManager、client-web enable/disable UX、OpenAPI、auth ownership、resource
  shutdown and deployment restart semantics。
- **Evidence**: core-py dynamically includes routes but never removes them；client-web remote enable/
  disable calls expect immediate activation/deactivation。Pinned FastAPI 0.139.2 retains included child
  routers and versions effective-route/OpenAPI caches，so a localized child route-set mutation is viable；
  current deployment is one web process/replica。
- **Status**: D-038 accepted direct route mutation for this project's risk profile。Do not add scattered
  running dependencies、request-drain generations or an isolated dispatcher in the MVP；reopen only if
  deployment concurrency or extension resource lifetime makes the low-cost contract false。

### P-015 — Config update is a shared operation，not an extension-specific workaround

- **Upstream**: Memos needs validated、atomic-as-observed config replacement while running；extension、
  source、storage and future configurable owners share the broad operation。
- **Broken assumption**: persisting an unvalidated dict and validating only when applying runtime state is
  an acceptable update order，or every owner should implement its own update pipeline。
- **Candidate owner**: a generic config-update operation owns merge → `config_cls` validation → durable
  write → live apply ordering；each target manager still owns address resolution、persistence and
  reconfiguration consequences。
- **Impact**: extension MVP implementation now；source/storage APIs and lifecycle only after their current
  paths are explored。This is not evidence for a generic hook registry or a universal config table。
- **Evidence**: ExtensionBase、SourceBase and StorageBase already declare typed `config_cls` seams，while
  current extension update commits raw input before runtime validation。
- **Status**: direction accepted by Sir；exact reusable interface and non-extension adoption remain a
  later technical design item。D-039 fixes the extension-first ordering；Memos must not preemptively invent
  unverified source/storage lifecycle。

### P-016 — Memos proves ordered and pre-memo attachment states

- **Upstream**: Memos 0.29.1 deliberately returns attachments in request order；MoeMemos may upload them
  with `memo=null` before creating the memo。
- **Broken assumption**: attachment order has no current source pressure，or every successful upload is
  already part of a memo graph transaction。
- **Owner**: D-040/D-044 make order and grammar extension-owned。D-043 owns raw storage；D-046 owns
  minimum cleanup semantics。
- **Impact**: relation payload、PATCH set semantics、orphan list/delete、failure residue and acceptance
  wording。
- **Evidence**: tagged server reverses the requested list and rewrites `updated_ts` before ordered reads；
  tagged MoeMemos uploads resources before memo create and sends nullable `memo` in streaming JSON。
- **Status**: D-040/D-043/D-044/D-046 confirmed。

## Deferred future-unit pressures

### P-002 — Collector reconciliation needs external identity

- **Future upstream**: scan/webhook/update/delete 要命中同一 external memo。
- **Pressure**: `block.id` 只表达 local identity；默认 `(resolver, content)` equality 不是稳定
  external identity。
- **Direction**: resolver-owned CanonicalMemo 可保存可靠 provenance/identity facts，按 stable
  external scope → local `source_id` fallback 的梯度做 best-effort exact match；不建 generic
  source binding table，不做 content/time fuzzy overwrite。
- **Status**: D-027/D-028 direction confirmed；collector deferred，不参与当前 v1 backend gate。

### P-006 — A family body representation cannot copy every product protocol

- **Future upstream**: Memos 使用 Markdown，flomo 或其他 memo products 可能有不同 authored
  representation/fidelity。
- **Pressure**: 直接复制某一产品 shape 会污染 canonical；开放 `format + arbitrary payload`
  又把分支成本扩散到 resolver/use。
- **Direction**: product-generation adapter 负责 normalize；canonical generation 固定其 body
  representation。真实 fidelity failure 再推动新 generation 或 component graph。
- **Status**: Canonical v1 当前采用 Markdown semantic minimum；flomo 已延期，不能驱动当前
  wire 扩张。

### P-007 — External ID needs its native uniqueness scope

- **Future upstream**: source 重建、重复配置或 instance locator 变化后仍希望识别同一 memo。
- **Pressure**: `source_id` 不是 external provenance truth，mutable URL/username 也不能冒充
  immutable namespace。
- **Direction**: 只使用产品能证明的 stable scope；没有时接受 local best-effort scope，匹配
  不足宁可产生 duplicate，再由 organization 改善 use。
- **Status**: policy confirmed；Memos 0.30 evidence 仅为 research，backend MVP 自己是 memo
  authority，不需要 cross-system reconciliation。
