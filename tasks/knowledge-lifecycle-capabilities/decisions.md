# Decision Register

> Task-state decision memory. Hub and code remain the final owners after promotion.

## Index

| Cluster | Decisions |
| --- | --- |
| Program boundaries | D-001–D-007, D-033 |
| Memo-like product and graph role | D-008–D-018 |
| CanonicalMemo, resolver, identity and time | D-019–D-028, D-032 |
| Memos extension and current MVP delivery | D-029–D-031, D-034–D-048 |
| RSS extension rewrite, propagated common contracts and close | D-049–D-078 |
| Active Technical question | None；next implementable unit not selected |

## Confirmed

### D-001 — Program trunks

- **Decision**: 本任务以收集、整理、应用三组能力及其纵向切片为主线。
- **Implication**: 术语、info-base 联合模型、extension / registry 与跨仓边界都是横切合同，
  不能取代能力主线。
- **Confidence**: Sir confirmed。

### D-002 — Actions, not states

- **Decision**: collection、organization、use 是对信息执行的动作，不是信息状态。
- **Implication**: 不建立未经需求证明的信息生命周期。
- **Confidence**: Sir confirmed。

### D-003 — Collection persistence model

- **Decision**: Tweet、GithubRepo、FeedItem 等是 source-specific 输入形状；collection 通过
  持久化 blocks / relations 完成收集，不引入通用采集对象或并列 source object store。
- **Implication**: graph 映射、identity 与更新语义按 source slice 讨论。
- **Confidence**: Sir confirmed and code-aligned。

### D-004 — Joint information semantics

- **Decision**: block 是基本持久信息单元，但其可用含义不由 block row 单独决定；resolver
  联合解释 raw content 与 local relations，storage 只在需要时取得 raw content。
- **Implication**: collection、organization、application 的设计都必须明确消费或产生哪种表示。
- **Confidence**: Sir confirmed and code/history-aligned。

### D-005 — Organization goal and open capability set

- **Decision**: organization 为 use 优化 info-base；breakdown、merge、linking 是已知能力，
  不是完备枚举。
- **Implication**: 允许从真实 use 场景发现其他 organization 能力，但不得无目标扩张。
- **Confidence**: Sir confirmed。

### D-006 — Indexing boundary

- **Decision**: indexing 不属于 organization；它只作为 application / retrieval 的支撑。
- **Confidence**: Sir confirmed。

### D-007 — Existing truth is fallible

- **Decision**: 现有 Hub、代码和 Sir 的判断都需要交叉验证；Hub 是获批稳定真相的最终归属，
  不是讨论中无需核验的前提。
- **Confidence**: Sir confirmed。

### D-008 — memo-like product role

- **Decision**: memo-like 指低摩擦收集用户想法、周围事物与零碎信息的多端应用类别；它是
  InKCre 的重要 collection surface，但不承担 info-base 的查阅或使用。
- **Implication**: 本切片的产品价值首先是随时随地可靠收集，不能把 InKCre 的 use 能力
  偷渡进 memo 客户端范围。
- **Confidence**: Sir confirmed；flomo 官方产品描述与该类别相符。

### D-009 — Productized memo integrations

- **Decision**: InKCre 不依赖不存在的通用 memo 协议，而是通过 core extensions 支持多款
  有代表性的 memo 产品；Memos 是已确认代表。
- **Implication**: 各产品可有独立 access 与 graph mapping；只有重复压力才提升为公共
  extension / registry 合同。
- **Confidence**: Sir confirmed；现有 extension 边界与方案方向相容，承载能力待 Technical
  阶段验证。

### D-010 — Dual memo integration relationship

- **Decision**: memo extension 同时支持 InKCre 作为 memo backend，以及 InKCre 从既有
  memo 服务进行 collection；两种关系都汇入 extension 的 collection boundary，再持久化
  到 info-base。
- **Implication**: 两条路径共享后半段 collection 语义，但各自保留独立的接入、身份、
  变更与失败合同，不能用一个含混的“同步”合同覆盖。
- **Confidence**: Sir confirmed。

### D-011 — Collection success from the user perspective

- **Decision**: backend 路径中，memo 客户端显示保存成功即代表该 memo 已被 InKCre
  持久化到 info-base；collector 路径的可达能力和成功确认依赖目标产品提供的 export /
  automatic-backup API。
- **Implication**: backend endpoint 不能在 graph 持久化完成前返回成功；collector 的详细
  成功、部分成功和可见性语义仍需按产品讨论。
- **Confidence**: Sir confirmed；事务边界与各平台接口能力待 Technical / Acceptance
  阶段验证。

### D-012 — Memo graph boundary

- **Decision**: 每个 memo 默认有一个承载 memo identity 与主要文本的根 block；图片和其他
  附件在需要独立 storage / resolution / use 时成为 component blocks，并通过 relation
  保留角色。只有来源本身提供可独立寻址的正文片段时，才继续拆分 text blocks。
- **Implication**: 是否拆 block 由独立身份和使用价值决定，不由 MIME type 机械决定；
  附件顺序没有被证明是 memo 的通用 graph 语义。
- **Confidence**: Sir confirmed；relation payload contract remains open。

### D-013 — Attachment association is unordered by default

- **Decision**: memo attachment relations 默认为无序关联。若正文显式引用附件，正文是位置语义
  的唯一 authority；只有来源明确把附件顺序定义为稳定语义时，extension 才另行保留。
- **Implication**: memo 不使用 `attachment:<order>` 作为通用合同，也不因附件排序单独推动
  relation schema 变化。
- **Confidence**: Sir confirmed the default rule。Memos 0.29.1 preflight later proved a product-specific
  exception：its request order is deliberately persisted and returned，see D-040。

### D-014 — Durable documentation changes are accumulated

- **Decision**: 讨论中产生的稳定结论、新架构理解和待纠正文档先记录在 task packet 的
  `documentation-promotion.md`，不逐次修改 durable docs；形成内聚批次后再统一审查和应用。
- **Implication**: “统一应用”指一个协调的 promotion batch，不改变 Hub source、Spoke
  shared-ref 与 Spoke-local docs 必须按 owner 分离操作的规则。
- **Confidence**: Sir confirmed。

### D-015 — Memos is the first reference product

- **Decision**: 首个 memo → graph mapping 以 Memos 为 reference product。
- **Implication**: 当前先由 Memos extension backend MVP 的真实 native shape 检验
  canonical/graph/read
  边界；未来 collector 作为独立 unit 再检验 reconciliation。只有重复压力才提升为通用
  memo extension 合同，不以不存在的通用 memo schema 起步。
- **Confidence**: Sir confirmed and official API evidence available。

### D-016 — Memos compatibility starts at the current API era

- **Decision**: 不支持旧历史版本；实现只面向最新版本，或最近一次 breaking change 之后的
  当前 API generation。方案必须预留未来 breaking generations 的多版本适配能力，不能把
  当前 shape 假设为永久合同。
- **Implication**: 首版精确 target 已由 D-031 固定为 0.29.1；0.27–0.28 与 0.30 只作为
  compatibility/research evidence。未来 adapter retirement policy 仍需在出现第二代时确定。
- **Confidence**: Sir confirmed at policy level。

### D-017 — Comments are independently collected memos

- **Decision**: Memos comment 从首版开始完整收集为独立 memo block，并以 relation 连接
  parent；它复用 memo 的 graph mapping，不扁平化进 parent content。
- **Implication**: 当前 backend 必须以独立 comment fixture 覆盖 create/read/change/delete；
  future collector 若采集 comments，也复用同一 graph semantics。parent lifecycle 不能导致
  comment graph 静默丢失或残留。
- **Confidence**: Sir confirmed and Memos native model aligned。

### D-018 — Current-generation adapter policy

- **Decision**: 每个 memo product adapter 支持当前 API generation；breaking release 产生新
  adapter，新旧 generation 可在迁移期短期并存，旧 adapter 不永久保留。`latest`
  main-branch schema 不等于 released wire contract。
- **Implication**: backend 只暴露其配置声明的 released generation，当前为 0.29.1；future
  collector 必须识别 product generation 并拒绝 unsupported generation。
- **Confidence**: Sir confirmed。

### D-019 — CanonicalMemo is the memo-family semantic boundary

- **Decision**: memo extension 由 product-specific、generation-specific adapters 将 Memos /
  flomo 等 native shapes 转换为 `CanonicalMemo`，再由 canonical mapping 写入 info-base
  graph；任何单一产品的 shape 都不能直接成为 memo extension 的核心模型。
- **Implication**: `CanonicalMemo` 只覆盖 memo-like 产品族，不是系统级 collected object，
  也不形成与 block / relation graph 并列的 durable store。
- **Confidence**: Sir confirmed at topology level；persistence/version boundary 已由 D-020/D-026
  关闭，exact v1 wire later closed by D-042。

### D-020 — CanonicalMemo is persisted in root block content

- **Decision**: `CanonicalMemo` 的序列化表示直接存入 memo root block 的 `content`；它不是
  只在 adapter / mapper 间存在的 transient model。resolver 读取 CanonicalMemo content，
  并联合 local relations 解释 attachments、parent、references 等 graph context。
- **Implication**: CanonicalMemo 是 durable、versioned content contract，但仍属于
  block / relation graph，不构成与 info-base 并列的 object store。
- **Confidence**: Sir confirmed。

### D-021 — Backend implements a minimal compatible API

- **Decision**: InKCre-as-backend 除 collection/write endpoints 外，还实现目标客户端正常
  工作所需的 read endpoints；只支持经过验证的最小兼容子集，不复刻完整产品 backend。
- **Implication**: endpoint scope 必须从目标 client journey 与实际调用证据得出；adapter
  需要 native request → CanonicalMemo，也需要 graph / CanonicalMemo → native response。
- **Confidence**: Sir confirmed at product-policy level。

### D-022 — Canonical content excludes graph-owned components

- **Decision**: CanonicalMemo content 排除 attachments、parent 与 memo references；这些具有
  独立 identity 或 graph value 的信息只由 blocks / relations 表达。
- **Implication**: 这是 canonical-content / graph 的通用 authority pattern；resolver
  联合 root content 与 relations 解释完整 memo，禁止重复持久同一事实。
- **Confidence**: Sir confirmed。

### D-023 — Backend reads are resolver-mediated

- **Decision**: product backend read adapter 不直接读取和解释 block / relation rows；它通过
  memo resolver 获取 graph 的 solved result，再转换为 product-native response。
- **Implication**: resolver 是 graph → memo semantics 的 owner，adapter 是 memo semantics
  → product protocol 的 owner。
- **Confidence**: Sir confirmed。

### D-024 — Concrete capability pressure may evolve core contracts

- **Decision**: 讨论从 memo-like、Apple Notes 等具体上游需求出发；当它们暴露 info-base、
  collection、organization、use 或 extension 的缺口时，显式记录传导链并允许系统合同演进。
- **Implication**: 不把现有 core 当作不可变前提，也不把尚未由具体压力证明的横切抽象提前
  升级为主线。
- **Confidence**: Sir confirmed。

### D-025 — Local memo identity is the block ID

- **Decision**: 在 InKCre info-base 内，memo 的 local identity 使用 `block.id`，不在
  CanonicalMemo content 中复制一个 canonical `id`。
- **Implication**: source-native identity 可以帮助 resolver 匹配已有 block，但它不取代
  `block.id` 作为 info-base local identity。
- **Confidence**: Sir confirmed for local identity。

### D-026 — Canonical content generation is selected by resolver identity

- **Decision**: CanonicalMemo payload 不携带 schema version；memo root block 通过 versioned
  resolver identity 绑定 exact canonical decoder。新的 product API generation 不自动产生
  新 canonical generation，新的 canonical shape 才产生新的 resolver identity。
- **Implication**: registry 必须保留仍被已持久 blocks 引用的 decoder generations；未知
  resolver identity 必须明确失败，不能猜测、fallback 或把新 decoder 用于旧 content。
  当前不增加 `BlockModel.content_schema_version`。
- **Confidence**: Sir confirmed the recommendation；current core-py / client-web registries have
  implementation gaps to address later。

### D-027 — Resolver-owned, best-effort cross-system consistency

- **Decision**: 不建立通用 source binding table。source-native provenance / identity 在对 use
  或精确 reconciliation 有价值时持久到 resolver-owned `block.content`；future memo
  collector 中即 CanonicalMemo。resolver 基于这些事实尽可能匹配已有 block。
- **Consistency boundary**: 不追求低 ROI 的跨系统全局一致性。无法可靠匹配而产生的
  duplicate、revision fork 或 weak link 进入已有 info-base 后，由 organization 通过
  merge / linking / 其他能力优化 use 效果。
- **Safety invariant**: resolver 不确定时宁可产生可整理的重复，不得模糊命中并覆盖
  错误 block。organization 只处理已有 info-base 的后果，不得把 collection 失败
  伪装成成功。
- **Confidence**: Sir confirmed the ROI / responsibility direction；exact CanonicalMemo fields and
  resolver matching contract remain open。

### D-028 — Source ID is an acceptable reconciliation-scope fallback

- **Decision**: reconciliation 优先采用 source-native memo ID 及其稳定 external namespace；
  产品不提供稳定 instance identity 时，允许使用 InKCre `source_id` 作为本地 best-effort
  namespace。future Memos collector 因此可以使用 source ID + instance-wide memo UID 精确
  匹配；当前 backend 自己是 memo authority，不需要这层 mapping。
- **Semantic limit**: source ID 不是 external provenance truth，也不承诺 source 被重建、合并
  或重复配置后仍能识别同一外部 memo。可用的 instance locator 仍可作为 provenance /
  diagnosis fact 持久化，但不能被描述成 immutable instance ID。
- **Failure rule**: scope 失效时允许 duplicate / fork 并交给 organization 改善 use；禁止以
  content、时间或 mutable username 做 fuzzy overwrite。
- **Confidence**: Sir confirmed source-ID fallback and best-effort exact identity。

### D-029 — memo-like delivery is backend-first

- **Decision**: `memos-extension` 的首个 MVP delivery scope 是 Memos-compatible backend；
  collector 延期为同一 extension 的 future scope。backend MVP 只实现选定 released
  generation 的最小 API subset，MoeMemos 是首个 compatibility acceptance client，而不是
  API authority。
- **Implication**: “minimum API”由 upstream Memos contract 与 MoeMemos 真实调用的交集界定；
  不复刻完整 Memos server，也不实现 client-private protocol。flomo 与 collectors 均不属于
  backend MVP，但不因此被建模为另一个 extension ownership unit。
- **Confidence**: Sir confirmed product priority, MoeMemos target, and deferral of flomo/collectors。

### D-030 — flomo backend is deferred

- **Decision**: `FlowMo` 已校正为 `flomo / 浮墨笔记`。公开产品合同没有显示官方 flomo 客户端
  支持 custom backend；在不存在可使用客户端/protocol 的情况下，本任务不实现 flomo-like
  backend。
- **Implication**: flomo 不再驱动当前 CanonicalMemo/API scope；未来只有发现受支持的
  replaceable-backend path、独立兼容客户端，或启动 collector task 时才重开。
- **Confidence**: Sir confirmed deferral if backend path is unavailable；official docs support the
  feasibility finding。

### D-031 — First Memos backend generation is 0.29.1

- **Decision**: 首版 Memos-compatible backend 以 released Memos 0.29.1 API generation 为
  protocol target，MoeMemos 2.0.4 为首个 compatibility acceptance client；不支持更旧
  historical generations。
- **Implication**: v0.30 native shape research 仍可检验 canonical semantics，但不能直接成为
  首版 wire contract。MoeMemos 后续支持 v0.30 时，通过 generation adapter 演进，不在首版
  同时实现两代。
- **Confidence**: Sir confirmed。

### D-032 — Memo-authored time is not block persistence time

- **Decision**: block `created_at / updated_at` 只描述 info-base row persistence；CanonicalMemo
  semantic minimum 使用 nullable、timezone-aware `created_at / updated_at` 表达 memo-side
  authored/source times。
- **Implication**: backend 按 memo service contract 建立这些时间；future collector 在来源没有
  可信时间时保持 null，不能用 collection time、block time 或运行机器 timezone 猜测填补。
- **Confidence**: Sir confirmed the authority distinction；exact v1 serialization/default behavior
  later closed by D-042。

### D-033 — Deployment is the product user/owner scope

- **Decision**: 当前 InKCre 产品不建立 deployment 内的 terminal-user、tenant 或 per-user
  ownership/ACL domain model；一个 deployment 表达单一 user/owner context。多个
  `ClientModel` 是围绕同一 info-base 的 runtime peers，不是多个人类用户。
- **External identity boundary**: source account、external author 或兼容协议中的 `user` 可以是
  configuration、provenance 或 wire projection，但不会自动升级为 InKCre core User。
- **Memos realization**: backend 投影一个 deployment-scoped Memos-compatible profile/settings；
  memo rows 不增加 user/tenant owner，也不复用 `ClientModel` 表示人。Bearer credential 的
  exact contract later closed by D-039/D-047。
- **Evolution rule**: future multi-user support 若出现，必须作为显式的新产品/跨单元变更处理，
  不能由某个 adapter 静默引入。
- **Confidence**: Sir confirmed at program level；current code/shared topology aligns with the
  absence of a terminal-user model, while durable shared docs do not yet state this product policy。

### D-034 — Missing updateMask uses adapter-local key-presence inference

- **Decision**: Memos 0.29.1 adapter 接受 MoeMemos 2.0.4 缺少 `updateMask` 的 PATCH，并从原始
  JSON 中实际出现的可更新 keys 推导 mask。这是明确命名、测试和隔离的 compatibility shim，
  不是严格 upstream parity。
- **Explicit-mask rule**: 请求提供合法 `updateMask` 时采用 Memos 0.29.1 语义，不额外推导或
  扩张 mask。
- **Presence rule**: 推导依据是 key presence，不是 truthiness 或反序列化后的 non-null values；
  `false`、`""`、`[]` 都是有效更新。未知/不可更新 key、空 inferred mask 明确失败；`null`
  除非上游字段合同明确允许，否则也失败。
- **Boundary**: shim 只属于 Memos 0.29.1 generation adapter，不下沉为 CanonicalMemo、memo
  application service 或 core 的通用 PATCH 规则。
- **Confidence**: Sir selected option 3 after reviewing the upstream/client conflict and inference
  semantics。

### D-035 — Memos extension is the implementable ownership unit

- **Decision**: 当前可实现单元的稳定 identity 是 `memos-extension`；`memos-backend` 只表示该
  extension 的首个 MVP delivery scope，不是独立 unit。
- **Ownership consequence**: CanonicalMemo、memo graph mapping、memo resolver 与
  product/generation adapters 都属于 Memos extension。backend、collector 或未来其他接入关系
  是该 owner 下可分别过 gate 的 delivery scopes。
- **Approval boundary**: backend MVP 已获批的 Product/Technical/Acceptance 结论不自动批准
  collectors、flomo 或未来 generations；它们仍需自己的 scope/gates，但不重复发明 canonical
  owner。
- **Confidence**: Sir corrected the prior unit/MVP conflation。

### D-036 — Authentication is composed by route tree

- **Decision**: public、peer JWT and extension-owned authentication are route policies，not three
  mutually exclusive `ExtensionBase` modes。Core protected routers and ordinary extension routers use
  `require_peer_jwt` by default。An extension that needs public or custom-auth routes explicitly uses an
  auth-neutral root and composes child routers with no dependency、the peer dependency or its own
  verifier。Memos uses a public detection child router plus a Memos-credential-protected child router。
- **FastAPI consequence**: remove the catch-all peer `JWTMiddleware` and reuse its validator through
  `Security`/`Depends` at router boundaries。Parent-router dependencies are additive and cannot be removed
  by a child，which is why mixed-policy extensions require an explicitly auth-neutral root rather than
  public exceptions under a protected parent。
- **ExtensionBase seam**: retain one overridable dependency hook whose default is
  `Security(require_peer_jwt)`；do not add a public/peer/self enum、path override、auth registry、extension
  sub-app or middleware solely for these requirements。
- **Management boundary**: backend MVP does not add `/memos/admin/*`。Credential setup/change/revoke
  should use the existing peer-authenticated extension configuration surface rather than inventing a
  parallel Memos administration API。
- **Documentation requirement**: implementation plan、local Unit TDD and any promoted cross-unit
  contract must preserve a minimal code-shaped example showing the core peer router、the default
  `ExtensionBase` hook and the Memos public/protected child-router composition；prose alone is
  insufficient。
- **Follow-on decision**: D-039 owns the confirmed PAT config/update semantics and exact public detection
  endpoint set；the route-auth composition remains D-036。
- **Confidence**: Sir explicitly accepted this route-composition refinement and requested that the
  minimal example survive into real implementation/documentation work。

### D-037 — Memos credential is long-lived by default

- **Decision**: the deployment-scoped Memos Bearer credential has no time-based expiry by default。It
  remains valid until explicitly replaced or revoked through the existing extension configuration
  surface。
- **Implication**: backend MVP does not add refresh tokens、login sessions、automatic rotation or
  periodic re-authentication。Missing、invalid、replaced or revoked credentials fail authentication；
  mobile sync must not stop merely because time elapsed。
- **Boundary**: D-039 later fixed token input、ordinary raw config persistence and no replacement overlap
  from InKCre's actual config trust boundary。
- **Confidence**: Sir explicitly confirmed the default lifetime。

### D-038 — Extension enable/disable is same-process hot

- **Decision**: extension `enable/disable` should change its HTTP route availability in the running
  process；a normal toggle does not require an application restart。For this project's current risk and
  production profile，directly adding/removing an extension-owned route set is an acceptable mechanism。
- **Runtime shape**: one retained router/route-set handle per extension is the mutation boundary。
  `ExtensionManager` is the only writer；enable publishes one exact route set，disable unpublishes it
  before `on_close()`，and re-enable must not accumulate duplicate routes。
- **Complexity boundary**: MVP does not add a permanent per-route running dependency、readiness gate、
  request-drain generation、isolated ASGI dispatcher or restart-bound activation model。Framework-
  specific route-cache/OpenAPI invalidation is localized behind the runtime host and protected by
  lifecycle tests。
- **Deployment boundary**: this contract assumes the current single-process/single-replica web runtime。
  A future multi-worker or multi-replica topology must reopen runtime-state propagation；it does not
  preemptively complicate this unit。
- **Confidence**: Sir explicitly preferred best-effort hot activation and accepted direct route mutation
  after calibrating both failure likelihood and consequence for this non-critical production context。

### D-039 — Memos PAT is ordinary validated extension configuration

- **Decision**: backend accepts one deployment-scoped、upstream-shaped
  `memos_pat_[0-9A-Za-z]{32}` Bearer credential。Its raw value is ordinary Memos extension config：it is
  persisted、loaded into runtime and returned through the existing peer-authenticated config surface。
  Omitted field preserves，`null` revokes，a valid string establishes or immediately replaces；the token
  remains valid until replace/revoke，without overlap、expiry、refresh or Memos-specific admin API。
- **Route contract**: only `GET /memos/api/v1/instance/profile` is public；
  `/memos/api/v1/status` remains unregistered (`404`) so MoeMemos falls through to the v1 adapter；all
  other implemented Memos and `/memos/file/*` routes require this PAT。
- **Generic config consequence**: extension config update is current config + shallow patch → validate
  through the existing extension `config_cls` → persist normalized JSON → update the running config。
  Invalid input or persistence failure leaves durable/runtime state unchanged。No Memos-only secret
  transform or read projection is introduced。
- **Boundary**: a future generic encrypted/redacted config facility may migrate Memos alongside other
  credential-bearing configs；this MVP does not pretend that only this token is secret while current
  Twitter、Telegram、IMAP and GitHub credentials remain recoverable。
- **Confidence**: Sir explicitly accepted ordinary raw config persistence and the generic update
  direction after reviewing the security/complexity trade-off；D-036/D-037 and released-client evidence
  close the remaining route and lifetime parts of O-018。

### D-040 — Memos attachment order is a product-specific graph fact

- **Decision**: D-013's unordered default remains the memo-family rule，but the Memos 0.29.1 adapter must
  preserve attachment request order。The tagged server deliberately rewrites attachment timestamps in
  reversed request order and lists them by that ordering；the repeated attachment field is therefore not
  incidental transport order。
- **Implication**: order belongs to attachment relations，not CanonicalMemo or attachment block content。
  Reordering changes the root → attachment relation set/targets without changing attachment identity or
  raw bytes。D-044 later fixed the exact predicate/content grammar。
- **Confidence**: deductive consequence of Sir-confirmed D-013 plus pinned Memos 0.29.1 source evidence。

### D-041 — Graph completeness is not an observable guarantee

- **Decision**: backend mutation failure is not required to leave a perfectly pre-command graph，and the
  MVP does not promise “no partial graph”。Do not add cross-component compensation、replay or cleanup
  machinery solely to enforce that guarantee。
- **Success boundary**: D-011 remains：a successful memo save means its primary memo root/change was
  persisted。The protocol response reflects the committed state；the exact HTTP result for subordinate
  attachment/comment failure remains fixture-owned。
- **Engineering latitude**: use one PostgreSQL transaction where it is already the simplest local
  implementation，but treat that as an implementation property，not a product/Acceptance invariant。
  Failure may leave orphan components、raw blobs or stale relations for later cleanup/organization。
- **Confidence**: Sir explicitly rejected the “无部分 graph” guarantee after preflight review。

### D-042 — CanonicalMemo v1 root wire

- **Decision**: CanonicalMemo v1 root content owns `body`、nullable timezone-aware `created_at` /
  `updated_at`、`archived`、`visibility` and `pinned`。Backend-created memos always establish both semantic
  times；future collectors may leave unavailable source times null。
- **Wire**: deterministic JSON；timestamps are UTC RFC3339；visibility uses canonical lowercase
  `private | protected | public`；unknown keys are rejected。`archived` is canonical semantics rather than
  copying Memos' generation-specific `state` enum。
- **Exclusions**: local identity remains `block.id`；canonical generation remains the resolver identity；
  attachments、parent and references remain graph-only。
- **Confidence**: Sir reviewed the proposed exact shape and reported no remaining issue。

### D-043 — Attachment raw bytes use PostgreSQL binary storage

- **Decision**: add a generic PostgreSQL-backed binary storage。The raw table owns only a generated pointer
  and `BYTEA` bytes；the attachment block owns attachment identity、filename、media type、decoded size and
  its storage pointer。
- **Reason**: this preserves graph/storage ownership and avoids inline base64 in canonical content or a
  DB + filesystem compensation protocol。A shared PostgreSQL transaction may be used where convenient，
  but D-041 means atomic graph completeness is not an Acceptance guarantee。
- **Boundary**: exact table/symbol names are implementation addresses；no parallel Memos object store is
  introduced。
- **Confidence**: Sir explicitly approved PostgreSQL binary storage。

### D-044 — Memos v1 relation payload grammar

- **Decision**: root → attachment relation content is `attachment:<zero-based-order>`；comment → parent is
  `parent`；memo → referenced memo is `reference`。Resolver validates the grammar and rejects duplicate
  attachment positions for one root。
- **Implication**: reorder rewrites relation positions/targets without changing attachment identity or raw
  bytes。This is a Memos extension contract on the existing open string payload，not a generic relation
  schema change。
- **Confidence**: follows D-040 and Sir's review that the remaining plan had no issue。

### D-045 — Repair client-web extension config routing

- **Decision**: the MVP delivery includes a separate client-web fix changing generic extension config save
  from `/{extension_id}/config` to core's `/extensions/{extension_id}/config` contract，with a focused
  request-shape test。
- **Boundary**: direct database editing remains possible in the trusted deployment；the path repair enables
  the existing core-API flow and must remain a sibling-repo change batch/commit。
- **Confidence**: Sir explicitly requested the repair after the preflight finding。

### D-046 — Memo delete uses primary success plus best-effort owned cleanup

- **Decision**: successful memo delete guarantees that the target root is no longer returned by memo
  list/read。The service then best-effort removes comment roots、parent/attachment relations、exclusively-
  owned attachment blocks and raw bytes。
- **Safety boundary**: cleanup residue is allowed under D-041；reference targets and any block without
  proven exclusive ownership must not be deleted。Traversal is cycle-bounded；repeated delete of an unknown
  root returns `404` in the 0.29.1 adapter。
- **Confidence**: Sir explicitly accepted the minimum deletion contract。

### D-047 — Exact API fixtures are a bounded executable compatibility contract

- **Decision**: fixtures cover only the approved Memos 0.29.1 backend subset，not the complete upstream
  server API。Each endpoint fixture pins request/query/header、response/status/error shape and the associated
  CanonicalMemo/graph/resolver effect where relevant。
- **Evidence layers**: upstream fixtures express tagged Memos 0.29.1 wire；MoeMemos fixtures express the
  2.0.4 real call sequence and deliberate compatibility deviations such as missing `updateMask`；InKCre
  fixtures express block/relation/storage and resolver output。
- **Test realization**: pure adapter/serialization fixtures、ASGI route/auth fixtures and PostgreSQL
  graph/storage fixtures remain separate；the pinned APK is the final client-level evidence。
- **Confidence**: Sir confirmed this interpretation and approved it as the remaining exact API contract。

### D-048 — Memos extension separates family core、product generations and access modes

- **Decision**: the stable Memos extension core owns CanonicalMemo、graph mapping/predicates、application
  commands and resolvers。Product/generation adapters（Memos 0.29.1、future flomo generations）own only
  native wire ↔ canonical/solved translation。Access modes（backend、future collector）own transport、
  scheduling/cursors/reconciliation and invoke the same extension core。
- **Test consequence**: one canonical/graph contract suite is reusable by every adapter/access mode；each
  product generation keeps its own request/response/error fixtures；backend and collector orchestration
  tests remain separate。
- **Complexity boundary**: design the package seams and dependency direction now，but do not invent a
  generic adapter registry、collector framework or flomo DTO before a second concrete implementation
  supplies pressure。
- **Confidence**: Sir explicitly required the implementation/tests to leave room for flomo and collectors；
  the boundary follows confirmed D-019/D-035 without expanding the current MVP。

### D-049 — Runtime acceptance is black-box-first，with static proof carrying structural verification

- **Decision**: new units should put most type、signature、dependency-direction、exhaustiveness and other
  structural verification into static mechanisms。Runtime tests should preferentially drive the public or
  deployed boundary and observe durable/user-visible effects；direct schema/default/helper/parser tests are
  not the default acceptance shape。
- **Double/live boundary**: hermetic CI may use a protocol double behind the real transport boundary and
  real persistence/runtime path。Where external availability is cheap，an opt-in live smoke should consume
  a real service/feed and assert stable invariants rather than volatile exact data。
- **Targeted-test exception**: retain a narrow white-box/pure test only when the behavior is valuable，cannot
  be proven statically，and cannot be observed reliably through the black-box path；the implementation plan
  must state that reason。Legacy low-value tests are removed when their replacement proof exists。
- **Memos history**: this preference does not retroactively invalidate the closed Memos layered fixtures；
  its released MoeMemos APK journey remains the final black-box evidence，while the extra layers were an
  accepted complexity trade-off for that unit。
- **Confidence**: Sir explicitly stated a general preference for black-box tests and assigning most
  verification to static checking，and required RSS acceptance to use real RSS/Atom or at least a double。

### D-050 — Feed-authored content remains authority；fetched full text is independent enrichment

- **Decision**: RSS/Atom-authored title、summary and content remain source-authored canonical facts。A
  successful item-link fetch does not overwrite them；the extracted full article is an independent graph
  component/enrichment with its own retrieval、failure and change behavior。
- **Use consequence**: resolver/use-facing text may prefer the full-text enrichment when available，while
  preserving access to the original feed representation。Enrichment failure alone does not turn an otherwise
  valid feed-item collection into failure。
- **Boundary**: exact component resolver、relation grammar、fetch policy and whether enrichment ships in the
  first MVP slice remain Technical/Product-scope work；the authority split is fixed。
- **Confidence**: Sir explicitly accepted this model。

### D-051 — RSS hardening is a behavior rewrite behind the existing extension identity

- **Decision**: retain the `rss` extension product/artifact identity，but design a new MVP implementation。
  Existing collectors、`seen_ids`、unversioned resolver、graph shape and white-box tests are failure/requirement
  evidence rather than an incremental modification base。
- **Library boundary**: mature third-party libraries should own RSS/Atom parsing and，if admitted，article
  extraction。InKCre continues to own HTTP policy、canonical mapping、native identity/reconciliation、graph、
  source job/state and observable failure behavior；a third-party feed reader must not introduce a parallel
  feed/entry store or application model。
- **Complexity boundary**: do not rewrite a parser，do not create a second extension，and do not use the rewrite
  to redesign every source or build a universal source framework。
- **Confidence**: Sir explicitly approved the behavior-rewrite framing and mature-library preference。

### D-052 — Full-text enrichment ships in the RSS MVP and is enabled by default

- **Decision**: the first RSS rewrite delivery includes item-link full-text enrichment as a second vertical
  slice after canonical feed collection。It is enabled by default and source configuration may explicitly
  disable it。
- **Trigger/failure**: do not infer truncation from arbitrary body length or similar heuristics。For an
  eligible item link，new or meaningfully updated items receive one best-effort enrichment attempt under the
  approved fetch policy；failure does not fail the primary feed-item collection。Unchanged items are not
  unconditionally re-fetched on every collection run。
- **Authority**: D-050 remains unchanged：feed-authored content is authority，full text is an independent
  component，and use-facing text may prefer the component when present。
- **Confidence**: Sir required enrichment to be enabled by default and accepted the other proposed MVP
  boundaries。

### D-053 — Feed-item reconciliation uses a best-effort exact identity ladder

- **Decision**: Atom uses `atom:id` first；RSS uses `guid` within the strongest stable feed scope；when the
  protocol ID is absent，use the canonical alternate link。When neither a native ID nor a link exists，do not
  manufacture an exact identity from a normalized-payload fingerprint；apply the source instance's explicit
  `create` / `discard` unidentified-item policy，defaulting to `create`。
- **Change behavior**: the same exact identity updates the existing local block。Native-ID changes and
  content/time similarity never trigger fuzzy overwrite；possible duplicates remain available for later
  organization。`create` treats every encounter with an unidentifiable item as a new block and records that
  exact native identity was unavailable；it does not claim idempotency or reconciliation。`discard` skips the
  item with an observable diagnostic。
- **Scope/provenance**: prefer a protocol-proven stable feed identity；fall back to the local source instance
  when RSS provides no stable external scope。Identity/provenance facts live in versioned feed canonical
  content，not a generic binding table。The info-base identity remains `block.id`。
- **Confidence**: Sir accepted the native-ID/link ladder，then explicitly withdrew the fingerprint fallback as
  unnecessary complexity。After checking the low expected incidence，Sir selected new-block collection and a
  source-configurable create/discard policy；default `create` follows that stated product preference。

### D-054 — Feed/channel information is an independent graph block

- **Decision**: persist feed/channel-native information as an independent block；persist each item as its own
  block and connect it to the feed block through a relation。Do not use source-instance configuration as a
  substitute for feed-native information，and do not duplicate mutable feed metadata into every item root。
- **Boundary**: a source instance owns collection configuration and runtime state；a feed block owns collected
  feed/channel facts and may be independently resolved，queried and graph-navigated。Relation direction/content，
  canonical feed shape and feed reconciliation remain Technical/Product follow-ups。
- **Confidence**: Sir explicitly accepted this separation after reviewing its graph and authority consequences。

### D-055 — Feed/channel reconciliation uses protocol identity before local URL scope

- **Decision**: identify an Atom feed by `atom:feed/atom:id` first；otherwise use the feed-declared
  `atom:link[rel=self]` when available；otherwise use the configured feed URL within the local source-instance
  scope。The same exact feed identity updates the existing feed block。
- **Change behavior**: a configured-URL change forms a new feed block when neither protocol identity nor a
  declared self link proves continuity。HTTP redirect handling and URL normalization are transport/Technical
  details and must not silently invent cross-feed equivalence。
- **Boundary**: the local source instance remains collection config/runtime state；its ID only scopes the last
  fallback and is not persisted as the feed's external identity。
- **Confidence**: Sir explicitly accepted the proposed feed identity ladder。

### D-056 — A source-time admission watermark may reduce unidentified-item duplicates

- **Decision**: under RSS source policy `create`，an item lacking exact native ID/link may be filtered by a
  low-cost source-time admission watermark。For the first successful contentful snapshot，or when the item has
  no parseable source-native time，create a new block。Thereafter create only when the item's effective native
  time is later than the previous successfully committed snapshot observation time；otherwise filter it。
  Policy `discard` continues to skip every unidentified item。
- **Watermark fact**: capture `snapshot_observed_at` when the complete feed response is received，but advance the
  RSS source state only after that collection succeeds。Do not substitute collect-job completion time；do not
  advance it for `304 Not Modified`。Prefer a valid native `updated` time，then `published`/`pubDate`；exact field
  projection remains Technical design。
- **Semantics**: this is an admission heuristic，not item identity，reconciliation，deduplication proof or an
  ordering contract。Scan all items rather than short-circuiting on document position。Late publication，
  backdating or publisher clock skew may cause a new unidentified item to be filtered；that bounded loss is
  accepted for this rare fallback instead of adding content fingerprints or snapshot-diff machinery。
- **Reusable pattern**: when exact identity is unavailable，a cheap independently observed monotonic watermark
  may bound repeated side effects，provided its weaker guarantee and failure modes stay explicit and the system
  does not promote the heuristic into authority。
- **Confidence**: Sir explicitly accepted the precise RSS watermark behavior and requested that the general
  pattern/mind be queued for durable documentation promotion。

### D-057 — Enclosures are graph components with manual and source-policy materialization

- **Graph authority**: persist each RSS/Atom enclosure as an independent metadata block and connect it to its item
  through a relation。The enclosure metadata block owns the native URL，media type，declared
  length/title and other supported feed metadata；the item root does not duplicate that association。
- **Download surfaces**: the RSS extension exposes a peer-authenticated manual materialization endpoint whose
  inputs identify enclosure metadata blocks。The command must pass each block through its exact installed resolver
  rather than parsing `block.content` directly，then return the newly materialized semantic content block。Source config also
  provides an automatic enclosure-download policy and selects the target
  writable storage。
- **Responsibility boundary**: the resolver interprets and validates enclosure semantics；an extension-owned
  application service performs network/storage/graph side effects；storage only persists and retrieves actual-content
  bytes。The downloaded block remains distinct from the enclosure metadata block so collection
  authority is not overwritten by local materialization。
- **Materialized semantics**: do not model the downloaded result as `StoredBinary` merely because storage holds
  bytes。Create the semantic media block selected by the materialized content kind—normally audio，video or
  image—and point that block at the selected storage。PDF，EPUB and ZIP also receive exact content resolver IDs
  in this delivery；unknown or not-yet-supported downloaded kinds fall back to a concrete file
  block with best-effort MIME type。Do not silently revive the rejected generic external `resource`/binding
  model merely because the endpoint response was described as a “resource block”。
- **Storage pressure**: existing `WritableStorage` plus built-in `postgresql_binary` can prove the strategy，but
  its whole-bytes synchronous write contract is not evidence of large enclosure/S3 suitability。Technical
  design must decide whether this unit adds a streaming capability and S3-compatible storage or verifies only
  the existing target while retaining storage-ID configurability。
- **Confidence**: Sir accepted the independent enclosure graph，required the manual extension endpoint，and
  required source-configured automatic download into storage in this unit，even if that exposes a need for a
  new storage type。Sir then corrected the materialized-block proposal：raw binary is a storage representation，
  while the block should use content semantics；Sir explicitly included PDF/EPUB/ZIP and selected file with
  MIME type as the unknown/unsupported fallback。

### D-058 — RSS may propagate media/storage corrections horizontally without a new unit

- **Decision**: keep `rss-extension-hardening` as the sole active implementable unit。Media resolver，storage
  and Memos attachment corrections discovered by the RSS vertical are horizontal state diffs inside this same
  discussion/design/acceptance/implementation loop，not a separately sequenced foundation unit。
- **Current Memos fact**: Memos attachments currently use `extensions.memos.attachment.v1`；their canonical
  content combines protocol attachment metadata with a PostgreSQL `blob_id` and the repository hard-codes
  storage `-4`。They do not use image/video/audio/file semantic blocks。
- **Required correction**: this unit must move Memos attachment actual content onto the corrected
  media/file + storage path while retaining the already accepted Memos 0.29.1 backend behavior。Whether the
  protocol attachment remains a metadata block or its identity is projected directly from a media/file block
  remains the next Product decision。
- **Blast-radius rule**: cross-owner changes still need explicit addresses，state diffs and regression proof；
  keeping one unit does not make RSS the durable owner of common media/storage contracts。
- **Confidence**: Sir explicitly rejected a mechanically split foundation unit and requested that existing
  Memos attachments be corrected in the same work if they do not already use semantic media blocks。

### D-059 — Independently useful protocol metadata has its own block

- **Decision**: retain a Memos attachment metadata block and connect it to one
  image/audio/video/PDF/EPUB/ZIP/file semantic content block。Memo ordered ownership targets the attachment metadata block；
  its resolver joins the content relation to project the Memos-native attachment。Unattached uploads remain
  discoverable through the exact Memos attachment resolver ID。
- **Authority split**: the metadata block owns protocol identity，role，lifecycle and authored/declaration
  provenance；the exact resolver ID expresses content kind，resolver solved content owns byte-derived facts，and
  storage owns actual content by pointer。Do not duplicate one authority fact merely to make both blocks self-contained。
- **Cleanup**: deleting a metadata block may clean its semantic content block/stored object only under explicit exclusive-
  ownership proof。A shared semantic content block survives metadata-block deletion。
- **Reusable pattern**: use `metadata block → semantic content block → storage` only when protocol/source-authored
  metadata has independently useful identity，role or lifecycle。Do not mechanically add a metadata block when
  the input's only meaning is already carried by the semantic content block。RSS enclosure and Memos attachment are the two current reference
  pressures。
- **Confidence**: Sir explicitly selected the two-layer Memos graph and identified it as a common pattern。

### D-060 — Block owns storage hydration without a second persistent pointer field

- **Persistent shape**: retain the existing conditional meaning of `BlockModel.content`。When `storage` is
  null，`content` is inline actual content；when `storage` is non-null，`content` is that storage instance's
  opaque pointer。Do not add `storage_pointer` or a duplicate `BlockRecord` representation。Keep `content`
  non-null and change storage deletion from `SET NULL` to `RESTRICT` while blocks reference it。
- **Hydration API**: `await block.get_hydrated_content()` is the single general actual-content read path。It
  returns inline `content` directly or resolves the pointer through the selected storage；resolver and other
  consumers that need actual content must not interpret `storage` themselves。
- **Lazy instance cache**: cache the returned actual content in ORM-non-mapped
  `block._hydrated_content`。Use a distinct unloaded sentinel supplied by `PrivateAttr(default_factory=...)` so
  an actual value cannot be confused with “not loaded” and Pydantic cannot deepcopy the sentinel identity。
  Newly loaded instances begin unloaded；the controlled block update path must invalidate the cache whenever
  persisted `content` or `storage` changes。This is model-instance memoization，not a promise that an external
  storage object cannot change；never assign hydrated bytes back to the mapped `content` column。
- **Terminology**: retire the ambiguous “real content / raw content” pair。`content` is the persisted inline
  value or storage pointer；`hydrated content` is the actual data returned by the block；resolver-specific
  interpretation remains a separate semantic result。
- **Metadata boundary**: MIME，size，checksum，filename/provenance and other semantic metadata must receive an
  explicit authority in the media design；they must not be encoded into the opaque pointer or duplicated in
  `content` merely because a storage-backed block otherwise has no inline metadata field。
- **Confidence**: after comparing a separate persistent/runtime representation with the smaller active-record
  change，Sir selected conditional persisted `content` plus block-owned lazy hydration/cache and accepted
  storage-deletion `RESTRICT`。

### D-061 — Storage hydration is a peer-local capability

- **Shared versus local**: storage type semantics，storage instance configuration and block pointer are shared
  protocol state；the executable handler is a capability registered in each peer runtime。Schema/migration
  authority does not make core-py a central content service。
- **Hydration**: each peer's block hydration path selects its local handler。A missing handler is an explicit
  unsupported-capability failure，not an implicit request to core-py or another peer。
- **Delegation boundary**: future cross-peer execution would require generic capability discovery and an explicit
  peer command contract。It must not be hidden inside ordinary block hydration or privilege one named runtime。
- **Current unit coverage**: client-web must support the full content lifecycle of the built-in
  `postgresql_binary` storage during this RSS/Memos horizontal slice。D-063–D-066 define complete CRUD，storage
  independence，cache refresh and the exact PostgREST transport。
- **Confidence**: Sir explicitly accepted the peer-local handler contract and required client-web PostgreSQL
  binary support，while reserving approval of the low-level transport。

### D-062 — Storage transports opaque content bytes; resolver owns interpretation

- **Storage contract**: a storage implementation locates and reads/writes a block's actual content as opaque
  bytes（or an equivalent streaming byte source）。It does not parse JSON/HTML，decode media，or decide whether
  the information is image，video，audio，PDF or another semantic kind。
- **Resolver contract**: resolver owns content-kind interpretation and parsing，using the block's exact resolver ID
  plus graph/metadata context。MIME may inform that interpretation，but it is not created as semantic
  truth merely because a storage transport returned a header or holds bytes。
- **Type naming pressure**: storage types should name access/persistence mechanics，not information kinds。The
  existing `http_image` / `http_video` / `http_html` / `http_json` / `http_text` split and the now-redundant
  “binary” emphasis in `postgresql_binary` require explicit redesign；this decision does not yet freeze their
  replacement names or migration shape。
- **Backing records**: an implementation may use a private/protocol backing relation to hold its bytes。That
  relation is not a storage type，storage instance，block or semantic media object。`storage_blobs` is an accepted
  name for the PostgreSQL implementation's backing relation；the earlier concern was conceptual classification，
  not its table name。
- **Confidence**: Sir identified this as a general pattern and explicitly assigned bytes transport/storage to
  storage and image/video/PDF interpretation to resolver。

### D-063 — Client-web PostgreSQL storage covers complete CRUD

- **Scope**: client-web `packages/core` must implement local create，read，update and delete support for the
  built-in PostgreSQL bytes storage in this unit；read-only hydration is insufficient。
- **Transport boundary**: the browser peer talks to the admitted database surface through PostgREST，not through
  a privileged core-py content proxy。The precise raw-binary read/write function or media-handler shape remains
  subject to Sir's review and a black-box proof against the pinned PostgREST v14.15 runtime。
- **Contract projection**: the admitted backing relation/functions must be added to the generated client-web
  database contract through its normal generation path，not by hand-editing generated TypeScript。
- **Storage independence**: CRUD operates on opaque pointer plus bytes and never discovers，loads or mutates a
  referencing block。The generic writable capability therefore needs a real update operation；for PostgreSQL the
  natural candidate is updating `storage_blobs.data` under the same `blob_id`，not mandatory copy-on-write。
- **Confidence**: Sir explicitly expanded this unit from PostgreSQL binary hydration to complete client-web
  write/read/delete support，including the update part of CRUD。

### D-064 — Block record time does not claim hydrated-content freshness

- **Timestamp meaning**: `block.updated_at` reports mutation of the persisted block record。When `storage` is
  non-null，the referenced object may live outside the protocol database and change independently；the timestamp
  therefore cannot generally be interpreted as the last modification time of hydrated content。
- **Dependency direction**: block selects a storage and carries its opaque pointer；storage does not depend back on
  block。Storage update/delete must not search for or mutate referencing blocks merely to manufacture block-level
  cache or timestamp coherence。
- **Cache boundary**: `_hydrated_content` / client-web's corresponding private cache is at most an instance-local
  snapshot。A mutation coordinated by the same block/application path can invalidate its known instance，but no
  generic cross-instance or cross-peer freshness guarantee is inferred。The explicit refresh/bypass API remains to
  be decided。
- **Derived data**: embeddings，indexes and other derived interpretations can become stale when externally stored
  content changes without an InKCre command。Detection/reconciliation belongs to collection or organization policy，
  not to the base storage CRUD contract。
- **Confidence**: Sir corrected the earlier copy-on-write rationale by identifying external storage mutability and
  rejected a reverse dependency from storage to block。

### D-065 — Hydrated-content cache is an explicitly refreshable instance snapshot

- **Default read**: `await block.get_hydrated_content()` in core-py and the equivalent client-web method lazily
  hydrate once and reuse the value held by that block instance。
- **Explicit refresh**: callers that require a new storage read pass an explicit refresh option。Refresh bypasses
  the cached snapshot，reads through the selected peer-local storage handler and replaces the instance cache with
  the result。
- **API projection**: Python uses `await block.get_hydrated_content(refresh=True)`；client-web exposes the same
  semantic through `await block.getHydratedContent({ refresh: true })` while retaining idiomatic language shape。
- **Non-guarantees**: this contract adds no TTL，background polling，storage-version inference，cross-instance cache
  invalidation or cross-peer coherence。A storage handler may later use provider validation features internally，
  but the base block API does not require them。
- **Confidence**: Sir explicitly accepted the instance-local cache plus explicit refresh contract。

### D-066 — PostgreSQL browser CRUD uses raw C/R and relation U/D

- **Create**: client-web sends bytes to an admitted `create_storage_blob(bytea)` RPC as
  `application/octet-stream`。The function has PostgREST's supported single unnamed `bytea` argument and returns the
  generated blob UUID used in the opaque pointer。
- **Read**: client-web calls an admitted read RPC with `blob_id` and `Accept: application/octet-stream`。The function
  returns an `application/octet-stream` domain over `bytea` so the raw transport consumes an `ArrayBuffer` rather
  than the normal JSON response decoder。
- **Update/Delete**: update PATCHes the exact `storage_blobs` row with PostgreSQL's `\\x...` bytea representation；
  delete uses the exact UUID-filtered relation DELETE。This preserves in-place object identity and uses the existing
  authenticated peer table authority。
- **Why hybrid**: raw Create/Read avoid encoding overhead on the common，large-data paths。PostgREST raw function
  input supports only one unnamed binary argument，so relation Update avoids inventing a custom identifier header or
  binary envelope；its roughly 2× hex upload representation is accepted for the less frequent path。
- **Client transport**: `packages/core` owns one small authenticated raw PostgREST fetch path for Create/Read；typed
  generated PostgREST relation operations remain the path for Update/Delete。The admitted functions and
  `storage_blobs` relation are projected into the generated database contract，not hand-maintained client types。
- **Verification**: black-box the four operations through the pinned PostgREST v14.15 runtime，including byte-exact
  round-trip，same-pointer update，missing UUID behavior，JWT/ACL denial and cache refresh。
- **Confidence**: Sir explicitly accepted the raw Create/Read plus relation Update/Delete wire contract。

### D-067 — Media metadata follows its authority; no generic block metadata is added

- **Protocol/source authority**: filename，protocol-declared MIME/length，source URL and source-authored timestamps
  remain in the canonical content of a metadata block（for example RSS Enclosure or MemosAttachment）。A metadata
  block is an ordinary block that owns protocol/source-authored facts about related content；it is not a separate
  wrapper type or source-module abstraction。Those facts are not copied onto the related media/file semantic content block。
- **Storage authority**: `blob_id`，object key，provider version and other retrieval mechanics belong only to the
  selected storage's opaque pointer/config。They are not semantic media metadata。
- **Resolver authority**: image/audio/video/PDF/EPUB/ZIP/file kind is expressed by exact resolver ID。Detected
  MIME，actual byte size，checksum，dimensions，duration and similar byte-derived facts belong to solved content；
  organization may materialize those that have durable use value as graph enrichment。
- **Graph shape**: a metadata block relates to a semantic content block。The metadata block keeps protocol identity/role/
  metadata/lifecycle；the semantic content block keeps resolver identity plus inline content or an opaque storage pointer。
  The same semantic content block may therefore be referenced without collapsing distinct source facts。
- **Schema restraint**: this unit does not add `blocks.metadata`。The current pressure is resolved by assigning
  existing facts to metadata-block content，pointer/config，solved content and optional organization enrichment；a
  generic JSONB field would add an unbounded competing authority without a remaining requirement。
- **Memos correction**: `CanonicalAttachment.blob_id` moves out of the attachment metadata block content and becomes
  the related semantic content block's storage pointer；the metadata block retains Memos attachment fields needed for native
  list/read/delete behavior。
- **Confidence**: Sir explicitly accepted this authority split，identified it as the correct design and promoted it
  as a common pattern。

### D-068 — S3 is valuable but sequenced with Nextcloud Files, not RSS

- **Decision basis**: the general utility of S3-compatible object storage is sufficient future product pressure；
  it does not need to be justified by the rare RSS enclosure that cannot fit in memory。
- **Current unit**: RSS enclosure materialization targets the already approved writable PostgreSQL storage。This
  unit does not implement S3-compatible storage and does not make very-large，non-materializable enclosure streaming
  an acceptance condition。
- **Abstraction restraint**: do not add a speculative streaming writable-storage contract solely for future S3。
  Keep the current unit's byte-oriented contract and explicit download bounds；introduce/reshape streaming when an
  actual storage implementation exercises it。
- **Sequencing**: design and implement S3-compatible storage with the future Nextcloud Files extension，where object
  storage，file scale，hierarchy/listing and incremental file synchronization provide stronger reference pressure。
  This is deferral to an identified unit，not rejection of S3。
- **Confidence**: Sir explicitly rejected large RSS files as the S3 decision basis and selected the Nextcloud Files
  extension as the more appropriate implementation point。

### D-069 — Each extension owns media-classification policy; core offers mechanisms

- **Ownership**: no global MIME/kind evidence ladder is imposed across Memos，RSS，Atom or future extensions。The
  extension adapter that understands its protocol owns which declared/observed evidence selects an exact resolver ID。
- **Common capability**: `ResolverManager` may deepen its existing resolver registry with reusable MIME
  normalization/detection helpers and MIME-to-registered-resolver matching，including an opt-in default helper。
  Extensions decide which evidence to provide，its order，when to call the helper and whether to override its result。
  Do not add a standalone media module or hide a mandatory precedence policy inside `ResolverBase`。
- **Memos evidence**: Memos 0.29.1 Attachment has a protocol `type` MIME field alongside filename and bytes。Upstream
  normalizes and accepts a provided type，falling back to filename extension and Go content detection only when it is
  empty。The current backend MVP also requires a valid non-empty type。Memos can therefore treat it as its stable
  declared-media-type input without mandatory byte sniffing。
- **Feed evidence**: RSS 2.0 enclosure requires `url`，`length` and MIME `type` attributes。Atom link `type` is
  optional and advisory；RFC 4287 says a dereferenced server response media type is authoritative over that hint。
  RSS and Atom adapters therefore need distinct explicit policies even inside one extension family。
- **Terminology**: call protocol/HTTP values “declared/observed media type”，byte magic a “content byte signature”，
  and reserve “signature” without qualification for contexts that actually define it；they are not interchangeable。
- **Current correction**: the existing RSS canonical stores enclosure URLs only and drops type/length。The rewrite
  must preserve the protocol attributes before any classification/materialization policy can be correct。
- **Confidence**: Sir rejected the proposed universal ladder，assigned policy to each extension and allowed only a
  reusable ResolverManager mechanism where it does not erase extension-specific semantics。

### D-070 — Memos Attachment uses its declared MIME without mandatory sniffing

- **Input authority**: the Memos product adapter requires and normalizes `Attachment.type` as its protocol-declared
  MIME。The MemosAttachment metadata block preserves that exact declaration for native list/read/download projection。
- **Resolver selection**: the extension maps the normalized MIME through `ResolverManager` to the semantic content block's
  exact resolver ID。Known media types select image/audio/video/PDF/EPUB/ZIP as applicable；an unknown or unsupported
  MIME selects file while retaining the declared MIME on the metadata block。
- **No universal verification**: byte-signature sniffing is not mandatory for a successful MoeMemos upload and a
  mismatch does not override the declared Memos field or reject the upload。A future diagnostic/enrichment may inspect
  bytes，but it is outside this compatibility write contract。
- **Graph consequence**: MemosAttachment remains the protocol metadata block；its content relation points to the
  media/file semantic content block whose storage-backed `content` is only the opaque pointer。Backend reads reconstruct
  Memos MIME from the metadata block，not from storage or globally detected solved content。
- **Confidence**: Sir accepted this Memos classification policy and corrected “protocol-declared media type” versus
  “content byte signature”。

### D-071 — RSS 2.0 enclosure type is the primary resolver-selection evidence

- **Protocol basis**: a conforming RSS 2.0 enclosure has required `url`，byte `length` and MIME `type` attributes。
  The canonical RSS Enclosure metadata block preserves all three rather than reducing the component to its URL。
- **Primary mapping**: a valid，specific `enclosure.type` is passed through `ResolverManager` to select the semantic
  content block's exact resolver ID。An unknown but valid declared MIME falls back to file while the metadata block retains it。
- **Fallback boundary**: HTTP response Content-Type，filename/URL evidence and optional byte detection participate
  only when the RSS declaration is absent，invalid，generic（for example `application/octet-stream`）or cannot provide
  a usable mapping。They do not silently rewrite the metadata-block field。
- **Malformed feed boundary**: this classification decision does not yet decide whether a non-conforming enclosure
  with missing required attributes is retained with diagnostics or discarded；that belongs to RSS item failure
  policy。
- **Confidence**: Sir explicitly accepted valid，specific RSS `enclosure.type` as the primary resolver-selection
  evidence。

### D-072 — Atom enclosure uses dereferenced HTTP type before its advisory hint

- **Protocol basis**: Atom `link.type` is optional advisory MIME；RFC 4287 says it does not override the actual media
  type returned when `href` is dereferenced。The canonical Atom Enclosure metadata block preserves `href` and optional
  `type`，`length` and `title` attributes exactly。
- **Primary mapping**: materialization first uses a valid，specific HTTP Content-Type to select the exact resolver
  ID。If the response type is absent，invalid，generic or unusable，the adapter tries the valid Atom
  `link.type` hint。
- **Fallback boundary**: only after both protocol-specific signals are unusable may the Atom adapter call optional
  `ResolverManager` filename/URL or byte-detection mechanisms；an unidentified result becomes file。
- **No source rewrite**: observed HTTP type and fallback results never overwrite the Atom metadata block's declared
  `type`。A specific HTTP/link conflict selects the resolver ID from HTTP while retaining the original hint for
  provenance。
- **Confidence**: Sir explicitly accepted this Atom enclosure classification policy。

### D-073 — Resolver makes graph application-usable; lazy graph materialization is allowed

- **Role**: resolver is the application-facing interpretation boundary for a block and its relevant graph。Its job is
  not limited to pure decoding；it makes graph information usable by application consumers。
- **Optional outcomes**: text and embedding-string representations may be unsupported or absent。The abstract base
  methods remain mandatory so every concrete resolver explicitly implements the capability surface；an unsupported
  resolver raises `UnsupportedResolverCapability`，and a supported resolver may return `None` for a block with no
  meaningful value。Neither case is represented by a fake empty string。
- **Lazy materialization**: resolution may call AI or another organization capability and persist missing derived
  blocks/relations。A read-triggered write is not inherently incorrect；it can be a lazy-loading/materialized-view
  behavior。
- **Actual problem**: callers currently cannot express whether remote work，cost，latency and graph mutation are
  allowed，and current image resolution mixes those effects with import-time credentials，fixed storage assumptions
  and ad hoc persistence。The rewrite must expose a materialization policy and make its writes idempotent/
  concurrency-safe enough for the unit's acceptance，rather than ban side effects。
- **Peer projection**: exact method names remain peer-local，but core-py and client-web must distinguish cached solved
  projection refresh from permission to materialize missing graph information。
- **Interface status**: D-074 closes the ordinary default and shared option vocabulary；D-075 closes the abstract
  method/unsupported-result boundary and exact common resolver IDs。
- **Confidence**: Sir identified the mandatory text/embedding contract as historical debt，accepted its refactor and
  corrected the proposed pure-read restriction with resolver's application-facing/lazy-loading role。

### D-074 — Resolver materializes missing graph by default；refresh is cache replacement only

- **Ordinary default**: resolver application use may materialize missing derived graph by default。A caller that
  requires a side-effect-free attempt explicitly sets `materialize_missing=False`（TypeScript
  `materializeMissing: false`）。This option is permission to create an absent derivation，not a command to replace
  one that already exists。
- **Refresh contract**: on a cache-bearing read，`refresh=True`（TypeScript `refresh: true`）bypasses the reusable
  instance/local snapshot，re-reads the currently available authority and replaces that cache。It does not itself
  authorize materialization，request AI，or regenerate an existing derivation；those effects remain governed by
  `materialize_missing` or an explicit organization command。The two controls are orthogonal。
- **Adjacent vocabulary**: `invalidate` discards a cached value without replacing it；`recompute` explicitly
  regenerates an existing derived representation and belongs to organization；`reload` is not an alias for refreshing
  information and should be reserved for a runtime/config/module lifecycle when such an API exists。New InKCre-owned
  APIs must not use an unqualified `force` boolean for any of these meanings。A third-party protocol-owned `force`
  parameter，such as the Memos API query shape，is preserved as protocol fidelity rather than renamed。
- **Relation direction**: `include_in` / `include_out`（TypeScript `includeIn` / `includeOut`）are the stable direct-
  relation selectors relative to the subject block：incoming means the block is `to_`，outgoing means it is `from_`。
  They do not imply recursive graph traversal。
- **Scope restraint**: this vocabulary does not require every method to expose every option。It fixes the name when
  that semantic control exists，while peer-local method names and Python/TypeScript casing remain idiomatic。
- **Current migration pressure**: client-web resolver methods currently call cache replacement `force`；the common
  resolver rewrite should migrate those InKCre-owned options to `refresh`。Legacy source-job `full` is not promoted：
  it currently combines scan breadth，incremental-boundary bypass，ordering and pagination effects across sources，so
  each retained behavior must be named from its source-specific contract instead of preserving one generic boolean。
- **Confidence**: Sir selected ordinary missing-materialization with an explicit read-only override，required
  `refresh` to become stable durable vocabulary and requested promotion of other genuinely common parameters。The
  relation selectors are already aligned across core-py/client-web；the `full` exclusion follows direct code evidence。

### D-075 — Exact resolver IDs version semantic-content contracts

- **Exact IDs**: new common semantic content blocks use `core.text.v1`，`core.html.v1`，`core.image.v1`，
  `core.audio.v1`，`core.video.v1`，`core.pdf.v1`，`core.epub.v1`，`core.zip.v1` and `core.file.v1`。
  `core` means shared InKCre-owned semantics rather than core-py execution authority。
- **Version meaning**: the `v1` suffix is the resolver contract version。It advances only for an incompatible
  persisted/solved/graph contract change，not for a parser release or file-format minor version。Use conventional
  `version` language rather than introducing `generation` for this axis。
- **Block roles**: protocol/source-authored identity，declaration，role and lifecycle remain in a metadata block；the
  related semantic content block owns its exact resolver ID plus inline actual content or a storage pointer。Both
  are ordinary blocks and remain connected by the accepted `content` relation。
- **Solved content**: `core.text.v1` solves to Unicode text and `core.html.v1` to decoded HTML source。The seven
  byte-oriented contracts share `byte_size` and nullable `detected_media_type`；image/audio/video/PDF/EPUB/ZIP add
  their approved bounded typed facts，and file adds no pretend format-specific facts。
- **Capability methods**: capability is invoked directly on a resolver instance。`ResolverBase.get_text()` and
  `get_str_for_embedding()` remain abstract so every concrete resolver declares behavior。An unsupported
  implementation raises `UnsupportedResolverCapability`；a supported implementation may return `None` when the
  particular block has no meaningful value。`ResolverManager` selects/constructs resolvers and owns shared registry/
  matching mechanisms，not instance capability dispatch。
- **Hard cut-off**: remove the bare `text`，`html`，`image` and `video` implementations and update every in-repo
  producer，consumer and test in the same coherent pass。Do not retain compatibility decoders or migrate old rows；
  reads of retired IDs fail explicitly，and client-web must not silently fall back to text。
- **Scope restraint**: the minimum does not require OCR，speech transcription or PDF/EPUB/ZIP child-graph expansion。
  Exact parser dependencies，bounded inspection，charset authority，peer-local solved types and Memos attachment
  resolver-version consequences remain Technical preflight。
- **Confidence**: Sir accepted the nine exact IDs and hard cut-off，kept abstract capability methods，moved calls back
  onto resolver instances，preferred `semantic content block`，and selected conventional `version` terminology。

### D-076 — Memos attachment v1 receives a one-time atomic migration to v2

- **Decision**: `extensions.memos.attachment.v1` rows are migrated atomically to the D-059/D-067 two-block graph，
  rather than discarded or supported through a permanent v1 decoder。The existing metadata block ID remains the
  Memos protocol identity and is rewritten as inline `extensions.memos.attachment.v2` canonical metadata without
  `blob_id`。A new `core.<kind>.v1` semantic content block receives minimal opaque PostgreSQL pointer JSON containing
  the existing blob UUID，and one metadata → semantic `content` relation connects them。Blob bytes are not copied；
  existing memo → attachment `attachment:<order>` relations remain unchanged。
- **Failure boundary**: each row conversion is transactional；a failed conversion leaves the v1 block、blob and owner
  relations unchanged。After a successful migration the runtime registers only v2，so this is data preservation at a
  breaking boundary，not indefinite version compatibility。
- **Production evidence**: a 2026-08-02 read-only query against canonical Neon `production` found Alembic head
  `d9f4e2a1b7c3`，no `storage_blobs` table and no `extensions.memos.attachment.v1` rows。The migration is therefore an
  empty forward step for the current public demo，while remaining necessary for another database that already ran the
  Memos/PostgreSQL-binary implementation。The same production snapshot contains retired bare resolver rows
  (`html=1`、`image=28`、`text=8`、`video=3`)；D-075 intentionally leaves those rows unsupported without migration。
- **Confidence**: Sir explicitly accepted the one-time atomic migration and clarified that canonical production is a
  public demo，so ordinary diagnostic access should be practical rather than governed as a high-criticality service。

### D-077 — Durable projection follows verified implementation；publication remains owner-specific

- **Decision**: during discussion，new architecture understanding stays in the task packet so unstable ideas do not
  churn durable docs。After product/technical design is stable and implementation supplies evidence，the unit loop
  projects accepted truth into the correct Hub、Unit TDD、deployment or peer-local owner；this does not require a
  separate “documentation unit”。
- **Operation boundary**: editing durable owner worktrees is distinct from commit、push、Hub publication and Spoke
  shared-ref bump。The latter operations still require explicit authorization and separate owner commits；Hub source
  must be published before any Spoke ref moves。
- **Correction**: earlier packet language incorrectly treated durable projection itself as a post-unit publication
  gate。Sir clarified that only discussion-time mutation was deferred，not implementation-time reconciliation。
- **Confidence**: direct clarification from Sir after RSS implementation completion；consistent with the repository's
  one-authority rule and Hub/Spoke workflow。

### D-078 — RSS runtime integration is sufficient close authority；generic test harness waits for a second pressure

- **Acceptance decision**: the real-transport HTTP double → source/job → migrated PostgreSQL graph → storage/
  resolver → source-state journey，combined with real-format semantic bytes、migration/PostgREST probes and full
  core-py/client-web regression，is sufficient acceptance authority for the RSS MVP。
- **Observation boundary**: this is business-runtime vertical integration rather than a full deployment/process-level
  public-API black box。Opt-in live RSS/Atom smoke was not selected in the final run and proves only fetch/parse when
  enabled。Additional transient HTTP、whole-feed malformed、enrichment/storage/resolver failure、process-interruption
  and scheduler exact-one-job probes remain non-blocking future hardening，not retroactive close gates。
- **Infrastructure decision**: retain the already shared hermetic environment and on-demand real-format asset
  generator。Keep RSS protocol routes、identity revisions、job/state assertions and graph cleanup local until a second
  external-source unit proves the same test shape；then extract the smallest common harness without flattening
  source-specific semantics。
- **State consequence**: `rss-extension-hardening` is Complete after Sir's 2026-08-03 review；no acceptance follow-up
  remains active。
- **Confidence**: Sir explicitly accepted the final acceptance scheme and authorized task-packet completion/cleanup；
  the infrastructure boundary also follows the program's two-real-pressure abstraction rule。

## Withdrawn

- 以 `observation`、audit、replay 或“图准入”组织任务。
- O-017 top-level protocol mount：MoeMemos 2.0.4 的 Retrofit endpoints 是 relative paths，登录
  host 保留 path，attachment URL 也在 host path 后追加 `file/...`；配置
  `https://<deployment>/memos/` 即可复用现有 `/{extension_id}` routes。原先“必须占用根级
  `/api/v1`/`/file`”的前提不成立。
- 把 collection / organization / use 建模成信息生命周期。
- 把 block / relation / resolver / storage 联合模型升级为独立前置主线。
- 为了讨论依赖而将 application 移到 organization 之前。
- 把 `SubGraphForm` 当作完整产品模型或 collection 产品产物。
- 把 CanonicalMemo 仅建模为 transient normalized / solved model，而不持久化到 block
  content。
- 为 source-native identity 建立通用 `resource`、opaque `source_key` 或
  `source_block_bindings` 持久模型。
