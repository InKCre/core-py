# Decision Register

> Task-state decision memory. Hub and code remain the final owners after promotion.

## Index

| Cluster | Decisions |
| --- | --- |
| Program boundaries | D-001–D-007, D-033 |
| Memo-like product and graph role | D-008–D-018 |
| CanonicalMemo, resolver, identity and time | D-019–D-028, D-032 |
| Memos extension and current MVP delivery | D-029–D-031, D-034–D-048 |
| Active Technical questions | None；ready for Impact Handshake |

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
