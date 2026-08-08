# Mail Extension

- **Unit ID**: `mail-extension`。
- **State**: **Active — Technical discussion**。
- **Objective**: 保留 Mail extension identity，把现有 PoC 当作需求与失败证据，先建立可信且尽可能完整的
  communication-record baseline，再让真实邮件场景推动 organization、info-base basic use/query 与
  client-web 的必要演进，使用户能以足够低的成本持有和打理来自多个邮箱的信息。长期目标是让 InKCre
  成为完整的 email client/agent；本轮 delivery scope 仍需单独界定，不把终局愿景一次性塞入实现。
- **Guardrails**: MVP / MLP 由用户 job、所得价值与可接受代价界定，不以邮件协议完整性、字段数量或
  feature checklist 判定；`Message-ID` reconciliation、reply/reference graph、MIME attachment materialization
  等只是候选 mechanism/pressure，不是预设 gate。InKCre 服务生产与创造，不是只读归档镜像；对 source
  状态的改变可以是有意产品行为，但必须服从清晰、可配置的用户选择。Mail vertical 可以推动
  organization、retrieval 与 client-web，但不借此宣称完成这些 capability trunks。
- **Verification**: Product/Technical 尚未冻结；Acceptance 必须以真实 IMAP protocol behavior 驱动
  `source → collect job → committed graph → resolver/use` 黑盒纵切，不能继续让 schema/helper tests
  充当 Mail 产品有效性的主要证据。具体服务、corpus、failure horizon 与静态/运行时分工等待 Acceptance gate。
- **Current Truth**: 现有实现能连接 IMAP、抓取基础邮件并生成 Email/EmailAddress graph，足以作为 PoC；
  它尚无可信的端到端 product acceptance。缺少哪些邮件能力本身不能证明它未达到 MVP，真实 job 是否完成及
  代价是否可接受才是判断 authority。`mark_as_seen` 已是 source config，且其改变邮箱状态是刻意 workflow
  choice，不应先验归类为缺陷。
- **Next Step**: Product scope 已形成完整 candidate；首个 Technical edge 正在
  [solved-content rendering](technical-design/block-rendering.md) 中讨论。`BlockInspector` 与 resolver-selected
  `SolvedContentRenderer` 的 ownership 已分开；generic render context 已撤回。`SolvedContentPopup`、InfoBaseRouter 与
  surface route realization 以及完整 Resolver + solved-content renderer props 已确认。GraphSurface 只是当前 realizer，
  route 不固化 surface；最小 domain routes 已冻结为 `overview | block | solved-content`。InfoBaseRouter 不建立
  第二套 history；它通过内部可替换 adapter 使用 Vue Router/browser 这一既有 authority，且 `back` 必须保留真实
  history traversal 语义；MVP public interface 已冻结为 `current + push + back`。下一步冻结 adapter/URL mapping
  boundary。GraphSurface application URLs 已冻结为 `/info-base/graph`、`/info-base/graph/blocks/:block` 与
  `/info-base/graph/blocks/:block/content`，并直接投影三种 domain routes。下一步冻结 adapter exact contract、
  initialization 与 malformed/unmapped parameters。InfoBaseRouter 已重新定位为由 `@inkcre/core` 提供 contract +
  singleton binding、由各 client 完整实现的 capability port；共享 history adapter/codec 候选已撤回。下一步冻结
  binding/init exact semantics。binding 复用现有 MFImplementation 的 module-scoped set/get/fail-fast 模式，不抽
  generic runtime-binding module。malformed route 由 app not-found 处理；合法 BlockRef 的实体缺失由 surface/view
  加载后呈现，Router 不查数据库。GraphSurface 始终保留 graph；`block` 与 `solved-content` 分别打开
  `BlockInspectorPopup` / `SolvedContentPopup`，popup 自己将 close 解释为 literal back。GraphSurface/ListSurface
  稳定统称 `InfoBaseView` navigation hosts，并通过 route destination outlet 实现 routes。下一步冻结 focus 与 loading
  owner。InfoBaseRoute 已冻结为 GraphSurface 唯一 focal-Block authority；GraphSurface 合理理解 stable route.name 并
  实现 focus/outlet，删除本地 selected-Block identity。两个 popup 只接收 BlockRef 并各自拥有 Block loading/missing
  lifecycle；SolvedContentPopup 还拥有 Resolver/solving/refresh/dispose。下一步冻结 route-ref change lifecycle。
  route-ref change lifecycle。Mail identity 已转入
  [mail identity and remote occurrence](technical-design/mail-identity.md)：协议不能保证一 Source 对应一个独立 remote
  account，只能保证它代表一套 local IMAP access context。collection candidate 改为 exact occurrence locator →
  `Message-ID` reconciliation → create Block；`Block.id` 是 local identity 而不是 reconciliation rung。D-239 已冻结
  MVP `OBJECTID/MAILBOXID` consumption：authentication 后至多一次 CAPABILITY query，MAILBOXID 随既有
  SELECT/EXAMINE 返回；bare value 不跨无法证明 comparable scope 的 Sources 比较。D-240 确立了 Source graph anchor、
  Mailbox identity 在 Mailbox Block、occurrence UIDVALIDITY/UID 在 Email–Mailbox membership 以及 Source state 不持有
  collected-item ledger；其 mandatory Source Block timing 已由 D-245 放宽为 lazy anchor。
  D-241 已冻结 canonical chain 为 `Source --manages--> Mailbox --contains {UIDVALIDITY, UID}--> Email`；直接采集对象
  使用 `Source --collects--> item`。active direction 是 representational-normalization common pattern，不是 Relation
  validation rule。D-242 已冻结 operational Source 删除后保留 Source Block、provenance relations 与 collected graph；
  relation 不证明 live credentials/readiness。D-244 经 ROI 复审撤回 D-243 的 shared identity：`sources.id` 保留，
  Source Block 使用独立 BlockRef。D-245 随后将 `sources.block` 冻结为 nullable unique FK，只有 producer 首次需要
  provenance endpoint 时才由 SourceManager 并发安全地创建 `core.source.v1` anchor；Source 创建继续是普通单表
  操作，不引入 `create_source` RPC。D-246 又纠正了 D-244 的 authority inversion：SourceModel 始终拥有
  id/type/nickname 等 Source facts；Block content 的
  `{id,type,nickname}` 只是为 `core.source.v1.get_label/get_text` 与历史可读性服务的 projection，不接管 authority。
  D-247 已冻结 `SourceManager.ensure_block(source, session)`：锁 Source row，在 caller transaction 内创建/复用 anchor
  并同步当前 projection，不另加 refresh flag。D-248 已将 Mailbox 永久定义为 Source-scoped observed Block；不同
  Sources 不合并 Mailboxes，只让 exact occurrence / Message-ID reconciliation 复用有实际收益的 Email Block。
  D-249 已冻结 `extensions.mail.mailbox.v1` canonical content：`name/delimiter/attributes/scoped mailbox_id`；不复制
  SourceRef、occurrence、counts 或 namespace facts。D-250 将 Canonical Email root 收窄为
  `{message_id,subject,authored_at}`，text/HTML body 变为 semantic content Blocks，attachment/inline MIME parts 变为
  metadata Blocks 并在 materialize 后指向 semantic content；同时冻结 source-native decomposition / “collect graph，
  not just Block” common pattern。下一步冻结 exact body/MIME-part relation grammar 与有价值的 MIME ordering/grouping；
  unresolved references、内部 checkpoint/failure 与其余 graph vocabulary 随后讨论。

## Confirmed Product Foundation

- InKCre 的根本目标不是预先回答每条信息最终产生什么具体知识，而是显著降低收集、整理和基本使用
  info-base 的成本，让信息规模积累有机会产生质变。
- info-base 持有的是 information；knowledge 只能存在于用户脑内。只有被用户理解并用于价值落地的
  information 才成为 knowledge，PRD 不应混用二者。
- Mail 相比继续枚举低优先级新 source 具有更高的真实用户价值。Sir 已拥有多个待管理、收集的邮箱，能够为
  collection、organization、query 与 client-web 提供真实 corpus 和产品压力。
- Mail 的长期产品终点不是只读 collector。InKCre 应尽可能持有完整通信记录，并最终成为完整的 email
  client/agent，形成收集、理解、组织、查询与邮件行动的闭环。incoming、sent、archive 等具体纳入范围和
  remote actions 仍由每轮 delivery scope 逐步确定。
- 已批准的纵切是：

  ```text
  real mail sources
    → trustworthy collection baseline
    → persisted mail graph + resolver/use representation
    → mail-demanded organization and info-base query improvements
    → necessary client-web journey
  ```

- 旧实现只提供 evidence，不约束 incrementally patch 还是 behavior rewrite；该选择等待 Technical/preflight
  evidence。

## Accepted Current Delivery Scope

- 尽可能完整地持有多个邮箱账号的 communication records，而不是只做 INBOX intake。
- Source setup 默认不自动收集历史邮件；ordinary collect 只面向 setup boundary 之后产生的信息。用户通过
  显式、可指定边界的 `backfill` collect 收集历史记录；backfill 是 collect 的特殊 intent，不是平行能力，
  也不复用含混的 legacy `full` 语义。
- 让邮件通过 resolver/use、邮件 journey 所必需的 minimum basic query 与 client-web surface 被实际使用；这些
  横向实现不自动关闭完整 feature-retrieval 或 graph-navigation units。
- 保留并验证可配置 `mark_as_seen`，把它作为本轮有意的 remote Mail action。
- 暂不实现 compose、reply、send、draft lifecycle 或 agent outbound execution；它们作为同一 Mail ownership
  unit 的 future delivery scopes 重新过 gate。
- 设计可以保留通往完整 email client/agent 的路径，但不得以 future compatibility 为由提前创建泛化 action
  framework。

## Accepted Account and Mailbox Boundary

- 一个 Mail Source 表示一个邮箱账号，不按 folder 拆成多个 Sources，也不把多个账号隐藏在一个 Source identity
  后面。
- 默认追求完整 communication record：纳入 inbox、sent、archive 与用户创建的 folders；drafts、spam、trash
  是默认排除类别。具体 provider 的 label/folder 映射属于 adapter。
- Mail extension config 持有 deployment-wide 默认排除规则；Source config 可以配置自己的排除规则，其初始
  默认值来源于 extension config。create-time defaulting、reset-to-default 与 update merge 语义留到 Technical
  gate；默认排除不等于永久不支持。

## Accepted Remote Deletion Boundary

- Mail Source 拥有远端删除策略；默认只删除 Email–Mailbox membership relation，不向 InfoBase 提交删除 email
  graph 的命令。InfoBase 不理解邮件或自行判断保留。
- graph 只表达当前已知 membership，不新增 `has been deleted from` tombstone relation。Source sync state 负责记录
  change processing progress；exact relation direction/content 留到 Technical gate。
- 可选 synchronized deletion 默认关闭，并且只有协议/server 能提供可信增量删除证据时才考虑；不靠周期性
  全 mailbox traversal/diff 实现。

## Accepted Mutable Mail Facts

- ordinary collection 持续同步 Email–Mailbox membership 与相关 remote state；同步失败不使已收集 Email content
  失效。
- Mailbox 是独立 Block；membership 由 Relation 表达。move 删除旧 relation 并增加新 relation。
- tag-like flags/keywords 是独立 Mail Flag Blocks，通过 Relations 连接 Email，不进入 Email root content。
- Seen、Answered 与 tag-like flags 是不同 canonical semantics；其 exact graph shape 留到 Technical gate，不照抄
  provider/protocol wire grouping。

## Accepted Collection Freshness

- 本轮提供 manual 与 scheduled collection；scheduled collection 通过创建 ordinary collect job 实现，不存在另一个
  scheduler-owned collection semantic。
- collection frequency 可配置；当前不要求 IMAP IDLE 或 near-real-time long-lived connection。
- core-py 是当前 executor，不是 Mail extension 的永久 runtime owner。未来有后台能力的 native Peer 可以更高频地
  创建/执行 collect jobs；browser Peer 可以不具备该能力。
- 本轮不提前实现 distributed scheduler、Peer cadence negotiation、job routing 或 duplicate-schedule suppression，
  但 Technical design 不得把 Mail contract 锁死到 core-py-only。

## Accepted Collect Job Boundary

- collect job 是 manual/scheduled Source collection 的 CronJob-like execution envelope，不是 mailbox、page、item 或
  remote source completeness contract。
- Source 内部拥有 traversal、checkpoint、partial effects、failure isolation 与 continuation；generic job 不理解这些
  source-native units。
- Source invocation 按其 shallow public completion semantics 正常返回，job 即 completed；只有异常逃逸、abort 或
  runtime failure 才使 job failed。completed 不承诺同步了多少邮件或完成了哪个 horizon。
- mailbox 局部失败可以在 Source 内部隔离并继续其他工作；不为此给 generic job 增加 mailbox-scoped transaction
  或 `completed_with_errors` outcome。
- job 是 one-shot；completed、failed、aborted 都是 terminal，不 retry/reopen。下一次 manual/scheduled run 创建
  新 job，并由 Source-owned state 决定从哪里继续；不新增 attempt、backoff 或 retry lineage。

## Accepted Attachment Boundary

- collection 创建 attachment metadata graph，但默认不下载实际 bytes，也不写入 Storage。exact metadata/remote
  reference shape 留到 Technical gate。
- 对既有 Email/Attachment graph 持久增加 semantic content Block，可以分类为 Organization enrichment；该分类不
  拥有实现。Mail attachment Resolver 执行/封装 materialization，并可委托 Mail Source/extension 取得远端 bytes，
  再使用 Storage 与 InfoBase 的通用能力。
- 用户打开/下载时临时读取或 stream attachment 是 use；只有 durable graph augmentation 才是 enrichment。
- 当前官方协议/客户端 evidence 不支持“可信 mail client 必然默认持久下载全部附件”的前提；详见
  [evidence](evidence.md)。

## Accepted Body and Inline MIME Boundary

- collection 保存 `text/plain` / `text/html` authored body；exact alternative/canonical shape 留到 Technical gate。
- CID image 等非文本 inline MIME parts 只收 metadata/reference，默认不下载或持久化 bytes。查看时可以按需读取；
  durable materialization 由对应 Mail Resolver 执行，并可分类为 enrichment。
- HTML 引用的远程资源不在 collection 时自动抓取。邮件文本语义可离线使用，但完全视觉 fidelity 可能依赖按需
  网络读取；这是已接受的 trade-off。

## Accepted Reply and Thread Boundary

- collection 将 source-native reply/reference facts 表达为 Email Blocks 之间的有向 Relations；方向是 reply Email
  → replied-to parent Email，exact predicate 留到 Technical gate。
- 不创建 generic Thread Block；thread/conversation view 从 Email relation graph 派生。未来只有 source-native
  thread object 证明独立 information value/identity 时才重新讨论。
- collection 不通过 subject/participants/time 猜测缺失关系；best-effort inferred links 属于 Organization linking。
- target Email 尚未收集时的 faithful unresolved reference 与 later reconciliation 属于 Technical open edge。

## Accepted Client-Web Boundary

- 不建立 Mail 专用 inbox/folder/message-list 浏览页，也不增加 Mail-only query/filter product。
- client-web Mail extension 参考现有 Twitter extension：注册 Email Resolver 与 resolver-owned content component；
  通用 `BlockContent`、Block details、graph/query result surfaces 负责呈现任意 Block。
- Email component 展示正文、participants、mailbox membership、flags、reply/reference navigation actions 与 attachment
  metadata。reply/reference 不渲染为 ordinary links；以“查看回复”等 action 请求 generic UI 跳转到目标 Email Block。exact
  parent/replies labels 与 multi-target interaction 留到 client-web design。
- `SolvedContentRenderer` 是 resolver-selected presentation contract，取代 `contentComp` 与曾提议的
  `BlockRenderer`。`BlockInspector` 提供“查看内容”（即 view solved content）与 rumination 等 current-Block actions；
  它不拥有 domain rendering 或 cross-Block navigation。Email renderer 可以给出 target Block action，但只有
  GraphSurface 决定如何选择、聚焦、定位或 route 到该 Block。
- `BlockInspector`、GraphSurface、solved-content view 与 cross-Block navigation 同属 InfoBase domain；不使用 generic
  render-context callback bag 掩盖这套 domain navigation。InfoBaseRouter 拥有 route/history operations，GraphSurface
  是当前 route realizer，未来 ListSurface 可以实现相同 locations；route 本身不出现 graph/list surface。
  `overview` 表示无 focal entity 的全局视野。Solved content 是由 `SolvedContentPopup` 实现的一等 MVP destination；
  exact surface-independent route vocabulary 是 `overview | block | solved-content`，两个 focal routes 都携带
  `BlockRef`。InfoBaseRouter 不拥有独立 history stack/`InfoBaseHistory` domain module，而通过 router-internal
  replaceable adapter 映射到 Vue Router/browser history；不得用 `push(block)` 模拟 `back`。
  MVP public interface 仅为 nullable read-only `current`、`push(route)` 与 literal `back()`；`current = null` 只表示
  当前 app location 在 InfoBase surface 之外，不是第四种 route；不公开无真实 caller 的 `replace()`。
  GraphSurface application route 通过 `/info-base/graph[/blocks/:block[/content]]` 选择 surface 并投影 domain route；
  adapter 直接从 Vue Router 派生 `current`，不保存 location mirror。
  `@inkcre/core` 只拥有 `InfoBaseRouter` contract 与 singleton implementation binding；client-web 完整实现
  Vue-backed `current + push + back`，GraphSurface/ListSurface/renderers 都是 consumer。共享层没有 state/history/
  route registry，也不引入 `InfoBaseRouterHistoryAdapter` 或 `InfoBaseRouteCodec`。
  binding 使用 `setInfoBaseRouter/getInfoBaseRouter`，未配置 get 时 fail-fast；这是复用 singleton-binding pattern，
  不新增 `createRuntimeBinding<T>()`、registry、optional initialization check 或 hot-swap lifecycle。
  malformed/unmapped app route 不产生 InfoBaseRoute；合法 BlockRef 即使 row 不存在也先产生 route，由
  GraphSurface/`SolvedContentPopup` 加载并呈现 missing outcome，InfoBaseRouter 不访问 persistence。
  `overview` 仅 graph；`block` 为 graph + `BlockInspectorPopup`；`solved-content` 为 graph + `SolvedContentPopup`。
  两个 popup 自己调用 Router.back 关闭，GraphSurface 不把 close 改写成 push 或猜测目标。
  GraphSurface/ListSurface 稳定统称 vocabulary-level `InfoBaseView` navigation host；route-owned destination 因
  dismiss 本身具有 back 语义而例外地自带 popup shell。`SolvedContentView` 已撤回；`SolvedContentRenderer` 保持
  presentation-neutral。
  GraphSurface 直接理解 `InfoBaseRoute.name` 并从 `router.current` 派生 focal Block；`block`/`solved-content` 聚焦同一
  referenced node，`overview` 清除 focus。node click 只 push route，route realization 不反向 push。
  `BlockInspectorPopup`/`SolvedContentPopup` 只接收 BlockRef，各自执行 Block.get 并拥有 loading/missing/error；
  GraphSurface 偶然已有的 Block 不作为 destination input。重复读取若成为真实成本再由 Block cache/manager 解决。
  `SolvedContentRendererProps` 同时提供完整 Resolver 与 typed solved content。
- 完整 email client/agent 是能力方向，不要求复制传统邮箱 UI information architecture。
- `contentComp` 当前名称/接口错误地暗示只渲染 `Block.content`；实际上 renderer 围绕 focal Block，消费 Resolver
  联合 hydrated content 与 local Relations 产生的 solved projection。hydrated content 只隐藏 inline/Storage branch；
  solved content 是 derived use-facing projection，不是 canonical/durable root content。Graph-aware solved projection
  以 `.root` 持有 focal Block canonical parsed content，relation-derived fields 只作为 siblings；exact props 与
  navigation bridge 留在 Technical gate。
- 本轮不预设 generic query increment；只有 preflight 证明现有 generic surfaces 无法合理触达 Email Blocks 时，才
  提议消除该 blocker 的最小 generic query change。

## Gate Status

| Gate | State | Exit condition |
| --- | --- | --- |
| Product | **In progress** | 用户旅程、collection boundary、纳入/排除、成功与可接受代价获批 |
| Technical | Pending | authority、graph、sync/change、resolver/storage、extension/client topology 获批 |
| Acceptance | Draft pressure only | 真实 IMAP 黑盒 authority、corpus、failure/repeat horizon 获批 |
| Implementation Plan + Preflight | Pending | increments、addresses、dependencies 与 branch simulation 冻结 |
| Impact Handshake + Start | Pending | durable/code state diff 获批且 Sir 明确开始 |
| Execute / Verify / Promote | Pending | 实现、证据与 owner-specific durable projection 完成 |

完整决定由 [program decision authority](../../decisions/index.md) 的 D-198–D-250 拥有；本 packet 只保留
unit control 与 approved implications。
