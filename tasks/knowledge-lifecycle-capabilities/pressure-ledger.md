# Capability Pressure Ledger

这里追踪具体 unit 如何传导出横切架构压力，不把候选 core change 自动升级为决定。每项遵循：

`上游需求 → 被打破的假设 → 候选 owner → 影响 → evidence → status`

active unit 是 [Semantic retrieval](units/semantic-retrieval/packet.md)，当前处于 Design consolidation。下列 Memos
pressures 保留为已完成单元的 provenance，不自动成为 semantic retrieval 的设计前提；新 unit 的横切压力应从
其 user journey 与 acceptance evidence 重新建立。

## Active-unit pressures

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
