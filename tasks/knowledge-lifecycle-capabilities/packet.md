# Knowledge Lifecycle Capabilities

- **Objective**: 增强 InKCre 的收集、整理与应用能力，并让每个可实现单元从产品设计、
  技术设计、验收、实现计划与 preflight 可审计地进入实现。
- **Guardrails**: 收集、整理、应用是能力动作而非信息状态；block / relation graph 是
  info-base 的持久 authority；横切机制只由具体单元的真实压力推动；durable docs 与业务代码
  各自只有在完成对应 Impact Handshake 且 Sir 明确“开始”后才修改，并按 owner 分离操作。
- **Verification**: 每个 active unit 必须拥有自己的可执行验收合同、阶段 gate、Impact
  Handshake 与验证结果；D-049 要求结构性验证优先交给 static mechanisms，runtime acceptance
  black-box-first。Program 完成还要求所有获批 durable truth 回到唯一 owner。
- **Current Truth**: program 拆分和术语基线已经形成；当前产品不建立 terminal-user、tenant
  或 per-user ownership/ACL，deployment 是单一 owner context，其中的 InKCre runtime nodes 统一称为
  peers（D-033/D-109）。[Memos extension](units/memos-extension/packet.md) backend MVP 的 Product、Technical、
  Acceptance、Implementation、official APK E2E 均已完成，core-py commit 是 `304a5c8`，独立
  client-web config-path fix 是 `f2ab107`；该 implementation unit 已完成。
  [RSS extension hardening](units/rss-extension-hardening/packet.md) 的 B0–B8 implementation/verification 与 durable
  reconciliation 也已完成，并于 2026-08-03 通过 Sir 的最终验收复审；
  Hub PRD/Product TDD、core-py Unit/deployment docs 与 client-web info-base architecture 已跟随已验证实现投影并
  分别提交为 Hub `48b069f`、core-py `835f89a`、client-web `765b22f`。Hub commit 已随
  semantic-retrieval shared batch 发布，两个 Spoke 也已消费该 published Hub head；final verification 显示 client-web
  remote main 已由外部/自动 push 到 `8324293`，而 core-py main 仍仅本地。core-py push 与 production migration
  仍是独立授权操作。
  RSS hardening 方向与
  black-box-first acceptance strategy 已获 Sir 接受；D-050 固定 feed-authored content / independent
  full-text enrichment authority，D-051 固定保留 extension identity 的 behavior rewrite 与成熟第三方库
  boundary，D-052 固定 full-text enrichment 进入 MVP、默认开启且可关闭，D-053 固定 best-effort exact
  native identity/reconciliation ladder、排除 payload fingerprint，并允许 source config 在罕见的
  unidentifiable item 上选择 create（默认）或 discard，D-054 固定 feed/channel 是独立 information block。
  D-055 固定 feed/channel exact identity ladder，D-056 固定 unidentified-item source-time admission
  watermark 及其非 identity 边界，D-057 固定 enclosure graph、manual extension command 与
  source-configured automatic materialization，并明确下载结果应按语义成为 audio/video/image 等 media
  block，PDF/EPUB/ZIP 也进入 scope，unknown/unsupported fallback 为带 MIME 的 file block。D-058 固定这些
  横向 media/storage/Memos 修正留在同一 RSS unit，D-059 固定 MemosAttachment metadata block → semantic
  content block，并抽象出有适用条件的 common pattern。D-060 固定保留 `content` 的 inline-value/storage-pointer
  条件语义，由 `BlockModel.get_hydrated_content()` 统一延迟读取实际内容并缓存到非映射 private attribute，
  不引入 `storage_pointer` 或 `BlockRecord`。client-web `packages/core` 已证实拥有平行的 Block/resolver/
  storage hydration 实现，因此属于同一横向 contract 的 downstream implementation surface；hydration
  由各 peer 的本地 storage handler 承担，缺失 handler 明确失败，不默认委托 core-py。D-061 同时要求
  client-web 在本轮支持 PostgreSQL binary。D-062 进一步固定 storage 只运输/保存 opaque content bytes，
  resolver 才拥有 image/video/PDF 等信息解释；现有按 content kind 拆分的 HTTP storage types 因而进入重构
  压力面。D-063 将 client-web 范围扩为 create/read/update/delete 的完整 CRUD；D-064 澄清
  `block.updated_at` 只表示 block record 时间，storage 不反向依赖 block，hydrated cache 也不承诺跨实例或
  跨 peer freshness。D-065 固定 instance-local snapshot + explicit refresh 合同；D-066 固定 raw
  Create/Read + relation Update/Delete 的 PostgREST wire shape。D-067 固定 media metadata 按 source、
  storage、resolver、organization authority 分层，不新增 `blocks.metadata`，并将其提升为 common pattern
  候选。D-068 将 S3-compatible storage 排入 future Nextcloud Files unit；RSS 不以超大 enclosure/streaming
  作为验收条件，也不提前增加 streaming abstraction。D-069 撤回跨 extension 的 global classification
  ladder：extension adapter 拥有 evidence policy，`ResolverManager` 只提供 opt-in common mechanisms，不新增
  media module。D-070 固定 Memos `Attachment.type` → normalized MIME → exact resolver ID，unknown → file；
  不做 mandatory byte sniff/mismatch rejection。D-071 固定合法、具体的 RSS `enclosure.type` 为 primary
  resolver-selection evidence，fallback evidence 不覆盖 metadata-block declaration。D-072 固定 Atom materialization 以
  specific HTTP Content-Type 优先于 advisory `link.type`，再调用 adapter-owned fallback。D-073 固定 resolver
  使 graph 可被 application 使用、text/embedding projection optional，并允许受控 lazy graph
  materialization。D-074 进一步固定 ordinary resolution 默认允许 materialize missing graph，显式
  `materialize_missing=False` 得到 read-only attempt；`refresh` 只拥有 cache bypass/replacement 语义，并与
  `recompute`、`invalidate`、relation `include_in/include_out` 形成跨 peer 稳定 vocabulary。Legacy source-job
  `full` 因混合多种 effect 不被提升为通用合同。D-075 固定九个
  `core.<kind>.v1` exact semantic content resolver IDs，abstract text/embedding capability methods，resolver-
  instance invocation，metadata block → semantic content block 命名，以及裸 `text/html/image/video` hard cut-off。
  [Semantic retrieval](units/semantic-retrieval/packet.md) 的 I0–I8 均已实现，core-py closure commit 为 `b80e5fd`，
  client-web closure commit 为 `ca4899c`；pinned corpus、真实 producer/storage/runtime vertical、deterministic
  rumination/ranking、local/delegated Peer journeys、本地 durable projection 以及 DashScope real-provider 6/6
  Acceptance 均已通过。Hub `95c4023` 已发布；core-py `cc8f90a` 与 client-web `8324293` 分别以纯 ref commit
  消费该 exact shared truth。该 implementable unit 已关闭。
- **Next Step**: [feature retrieval](units/feature-retrieval/packet.md) 已完成实现、J1–J7、真实 NASA/DashScope、
  core/client promotion、独立 Render + Neon fork/cold-start 与 exact-main Pages delivery 验收，该 Unit 已关闭。
  Native Extension release 也是已完成的独立插曲。返回 implementable-unit selection，不根据队列编号自动启动下一项。

## Program Boundary

- **Collection**: 现有 sources、memo-like、CalDAV、Nextcloud Files、Apple Notes。
- **Organization**: 以改善 use 为目标；breakdown、merge、linking 是已知能力，不是完备枚举。
- **Application**: 特征检索、语义检索、图导航检索；indexing 是应用支撑，不属于
  organization。
- `block.get_hydrated_content()` 统一提供 actual content；resolver 联合 hydrated content 与 local relations
  得到 use-facing interpretation。这是联合信息语义，不是第四条能力主线。
- Hub 现有内容和 Sir 的判断都是需要核验的证据；二者都不是自证前提。
- deployment-scoped single-user 是当前产品边界；外部 source account 或协议中的 `user` 不
  自动成为 InKCre core domain user。

## Active Implementable Unit

当前 active implementable Unit 是 [Feature retrieval](units/feature-retrieval/packet.md)。Unit 边界容纳 lexical 与
perceptual features；当前只推进第一个可独立设计、实现和验收的 lexical retrieval increment。Graph relationship
recall 与 hybrid composition 分别由 graph-navigation 和后续组合层承担。

[Mail extension](units/mail-extension/packet.md) 的 Product、Technical、Acceptance、Implementation、Verify、Promote
与 owner-separated delivery 均已关闭。
本轮保留 extension identity，把旧实现当作需求与失败证据；先建立可信 collection baseline，再由真实邮件
场景推动 organization、info-base basic use/query 与 client-web 的必要演进。MVP / MLP 由用户 job、价值与
可接受代价决定，不以协议完整性或 feature checklist 代替产品判断（D-198/D-199）。

[Semantic retrieval](units/semantic-retrieval/packet.md) 的 Product、Technical、Acceptance、Implementation Plan、
Preflight、Impact Handshake、Execute、Verify 与 shared-truth promotion 均已关闭。

[RSS extension hardening](units/rss-extension-hardening/packet.md) 已完成，不因 semantic retrieval 消费其
resolver/hydration contract 而重新打开。

[Memos extension](units/memos-extension/packet.md) 已关闭；future collector/product generations 不继承其
backend MVP approval。

同一时刻最多只有一个 unit 标记 Active。supporting documents 不维护独立 phase 或 `Current question`；
它们由 unit packet 路由。

## Delivery Loop

```text
Product contract
  → Technical contract ↔ Acceptance draft ↔ Implementation-plan probe
  → evidence preflight / branch simulation
  → approved Acceptance contract + frozen Execution baseline
  → Impact Handshake
  → explicit “开始”
  → Execute
  → Verify / Promote
```

- **Experimental task-wide discussion loop**：current model reconciliation → authority/scope/lifecycle classification →
  topology and/or multi-execution sequence when behavior crosses owners or time → dominated-option removal → at most one
  credible human fork。A question is an output of unresolved model pressure，not the unit of discussion progress。This protocol
  is under Sir's experiential review and is not a law；see [design taste](design-taste.md)。
- Product 明确用户旅程、范围、非目标、成功和可观察失败。
- Technical 明确 owner、topology、data/API contract、compatibility 与 failure/partial-effect semantics。
- Acceptance 在实现前固定 public/runtime input、持久 graph、resolver/native output、错误与重复执行
  behavior。默认以真实 transport + persistence 的 black-box scenario 证明；white-box fixture 只有在
  D-049 exception 成立时保留。
- Implementation-plan probe 可以在 Technical/Acceptance 审查中提前展开增量、代码地址、依赖与
  验证顺序，用它暴露遗漏的设计；此时它不授权实现。
- Preflight 可以在 design probe 后执行，核实版本、地址、运行环境并遍历实现分支；它发现新的
  owner/behavior 时必须退回相应 Technical/Acceptance gate，而不是把问题留到 Execute。
- 只有 Technical/Acceptance 获批、preflight 暴露的 questions 关闭后，plan 才冻结为 Execution
  baseline。若计划后来又暴露新的 owner/behavior 分叉，继续退回对应 gate。
- Execute 必须同时具备完成的 Impact Handshake 和 Sir 对该 state diff 的明确“开始”。

## Program Navigation

- Active design/discussion filter: [design taste](design-taste.md)
- Capability topology and queued work: [capability-map.md](capability-map.md)
- Single decision authority: [decision register](decisions/index.md)
- Cross-cutting pressures: [pressure-ledger.md](pressure-ledger.md)
- Terminology and repository evidence: [terminology-audit.md](terminology-audit.md)
- Peer terminology migration evidence: [peer-terminology-migration.md](peer-terminology-migration.md)
- Durable-doc promotion queue: [documentation-promotion.md](documentation-promotion.md)
- Track maps: [collection](tracks/collection.md), [organization](tracks/organization.md),
  [application](tracks/application.md)

## Retention and Promotion

- Task files are working memory, not durable truth owners。
- 获批决定只在 `decisions/` register 陈述一次；unit/design/evidence 通过 decision ID 或链接引用。
- 讨论中尚未稳定的 durable-doc pressure 只进入 `documentation-promotion.md`；design 冻结且 implementation
  提供证据后，按 PRD、Product TDD、Unit TDD 等 owner 形成内聚批次并随 unit closure 应用。Commit/push、
  Hub publication 与 shared-ref bump 仍按 owner 独立授权。
