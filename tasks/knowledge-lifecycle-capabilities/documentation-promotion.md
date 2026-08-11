# Durable Documentation Promotion Plan

## Control

- **Mode**: Memos/RSS/semantic-retrieval/Mail shared promotion published。Mail PRD/Product-TDD truth is Hub `067c60a`；
  core-py `8e07da8` and client-web `056c265` consume that exact published head through pure shared-ref commits。The Mail
  implementation/local-doc owners remain separately committed as core-py `d3cded7` and client-web `1e69938`。
- **Apply gate**: unresolved discussion pressure remains here；stable design + verified implementation triggers
  durable projection during unit completion。Commit、push、Hub publication、shared-ref bump 与 production mutation
  remain separately authorized operations。
- **Owner rule**: Hub source、Spoke shared-ref、core-py Unit TDD 与 client-web docs 分属不同
  owner/operation，不混入一个 commit，也不在 `docs/_shared/**` 直接编辑。

## Promotion Test

候选内容必须同时满足：

1. 已从讨论假设升级为获批、稳定且可复用的产品或技术合同；
2. 有一手产品事实、当前实现证据或 acceptance fixture 支撑；
3. 唯一 owner 已确定，不复制同一事实；
4. 不把某个 Spoke 的偶然类名或临时 workaround 升级为共享合同；
5. 与已有 durable claim 冲突时明确写出 `From → To`，不静默叠加。

## Known Corrections to Existing Hub Truth

以下纠错已在 Hub source worktree 中按 owner 应用；本表保留 From → To 的 promotion provenance：

| Existing pressure | Intended correction |
| --- | --- |
| collection 被描述为产生 blocks/relations，同时 organization 又像是把 collected information 转成 blocks/relations | collection 为了持久化 source information 可以拆成 graph；organization 打理**已经存在**的 info-base，以改善 use |
| collection / organization / use 容易被读成信息状态或固定 lifecycle | 三者是对信息执行的能力动作，不新增未经需求证明的 lifecycle |
| breakdown/merge/linking 容易被当成 organization 的完备枚举 | 它们只是已知能力，目标始终是为 use 优化 info-base |
| indexing 容易被归入 organization | indexing 只作为 application/retrieval 支撑 |
| source-native objects 可能被误解成 graph 之外的持久模型 | Tweet/GithubRepo/FeedItem 等通过 blocks/relations 持久化；不建立通用 collected god object |
| resolver 的 `v1` / `v2` 轴被叫作 `generation` | 按开发者惯例叫 `resolver contract version`；这是一致性/自解释修正，不是声称 `generation` 在其他上下文均错误 |
| graph 中的 source/protocol object 被叫作 `wrapper` | 它是普通 block；在拥有与关联 semantic content 有关的 protocol/source-authored facts 时按职责叫 `metadata block`，不新增 wrapper type |

## Candidate Hub PRD Batch

### Program-level product truth projected to Hub source

- collection、organization、use 的动作边界，以及 indexing 的归属。
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
- 当前 InKCre 不建立 terminal-user、tenant 或 per-user ownership/ACL；deployment 是单一
  user/owner context，多 runtime `client` 是 peers 而不是人类用户。external account/user 只在
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

### Product truth still blocked

- 当前 backend MVP 没有剩余 Product blocker；其余未决项属于 Technical/Acceptance gates。
- 其他 collection units 的用户可见 partial success、delay、delete 与 compatibility semantics。
- feature retrieval 与 graph-navigation retrieval 的完整可观察行为与质量门槛。Semantic retrieval MVP 已形成
  稳定合同、real-provider 实现证据和 Hub source projection，不再与另外两类 retrieval 捆绑。

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

## Candidate Hub Product TDD Batch

### Cross-unit contracts projected to Hub source

- block 是基本持久信息单元；block hydration 隐藏 inline/pointer 分支，resolver 联合 hydrated content 与
  local relations 得到 solved/use-facing interpretation，storage 只负责按 pointer 取得 actual content。
- source-specific input 通过 extension mapping 持久化为 block/relation graph；`SubGraphForm`
  是 write form，不是完整信息模型。
- memo root content 直接保存 memo-family `CanonicalMemo`；attachments、parent、references 只由
  graph components/relations 表达，backend read 只消费 resolver solved result。
- attachment relation 默认无序；正文内显式 attachment reference 是位置 authority。Memos 0.29.1
  是已证明的 source-defined order exception，应在现有 relation payload 中保留，不推动通用
  relation schema 变化。
- comment 复用 memo root mapping，并通过 parent relation 连接。
- product API version 与 CanonicalMemo resolver contract version 是正交版本轴；CanonicalMemo decoder
  由 versioned resolver identity 选择，不在 payload/BlockModel 重复 schema version。
- info-base local memo identity 是 `block.id`；不建立 generic `resource`、`source_key` 或 source
  binding table。
- future collector 采用 best-effort exact reconciliation；匹配不足宁可产生可整理 duplicate，
  不得 content/time fuzzy overwrite。
- 复杂度投入应由边际效益而不是理论完备驱动：先识别仍未解决的问题造成的实际损失，再选择能以最低
  dependency/obscurity 成本消除主要损失的机制，并在新增机制的边际收益不再覆盖其维护与错误成本时停止。
  D-056 是 reference pressure：content fingerprint 试图制造更强 identity，却带来 normalization/stability
  成本；独立 source-time watermark 以更弱、显式的保证取得足够的 duplicate reduction。具体 heuristic
  仍不得被描述为 identity、reconciliation 或 correctness proof。
- Cache/effect controls use stable，orthogonal vocabulary across peers：`refresh` bypasses and replaces an existing
  local snapshot from current authority；`materialize_missing` permits creation only when a required derivation is
  absent；`recompute` is an explicit organization command that regenerates an existing derivation；`invalidate`
  discards a cache without reading a replacement。`refresh` itself neither grants AI/graph mutation nor requests
  recomputation。Python uses snake_case and TypeScript uses camelCase。
- New InKCre-owned APIs do not use `force` or `reload` as aliases for `refresh`。Protocol-owned names remain exact，
  including a third-party `force` query parameter。Legacy source-job `full` is not a stable cross-source contract and
  must not be promoted before its mixed scan/reconciliation/order/pagination effects are separated。
- Direct relation selection uses `include_in` / `include_out`（TypeScript `includeIn` / `includeOut`）relative to the
  subject block：incoming has the subject as `to_`，outgoing has it as `from_`；neither option implies recursive graph
  traversal。
- D-039 已关闭 deployment-scoped Memos PAT：ordinary raw extension-config lifecycle、generic validated
  update ordering、exact public profile/v0-status-404 与 immediate replace/revoke。
- D-041/D-042/D-043/D-044 已关闭 partial-graph boundary、CanonicalMemo v1、PostgreSQL binary storage
  与 Memos relation grammar；D-045 要求单独修复 client-web config path；D-046/D-047/D-048 关闭
  owned cleanup、exact fixtures 与 family/product/access-mode extensibility seams。

### Implementation evidence used for promotion

- installed extension decoder retention、unknown resolver explicit failure、core-py route/config runtime
  与 client-web config path 已由 implementation/tests 证明。
- D-047 exact fixtures、D-046 deletion behavior、PostgreSQL binary storage、partial cleanup residue 与
  official MoeMemos APK journey 均有 executable evidence。
- existing `/{extension_id}` route 已由 MoeMemos pathful base URL 复用；route-auth composition、hot
  lifecycle、caller-session graph commands 与 writable storage 已实现。证据仍不支持 top-level mount、
  generic resource binding 或通用 extension/resolver registry redesign。

### Deferred technical scope

- collector scan/webhook/export、cursor、external identity 与 reconciliation。
- flomo/其他 memo product adapters 及其 fidelity contract。
- feature/semantic/graph navigation、index/projection invalidation 与 retrieval UI。

## Spoke Unit TDD Promotion Applied

core-py local Unit TDD promotion 已应用，只记录本仓内部 implementation architecture，例如：

- memo extension package、route/service/resolver/storage/transaction boundaries；
- graph mutation 与 solved result 的 internal contracts；
- auth/config 的 local wiring；
- Memos extension 的 0.29.1 backend adapter 对 missing `updateMask` 的 raw-JSON key-presence
  inference 与 negative
  cases；
- tests、migrations 与 failure/residue handling 的实现真相。

具体 ownership 已投影到 `docs/30-unit-tdd/memos-extension.md` 与更新后的
`business-pipeline-and-authority.md`；临时 implementation observation 未被提升为共享合同。

## Architecture Understanding Log

这些发现保留为 provenance；已通过 Promotion Test 的内容现在由对应 durable owner 陈述，不以本 log 作为
并行 authority。U-009 仍只属于 task/workflow evidence：

- **U-001 — Joint graph semantics**: block/relation/resolver/storage 共同决定信息如何保存与解释。
- **U-002 — Attachment position**: association 默认无序；显式 inline reference 才拥有位置。
- **U-003 — Ordered slots are not linked lists**: `root --slot--> component` 是 slot mapping；
  当前 relation fetchsert identity 也不直接支持只换 `to_` 的 slot semantics。
- **U-004 — Text storage can carry a grammar**: JSON/text 并非天然无结构，但也不会自动获得
  canonical identity、typed query 或统一解释；resolver 不是 relation content 的唯一消费者。
- **U-005 — No historical support is not no version architecture**: 当前 target 已固定 0.29.1；
  future breaking generation 仍需要显式 adapter/generation boundary。
- **U-006 — Family canonical is not a god object**: CanonicalMemo 属于 memo extension，且就在
  graph root content 内；它不与 info-base 竞争 authority。
- **U-007 — Upstream needs evolve core contracts**: 具体 source/use pressure 可以传导到
  info-base、collection、organization、application 与 extension，但必须保留证据链。
- **U-008 — Persistence time and authored time differ**: block row time、memo-authored/source time、
  collection observation time 不得互相替代。
- **U-009 — A plan can be a design probe before it is executable**: 代码地址、依赖和可验收纵切可以
  在 Technical/Acceptance 阶段暴露遗漏合同；只有上游获批且分叉关闭后，才冻结为 execution
  baseline。
- **U-010 — Client base URL participates in route compatibility**: protocol annotations 的 relative
  path 必须与 client 对 configurable host path 的保留/拼接一起判断；不能只看到 `api/v1` 就推断
  server-root mount。MoeMemos 可用 `/memos/` base URL 复用当前 extension namespace。
- **U-011 — Complexity follows marginal utility**: 不以理论上还能更完整为继续设计的充分理由；比较
  unresolved harm、机制覆盖率、dependency/obscurity 与长期维护成本。选择足够有效的低成本机制后停止，
  同时把剩余风险与弱保证写清楚。D-056 的 time watermark 是实例，不是这条方法本身。
- **U-012 — Storage representation is not information kind**: storage 可以把 audio、video、image 或其他
  information 的 actual content 都保存为 bytes；这不使它们成为 `binary block`。block/resolver 按信息语义
  命名和解释，storage 只按 pointer 保存/取得 actual content。RSS enclosure 与 Memos attachment 已形成两个
  当前 reference pressures；PDF/EPUB/ZIP 使用 concrete generations，unknown/unsupported 使用带 MIME 的
  file fallback。
- **U-013 — Metadata block can describe related content**: 当 protocol/source object 拥有可独立使用的
  identity、metadata、role 或 lifecycle 时，使用 `metadata block → semantic content block → storage-backed content`
  分离 provenance、信息语义与物理保存；resolver 联合 graph 投影 native/use-facing value。这两者都是普通
  block 的职责命名，不新增 wrapper 类型；没有独立意义的 input 不机械增加 metadata block。RSS
  enclosure 与 Memos attachment 是当前 reference pressures。
- **U-014 — One block read contract hides conditional persistence**: `block.content` 在 inline block 上是
  actual content，在 storage-backed block 上是 opaque pointer；通用 consumer 通过
  `get_hydrated_content()` 取得 actual content，不自行解释 storage。hydration 可缓存在 ORM 非映射的
  private state，但绝不能覆盖 mapped pointer。该 read contract 取代含混的 real/raw content 双重命名，
  也不为追求字段纯粹性提前增加第二套 block representation。
- **U-015 — Storage mechanics do not define content semantics**: storage type 只描述如何按 pointer
  定位、读取或写入 opaque content bytes；stream 是 bytes 的 execution representation。resolver 才根据
  exact resolver ID、graph 与 metadata 把内容解释为 image/video/audio/PDF 等信息。实现 backing table 不是
  storage type 或 semantic block；不要按 media kind 复制 HTTP/S3/PostgreSQL storage families。
- **U-016 — Metadata follows authority, not a generic container**: protocol/source-declared filename/MIME/length/URL/time
  留在 metadata block canonical content；storage retrieval mechanics 留在 opaque pointer/config；
  content kind 由 exact resolver ID 表达，byte-derived facts 由 solved content 拥有；只有确有长期 use value 的
  derived facts 才由 organization 物化为 graph enrichment。不要仅因 storage-backed block 的 `content`
  被 pointer 占用，就增加无边界的通用 block metadata JSON。
- **U-017 — Effect words name orthogonal controls**: `refresh`、`materialize_missing`、`recompute` 与 `invalidate`
  分别拥有 cache replacement、missing derivation permission、existing derivation regeneration 与 cache eviction
  语义；不能用 `force`/`reload` 把这些 effect 压回一个模糊 boolean。该合同只约束确实提供相应能力的 API，
  不要求所有方法机械增加同一 options bag。
- **U-018 — Relation direction is subject-relative**: `include_in` / `include_out` 是相对 subject block 的 direct
  relation selectors，并在 Python/TypeScript 仅做 casing 投影；它们不是 graph traversal depth/mode。
- **U-019 — Repeated spelling is not yet a common contract**: 多个 source 的 `full` 共享拼写，却混合扩大扫描、
  绕过增量 cutoff、改变顺序与延续分页等效果。Promotion 以稳定语义而非出现次数为准；`full` 当前是待拆解
  vocabulary debt，不是应被固化的 common parameter。
- **U-020 — Conventional version language beats a new synonym**: 当一个轴表达 API、persisted shape 或 resolver
  contract 的 breaking evolution 时，优先使用通行的 `version`，并用限定词说明是哪一种 version；不再用
  `generation` 创造项目内同义词。现有 task packet 中把 product/API/canonical `generation` 当作 `version`
  使用的历史段落属于待批量纠正的 terminology debt，不构成新的领域概念。
- **U-021 — Readiness proves the executable wire contract**: database protocol readiness 不能只检查 schema、
  relation/function names 与 ACL；对 admitted RPC 还要验证 argument names/types、return database type、set/
  volatility shape 和 media-type transport。PostgREST 14 的 raw `bytea` response 需要显式
  `application/octet-stream` domain，而 raw request 只要求 single unnamed `bytea` parameter；这两者不是同一
  capability。内部 trigger/helper function 必须留在 internal schema，不能因为 authenticated peer 需要
  EXECUTE 就进入 public protocol schema。
- **U-022 — Writable storage owns pointer serialization**: application/extension command 只应提交 actual bytes 并
  得到可直接持久化到 `block.content` 的 opaque pointer string；storage handler 自己拥有 internal key → pointer
  grammar。调用者硬编码 PostgreSQL `blob_id` JSON 会让 future S3/Nextcloud storage 反向泄漏进 source domain。
  Python 的低层 caller-session write 可以保留 storage-native key，但 common create seam 应与 client-web 一样
  返回 pointer string。
- **U-023 — Incremental state must name its authority scope**: ETag/Last-Modified 只对产生它们的 configured
  request URL 有效；source-time watermark 只对产生它的 exact feed graph root 有效。cursor/timestamp 本身不是
  可跨 identity 重用的事实，因此 state 同时保存 scope reference（本例为 configured URL 与 feed block ID）；
  config 或 native identity 改变时 reset unrelated heuristic，而不是让旧 cursor 误删/误跳新 source facts。
- **U-024 — Source config change is not proven feed continuity**: RSS feed continuity 依次由 source-scoped native
  feed ID、declared self URL、source-scoped configured URL 证明。无法 exact match 时创建新的 feed root，旧 feed/
  items 保留；同一 declared identity 下 configured URL 可以更新。`source_instance_id` 是 scope，不足以单独
  证明两次外部 information 来自同一 feed。
- **U-025 — Schedules create commands, not hidden effects**: manual collection 与 scheduler trigger 都先创建普通
  PENDING collect job，再由同一个 atomic-claim runner 执行。schedule 是 command creation policy，不应成为绕过
  job diagnostics、status、retry 和 source-state semantics 的第二条 effect path。
- **U-026 — Disclose dynamic schemas progressively**: Agent 初始上下文只提供完成语义选择所需的 compact exact
  identities 与 descriptions；大型、稀疏使用或 runtime-dependent 的具体 input schemas 通过领域专用查询 Tool
  按需取得。不要把所有可选能力的联合 schema 固定注入每次模型调用，也不要为此建立万能反射服务。
- **U-027 — Domain owners produce the canonical downstream command**: 领域实现拥有其输入 schema、description 与
  语义转换，并直接产生下游 authority 接受的 canonical command。Agent/runtime 只提供注册、路由和 typed
  validation；不要复制领域 schema，也不要增加只为跨 Tool 转换而存在的中间 DTO。Resolver-owned
  StarsGraphForm authoring 通过一个领域拥有的 normalizer 产生 canonical GraphForm，而非交给 LLM 转换，是当前
  reference pressure。
- **U-028 — Separate discovery、proposal and commit by effect**: schema/capability discovery、non-persisting proposal
  construction 与 durable mutation 使用不同的窄 Tool 边界；写入集中到唯一明确 command，但不扩大成通用
  capability invocation、通用事务或 delegation job。
- **U-029 — Do not persist or transmit derivable authority twice**: 当一个值可以通过稳定、低成本且无歧义的不变量
  从同一 command/result 推导时，不再添加第二个字段表达它。Resolver draft 的 `id_start` 已固定为 star Block ID，
  因而额外 `entry_id` 只会制造可分歧的重复 authority。
- **U-030 — Models choose semantics；code enforces mechanics**: LLM/Agent 负责需要语义判断的能力选择、关系表达和
  是否提交；领域模块负责 exact routing、schema validation、identifier allocation、结构不变量与持久化。不要
  用模型处理可确定的机械转换，也不要让通用 runtime 接管领域判断。
- **U-031 — Runtime boundary turns raw input into ordinary typed input**: 接收外部/模型 raw payload 的
  framework/runtime boundary 负责把它反序列化、验证为 typed input；随后被调用的函数接收普通 typed/domain
  input，不再用 `validated_input` 命名、`Validated[T]` wrapper 或额外状态重复表达“边界已经验证过”。这不取消
  各层独有的不变量：Pydantic model 继续拥有自身结构约束，后续模块仍可检查自己拥有的不同约束，数据库继续
  拥有 referential integrity。`submit_graph` 与 `draft_graph → Resolver.create_graph` 是当前 reference pressure。
- **U-032 — Batch-local identity solves mutually referencing creation**: 普通 creation Form 不携带数据库生成的
  identity、timestamps 或其他 database-managed state。当一个批量 command 必须同时声明待创建实体并让同批关系
  引用它们时，command envelope 可以引入仅在该 command 内有效的 identity namespace；对于 bigint row identity，
  InKCre 使用非零 signed ID：负数声明待创建实体，正数引用已有实体，零无效。该 exception 属于批量引用机制，
  不把数据库生成字段重新泄漏进所有 base Forms。GraphForm 是当前 reference pressure。
- **U-033 — Spend common-path complexity only for material marginal return**: 当一个更精确的表示要求每个高频事实
  永久携带额外 identity、状态或一致性关系，却只保护罕见边缘情况时，先判断边缘情况能否通过明确的 producer
  invariant 安全、局部地退化。只有退化不造成错误 mutation、信息丢失或 authority 混淆，并且 common path 的
  语义、维护与 use 收益显著时，才选择较简单表示；这不是“忽略 edge case”，而是把复杂度放在实际产生回报的
  分支。Mail 的 plain `tags` + same-Mailbox duplicate non-reconciliation 是当前 reference pressure：罕见情况增加
  best-effort canonical Email Block，而不是让每条 flag Relation 重复 locator 或产生可变状态歧义。
- **U-034 — Identifier usability requires exact-one resolution in an explicit scope**: identifier 不是脱离 namespace、
  comparison scope 与 operation 的绝对标签。一个 reference/reconciliation/mutation boundary 只有在候选经过 scope
  与 eligibility 过滤后恰好解析为一个既有实体时，才能据此复用或修改该实体。零候选表示当前本地无 referent，
  多候选表示当前 scope 内不唯一；两者都不能被 arbitrary first/min-ID selection 隐藏，但 token 仍可作为
  source-native evidence。具体 shallow outcome 由领域 command 决定：继续较弱 ladder、创建、保留 unresolved 或
  skip；common contract 只禁止在非 exact-one resolution 上作用于某个既有实体。Mail D-264 是当前 reference
  pressure。
- **U-035 — Reconciliation completes absence but preserves contradiction；shared ladders own mechanics, not evidence**:
  一个 exact-one candidate 的 identity fact 为空时，可以用后续同 scope 的 non-null evidence 补全；双方同一 identity
  fact 均为 non-null 且冲突时，不得靠覆盖值、继续较弱 rung 或内容猜测掩盖矛盾。若多个 Source 已经重复出现
  strongest-to-weakest ladder，通用 Source-domain mechanism 可以内聚 ordered async execution、candidate cardinality、
  short-circuit 与 rung-labelled typed outcome；comparison scope、evidence meaning、eligibility、compatibility 和最终
  command effect 仍由各领域 owner 决定。Mail D-265 是当前 reference pressure；exact utility API/name 等待
  implementation preflight。
- **U-036 — Locate controls reuse；input kind controls the newly created representation**: identifier/reference ingestion
  先在明确 scope 内 locate existing domain entity；只有 exact-one 才授权复用，zero/many 则不把 ambiguity 隐藏为
  arbitrary choice。若 command 仍必须表达输入事实，它可以创建一个新的领域实体；reference-only observation 创建
  sparse/incomplete entity，full collection 创建完整或可继续物化的 entity，但二者不需要不同的 placeholder type 或
  reconciliation lifecycle。Mail D-266 是当前 reference pressure。
- **U-037 — Judge heuristics by expected harm and recovery topology，not error probability alone**: “猜错概率低”不足以
  证明 heuristic 值得采用；同时评估错误后果、系统能否检测、是否能自动/自然恢复，以及是否把内部歧义转嫁为用户
  纠错操作。不可检测地把错误外部 bytes 持久化为 semantic content，且只能让用户尝试另一个 locator 才可能纠正，
  即使低概率也不应采用。优先选择可见、局部、不会伪造 authority 且可由 Organization 修复的退化，例如产生
  best-effort duplicate。Mail D-271 是当前 reference pressure。
- **U-038 — Keep protocol identity separate from protocol parameters**: protocol 回答“使用哪套通信合同”，
  parameters 回答“如何构造/进入该合同的一个具体 endpoint”；两者 authority、schema 与 consumer
  不同，不应展平或混合在同一 object namespace。Protocol 字段应当判别 parameters schema，但 protocol
  identity 必须忠于其真实 authority：可以是 InKCre-owned exact/versioned Peer wire contract，也可以是公开
  IMAP/POP3 standard，不因结构复用而强行内部化。Peer D-123/D-124 与 Mail D-275/D-276 是当前
  reference pressure。该分离不要求 typed protocol vocabulary 预先列举已知但未支持的标准；Mail D-277
  将当前有效值收窄为 `Literal["imap"]`。
- **U-039 — Bind external-resource lifetime to a domain command with native language scope**: factory 只构造对象、
  不产生 I/O；领域 command 通过语言原生 resource scope 取得、使用并释放外部连接。这使 exception、
  cancellation 和 normal completion 共享一个清理 authority，调用者无需理解 partial connection state；也不应
  在没有实测回报前扩张成 cross-command cache/pool/lifecycle manager。Mail D-279 是当前 reference
  pressure，Python async context manager 是其当前 concrete mechanism。
- **U-040 — Resolve common Source materialization policy through explicit → deployment default → built-in fallback**:
  外部 bytes 的目标 Storage 是 Source-domain local policy，不是具体协议参数。显式 Source 选择优先，其次是
  deployment-scoped 默认 writable Storage；二者均缺失时使用一定可用的内置 PostgreSQL binary Storage。只有
  “未配置”才能进入下一层；已配置但不存在或不可写必须暴露配置/能力错误，不能被 fallback 静默掩盖。Mail
  D-282 是第一个 reference pressure；D-283 将 per-Source explicit reference 提升为 nullable
  `sources.storage`。D-284 进一步确认 code/catalog 能力一致性属于 Storage registry/bootstrap 系统边界，而不是
  通过每次使用时的 defensive getter 重复发现。D-285 将 derived capability projection 固定为
  `storage_types.writable`；Source reference 只能选择其 type 可写的 Storage instance。
- **U-041 — Resolver solving exposes semantic completion，not internal command status**（candidate Product TDD / Unit TDD）：
  `get_solved_content` 返回调用者需要的 use-facing solved content；内部 lazy materialization 是 create、reuse、race
  还是 fetch，不应自动扩大成 public outcome。只有该事实本身属于领域 solved semantics 时才暴露。这个浅完成合同
  应由 Resolver base docstring 与 peer-equivalent contract 拥有，让调用者无需理解深模块内部状态代数。Mail D-288
  是当前 reference pressure。
- **U-042 — Do not let tolerated residue shape the common API**（candidate Product TDD / Unit TDD）：低概率、低损害、
  best-effort 容忍的冗余或竞态残留不是受鼓励的领域行为；不要为了让它“更可预测”而在高频路径散布稳定选择、
  duplicate-aware 分支或专用 utility，否则会把妥协提升成事实上的公共合同。公共深接口应表达正常 use operation：
  例如 InfoBaseManager 的 singular related-Block read 只返回任一满足关系谓词的 Block，不承诺 uniqueness、order 或
  repeat-read stability；use-facing output 的 cardinality 继续服从领域语义，而不是被持久化冗余改写；需要观察全部
  graph facts 的调用者仍使用普通多值查询。该原则不适用于 identity reconciliation/mutation：后者继续要求
  U-034 的 exact-one resolution。Mail D-289/D-291 是当前 reference pressure。
- **U-044 — Match concurrency machinery to expected harm，while keeping the normal result valid**（candidate Product TDD /
  Unit TDD）：即使 deployment 是 single-user，自动化和异步入口仍会产生并发，因此不能假设 race 不存在；但也不因
  理论 race 自动引入 exactly-once、专用唯一约束、回滚协议或复杂 duplicate lifecycle。先保证竞态残留不使正常
  command 失败或改变其领域结果，再用 lock/recheck 等局部机制减少残留；只有损害足以支撑成本时才升级更强保证。
  Organization 可修复低损害冗余，但不能成为 producer 放弃低成本预防的理由。Mail D-287 是当前 reference pressure。
- **U-047 — Derive implementation-owned capabilities once，then enforce durable references at the data boundary**
  （candidate Product TDD / Unit TDD）：当能力由注册的实现类拥有、而持久 reference 的合法性依赖该能力时，
  registry/bootstrap 将实现 contract 投影到 catalog，数据库约束保证引用不会进入不可能状态，普通 use path
  直接依赖这个已建立的不变量。不要让每个 caller 反复 rediscover `isinstance`，也不要让可编辑 catalog 反过来成为
  代码能力的 authority。`WritableStorage → storage_types.writable → sources.storage` constraint 是当前 reference
  pressure（D-284/D-285/D-290）。
- **U-048 — Do not gate primary progress on an orthogonal best-effort effect**（candidate Product TDD / Unit TDD）：先明确
  command 的 primary accepted effect；若另一项配置行为失败既不否定已接受事实、也不妨碍安全推进，而且为了重试它
  会阻塞高价值进度、重复大量工作或引入新的 ledger/retry lifecycle，则该行为应在 primary commit 后 best-effort
  执行并留下有界 diagnostics，而不劫持 progress cursor。只有 side effect 本身属于 correctness boundary 时才允许
  gate。Mail D-310 的 graph/checkpoint 与 `mark_as_seen` 是当前 reference pressure；Memos primary delete + best-effort
  cleanup 提供了较早的同类 evidence。

## Apply Checklist

1. **Memos/RSS implementation done** — confirmed decisions、exclusions 与 acceptance evidence 已冻结。
2. **Hub source projected and published** — PRD claims/workflows、knowledge capability contract、authority/topology
   与 claim matrix 已吸收 Memos、RSS 及 common patterns；`48b069f` 已作为 published `95c4023` 的 ancestor 到达
   Hub main。
3. **Core-py local projected and committed** — Memos/RSS Unit TDD、business pipeline、database runtime v2 与最近
   local guides 已和 implementation reconcile；commit `835f89a` 未编辑 `docs/_shared`。
4. **Client-web local projected and committed** — peer hydration、exact semantic resolvers、PostgreSQL CRUD 与
   safe browser handles 已进入 local architecture；commit `765b22f` 未编辑其 `docs/_shared`。
5. **Verification complete** — Hub `git diff --check` + SVC noop；45 relative links resolved；core-py owner docs
   Ruff-format/repository-lint green；client-web complete `pnpm check` green。Core-py full formatter only retains four
   unrelated pre-existing guide drifts。
6. **Owner-separated publication complete** — Hub 先发布 `95c4023`；core-py `cc8f90a` 与 client-web `8324293`
   随后各自只提交 `docs/_shared` gitlink。client-web remote 后续被观察为已同步；core-py push 与 production
   migration 仍是独立 operation。
7. **Tactical guides repaired** — retired semantic HTTP IDs、raw-content domain terminology、scheduler dual-path、
   Memos attachment v1 与 client-web pointer-rendering docs 已修正。
8. **Semantic retrieval projected and verified** — core-py `semantic-retrieval.md`、business-pipeline and runtime/
   development docs，client-web Peer/runtime architecture，and the Hub source PRD/Product TDD match I0–I8 implementation。
   Credentialed DashScope Acceptance is 6/6；Hub links/diff/SVC noop are green。Hub publication and both exact Spoke
   shared-ref commits are complete without mixing owners。
