# Candidate Hub PRD Batch

### Program-level product truth projected to Hub source

- collection、organization、use 的动作边界，以及 indexing 的归属。
- Sink 的产品定义需要从“检索或索引 info-base 内容供 downstream use”收紧为 downstream delivery：
  sink 是相对 source 的能力边界，让 downstream actor 在自己的工作上下文中使用被选择的 info-base information。
  MCP 的首个候选边界是 Agent retrieval of InKCre；写作、设计、编码或 chat 等最终工作类型由 caller 拥有。
  Hub 不建立 generic sink framework，也不把某个具体 sink 的协议/API 提升为产品总合同。
- InKCre 首先降低用户收集、整理和基本使用 info-base 的成本，使 information 的规模积累有机会产生质变；
  它不要求每个 source unit 预先证明某个具体知识产出。info-base 持有 information，knowledge 只存在于
  用户脑内；被用户理解并用于价值落地的 information 才成为 knowledge，PRD 不应混用二者。
- MVP / MLP 由用户 job、所得价值与可接受代价界定，不由协议完整性、数据字段或 feature 数量机械判定。
  对 source system 的状态改变也不天然是错误副作用；它可以是生产工作流的一部分，但应服从清晰、可配置的
  用户选择。该原则当前由 Mail product discussion 提出，等待 unit evidence 后决定最终 PRD 表述。
- Mail 的长期产品方向不是只读邮件 collector：InKCre 应以尽可能完整的 communication record 为信息基础，
  最终成为完整的 email client/agent，覆盖收集、理解、组织、查询与有意邮件行动。该终局不自动把所有
  compose/reply/send、mailbox mutation 或 autonomous-agent behavior 纳入当前 delivery scope。
- 当前 Mail delivery scope 只承诺 communication-record foundation、持续更新、resolver/use、邮件所需 minimum
  basic query、必要 client-web journey 与可配置 `mark_as_seen`；compose/reply/send 作为 future scope 重新过 gate。
- Mail Source setup 默认只开始 forward collection；历史邮件由用户显式运行可指定边界的 backfill collect。
  `collect` 是把系统外部信息带入 info-base 的总动作，`backfill` 是特殊 collect intent，不是平行能力。Legacy
  `full` 不再承载历史收集语义；current-state 与 history-capable Sources 仍拥有不同 source-native boundaries。
- `enrichment` 保留为 Organization 从既有 graph 出发、为改善 use 而增加信息或结构的 approach vocabulary。
  RSS collection-time `full-text enrichment` 应在对应 owner 中纠正为 `full-text acquisition`，不改变其既有
  source ownership 或行为；Mail 入库后展开正文 URL 是 enrichment 的 reference example。
- Source 本身就是 collection behavior 的 owner，不使用冗余的 `source-owned collection`；按上下文称
  collection、source acquisition 或具体 acquisition operation。
- Mail Source—not InfoBase—owns remote-deletion behavior。默认只移除 Email–Mailbox membership relation，不提交
  email graph deletion，也不新增 `has been deleted from` tombstone；opt-in synchronized deletion 默认关闭，且只在
  协议提供可信增量删除证据时考虑，不通过全量遍历模拟。
- Mailbox 与 tag-like Mail Flag 是独立 Blocks；membership/flag assignment 由 Relations 表达。Seen/Answered 不与
  tag-like flags 强行合并，exact canonical graph vocabulary 等待 Technical design。
- Mail manual/scheduled collection 使用同一种 collect-job execution semantic；scheduler 只创建 jobs。本轮不要求
  IMAP IDLE。core-py 是当前 capable executor，不是 Extension 的永久 runtime owner；future native Peers 可以拥有
  不同同步频率，但当前不提前引入 distributed scheduler 或跨 Peer cadence coordination。
- Collect job 是 CronJob-like Source invocation envelope，不是 source-internal completeness/transaction unit。Source
  拥有 mailbox/page/item traversal、checkpoint、partial effects 与 failure isolation；job completed 只表示 Source
  invocation 按其 shallow public completion semantic 返回，不承诺某个同步 horizon。
- Collect job 是 one-shot、无 retry lifecycle；terminal 后不 reopen。后续 manual/scheduled invocation 创建新 job，
  Source 仅通过自己的 state 继续收集，不引入 attempts、retry lineage 或 job backoff。
- Mail collection 默认只持有 attachment metadata/remote reference，不下载实际 bytes 或写入 Storage。对既有
  Email/Attachment graph 进行 durable materialization、增加 semantic content Block 可以分类为 Organization
  enrichment，但 Mail Resolver 拥有 materialization 深接口，并可委托 Source/extension 取得 bytes；classification
  不等于 implementation ownership。用户打开时的 transient fetch/stream 属于 use。
- Mail collection 保存 authored `text/plain`/`text/html` body；CID image 等 non-text inline parts 只保存
  metadata/reference，查看时 lazy fetch，持久化仍走 Mail Resolver materialization。HTML remote resources 不自动
  抓取，完整视觉 fidelity 可以依赖按需网络读取。
- Mail collection 将 source-native reply/reference facts 表达为 reply Email → parent Email Relations；不创建 generic
  Thread Block，也不按 subject/time/participants 推断。Thread view 从 graph 派生，missing-link inference 属于
  Organization linking。
- client-web 不建立 Mail 专用 inbox/folder/message-list 页面或 Mail-only query UI。Mail extension 参考 Twitter
  extension，通过 Email Resolver/content component 在 generic BlockContent、details、graph/query-result surfaces 中
  渲染 Email Block；完整 email client/agent 是能力方向，不是传统邮箱 UI 复刻要求。
- reply/reference 在 Email renderer 中表现为请求跳转到目标 Block 的 action（如“查看回复”），不是普通 links；只有
  GraphSurface 拥有 target Block selection/focus/route，Block details 只知道当前 focal Block。`contentComp`/
  `BlockContent` 当前名称与接口掩盖 renderer 实际消费 focal Block + Resolver-owned local graph projection，需在
  client-web Technical owner 中纠正。
- `block.resolver` 应被明确为 exact Block behavior contract 的选择，而不只是 decoder/display discriminator；
  client-web Resolver 注册 `SolvedContentRenderer` 呈现 solved projection，`BlockInspector` 通过“查看内容”动作进入
  view-solved-content lifecycle 并保留 rumination 等 current-Block commands。PRD 保留 Block/Resolver 的产品含义，
  Product TDD 明确 persisted representation → hydrated content → solved content 的 authority/derivation 边界，
  client-web local architecture 记录 controller/renderer/Inspector/GraphSurface composition 与 target-Block navigation
  bridge。Graph-aware solved content 不得伪装成 canonical root content；`.root` 是 focal Block canonical parsed content，
  relation-derived fields 只作为 siblings。
- BlockInspector、GraphSurface、solved-content viewing 与 cross-Block navigation 属于 InfoBase domain。不要把
  navigation 缩成 renderer callback/context；实现证据应验证一等 `SolvedContentPopup` 与 InfoBaseRouter-like domain
  locations 是否成为正确 owner，并让 GraphSurface 负责 route realization。Module Federation singleton/Resolver
  registration evidence 不能被误读为禁止 `SolvedContentRenderer` 使用完整 Resolver。
- `SolvedContentRendererProps` 同时包含 exact Resolver 与 typed solved content。InfoBaseRouter/GraphSurface/
  SolvedContentPopup 已成为 accepted client-web InfoBase topology：router owns location/history operations，GraphSurface
  是当前 route realizer，SolvedContentPopup owns Resolver/popup lifecycle；route 不以 graph/list 命名 presentation
  surface。surface-independent domain routes 固定为 `overview | block | solved-content`，两个 focal routes 携带
  `BlockRef`；未来 ListSurface 可以实现同一 locations。InfoBaseRouter 不建立第二套 history 或独立的
  `InfoBaseHistory` domain module，而通过 router-internal replaceable adapter 使用 Vue Router/browser authority；
  `back` 保持 literal history traversal。MVP public interface 仅为 read-only `current`、`push(route)` 与 `back()`；
  `current` 在 app location 不属于任何 InfoBase surface 时为 `null`，不是第四种 domain route；不公开无 caller 的
  `replace()`，也不建立 arbitrary extension route registry。GraphSurface application URLs 映射为
  `/info-base/graph`、`/info-base/graph/blocks/:block` 与 `/info-base/graph/blocks/:block/content`；URL 中的 `graph`
  选择 current surface，不进入 domain route。adapter 从 Vue Router 直接派生 current，不维护 location mirror。
  InfoBaseRouter 的 shared topology 不是 history/codec composition：`@inkcre/core` 只拥有 fixed contract 与 singleton
  implementation binding，各 client 完整实现自己的 navigation projection；GraphSurface/ListSurface/renderers 是
  consumers。共享层无 route/history state 或 route registry，已撤回 shared `InfoBaseRouterHistoryAdapter` 与 codec。
  Singleton binding 使用已有 MFImplementation 同类的 module-scoped set/get/fail-fast pattern；不要因为两个实例就
  抽出 generic runtime-binding helper/registry。缺失 binding 是 bootstrap composition error，不是 optional state。
  InfoBaseRouter 只验证/投影 client route syntax，不查询 Block existence；malformed/unmapped location 归 app-level
  not-found，合法 BlockRef 指向 missing row 时由 GraphSurface/SolvedContentPopup 的加载生命周期呈现。
  GraphSurface 对三种 route 的 realization 是 graph-only、graph + `BlockInspectorPopup`、graph +
  `SolvedContentPopup`；一等 destination 不等于页面。popup 自己拥有 close 并调用 literal Router.back，surface 不猜
  parent route。GraphSurface/ListSurface 稳定归类为 `InfoBaseView` navigation hosts，并以 route destination outlet
  实现 route。`SolvedContentView` 撤回。
- Product TDD 应沉淀 UI container/content rule：presentation-neutral content 不选择 popup/drawer/card/list item 等
  container，通常由 parent composition owner 组装；只有 container lifecycle 本身成为 addressable route
  destination behavior（例如 dismiss → Router.back）时，destination component 才自带 shell。该规则未来应派生进
  UI agent skill，但 Mail unit 不负责补建尚不成熟的 UI skill build/delivery infrastructure。
- InfoBaseRoute 是 InfoBaseView 的唯一 focal-Block authority；GraphSurface 作为 realizer 正确理解 stable
  `route.name` 并把它映射为 graph focus/outlet composition，不保存另一份 selected-Block identity，也不在 realization
  时反向 push。Vue route name/path 仍只属于 client implementation。
- `BlockInspectorPopup`/`SolvedContentPopup` 的 route input 都是 BlockRef；destination 自己拥有 Block loading、
  missing/error 与 close/back lifecycle，SolvedContentPopup 还拥有 Resolver/solving/refresh/dispose。InfoBaseView 的
  graph/list projection 偶然持有的 Block 不是 popup resource provider；未来只在真实成本下引入 Block cache owner。
- Mail unit 不预设 generic query increment；只有 preflight 证明现有 generic surfaces 无法合理触达 Email Blocks 时，
  才提出移除 blocker 的最小 generic query change。
- memo-like 是独立、多端、低摩擦的 collection surface，用于记录想法、周围事物与零碎
  信息，不承担 info-base 的查阅/use。
- 长期产品方向允许 memo extension 分别支持 backend 与 collector，但两者是独立产品关系、
  独立 deliverable，不共享一个含混的“同步”合同。
- Memos 是首个 memo → graph reference product。
- InKCre 的长期产品事实是不建立 terminal-user、tenant 或 per-user ownership/ACL domain；deployment 是单一
  owner context，多 runtime `client` 是 peers 而不是人类用户。external account/user 只在
  source/protocol 边界拥有其原生语义。
- Extension APIs default to core peer authentication, but an extension may explicitly own its protocol
  route-auth composition；Memos uses an auth-neutral root with separately classified public and
  protocol-protected child routers。This does not create a core User and does not require a Memos
  administration API。Promoted technical documentation must retain a minimal code-shaped example of
  this topology instead of reducing it to prose-only “self-auth mode”。
- Memos credential is deployment-scoped and long-lived by default until explicit replacement/revocation；
  it is ordinary raw extension config with validated merge/persist/live-apply ordering；no refresh-token、
  session or Memos-specific secret lifecycle is introduced。
- Extension enable/disable normally changes route availability in the running single-process deployment；
  restart is not the ordinary activation boundary。

### Memos extension and backend MVP truth projected to Hub source

- implementable ownership unit 是 Memos extension；CanonicalMemo、graph mapping、resolver 与
  product/generation adapters 由该 extension 拥有。Memos-compatible backend 只是首个 MVP
  delivery scope。
- 当前 MVP 是 Memos 0.29.1-compatible backend，MoeMemos Android 2.0.4 是 compatibility
  acceptance client 而非 API authority。
- backend 只实现目标 journey 所需的最小 write/read surface，不复刻完整 Memos server。
- 客户端显示 write 成功代表 primary memo mutation 已持久化；D-041 不保证 graph completeness，
  failure 可留下 orphan/stale components。先行成功上传的 unattached attachment 是独立资源。
- comment 是独立 memo，并以 parent relation 连接；comments 需要独立 fixture，即使当前 APK
  core sync 不调用它。
- flomo backend、collectors、Memos 0.30/older generations、social/share/explore 默认不属于该
  unit。
- Memos current-user/settings 是 deployment-scoped compatibility projection，不新增 User/tenant
  tables，也不把 `ClientModel` 当人类用户。

### Historical product truth no longer blocking

- 当前 backend MVP 没有剩余 Product blocker；其余未决项属于 Technical/Acceptance gates。
- 其他 collection units 的用户可见 partial success、delay、delete 与 compatibility semantics。
- feature retrieval 与 graph-navigation retrieval 已形成各自的稳定合同、implementation evidence and closure；
  future perceptual/hybrid work must reopen through new concrete pressure, not through this historical backlog。

### Semantic retrieval batch projected to Hub source

- semantic retrieval 返回按相似度排序的现有 Blocks/Relations 与 score metadata，不生成 answer、transient chunk
  或 Chat/RAG product behavior；
- organization 保持为改善 use 的 graph mutation；本 MVP 的 explicit rumination 围绕一个 focal Block 反刍，
  可以 additive no-op/增图，但不替代或删除原 Block；
- embedding records 是 profile-scoped、可重建的 use support，information authority 仍是 graph；candidate maintenance
  与 retrieval 分离，stale records 在显式 maintenance 前不可用；
- exact capability discovery 与 invocation 分离；Peer advertisement 只陈述 capability/inbound/lease，业务 facade
  通过 PeerManager 做 opaque delegation，provider inbound 必须进入 non-delegating local path；
- generic capability invoke endpoint、delegation job、readiness advertisement、persistent Agent Thread/checkpoint、ANN/
  HNSW、pagination 和 transient segment layer 均不属于本 MVP；
- Acceptance authority 是经过真实 Memos/RSS/Atom/HTML/storage/rumination 边界形成的 pinned corpus graph；可读 alias
  只属于测试 harness，不进入 production model/API。Deterministic vectors 证明 control flow，不替代 credentialed
  provider semantic-quality authority。
