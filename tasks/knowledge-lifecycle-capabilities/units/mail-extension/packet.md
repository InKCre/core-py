# Mail Extension

- **Unit ID**: `mail-extension`。
- **State**: **Complete — implemented、accepted and promoted 2026-08-11**。
- **Objective**: 保留 Mail extension identity，把现有 PoC 当作需求与失败证据，先建立可信且尽可能完整的
  communication-record baseline，再让真实邮件场景推动 organization、info-base basic use/query 与
  client-web 的必要演进，使用户能以足够低的成本持有和打理来自多个邮箱的信息。长期目标是让 InKCre
  成为完整的 email client/agent；本轮 delivery scope 仍需单独界定，不把终局愿景一次性塞入实现。
- **Guardrails**: MVP / MLP 由用户 job、所得价值与可接受代价界定，不以邮件协议完整性、字段数量或
  feature checklist 判定；mail identity reconciliation、reply/reference graph、MIME attachment materialization
  等只是候选 mechanism/pressure，不是预设 gate。InKCre 服务生产与创造，不是只读归档镜像；对 source
  状态的改变可以是有意产品行为，但必须服从清晰、可配置的用户选择。Mail vertical 可以推动
  organization、retrieval 与 client-web，但不借此宣称完成这些 capability trunks。
- **Verification**: Product、Technical、Acceptance 与 R5 plan/preflight 已冻结。2026-08-11 已用 WorkSSD 上从
  official source 构建的 Dovecot 2.4.4、disposable PostgreSQL 和 acceptance-owned `.eml` corpus 通过 J1–J3；
  built client-web + Mail remote + PostgREST + core-py Peer 通过 J4。core-py 通过 Ruff、Pyrefly 与
  `376 passed, 35 skipped`；client-web 完整 `pnpm check` 通过。core-py aggregate gate 只被已定位的 shared-doc
  fenced-Python formatting 阻塞，Hub source correction 已纳入本次 owner-separated promotion。
- **Current Truth**: 旧 PoC Mail behavior 已 hard-cut。当前实现拥有 global typed Job/Cron、Source anchor 与 writable
  Storage policy、protocol-neutral IMAP Adapter、ordinary/backfill collection、canonical Mail graph、exact MIME
  materialization Peer capability、五个 Mail Resolvers，以及 client-web generic InfoBase route/popup/Mail solved-content
  journey。J1–J4 已证明 real protocol → graph → Resolver/Storage → browser，而不是 schema/helper proxy。
- **Next Step**: 本 unit 已关闭。Hub `067c60a`、core-py implementation `d3cded7`、client-web implementation
  `1e69938` 以及两个纯 shared-ref commits（core-py `8e07da8`、client-web `056c265`）已按 owner 分离完成；
  post-bump `pdm run check` / `pnpm check` 均通过。Program 返回 unit-selection gate，不在本 packet 内预选下一个
  active unit。
  Adaptive batching 仅是本 unit 收口阶段的临时协作策略，低风险自然推论不再逐项请求批准。
- **Decision History**: Product scope 已形成完整 candidate；D-263 已冻结 linear Email ladder，D-264 已冻结每一 rung 的
  `zero → continue / one → reuse / many → stop-and-create`，D-265 已冻结 null identity completion 与 non-null
  contradiction rejection，D-266 已据此恢复 Message-ID reference anchor 的 locate/reuse-or-create 与 later
  completion。Mail identity edge 当前关闭；D-268 已冻结 MailFlag canonical content、description authority、name
  normalization 与 observed-FLAGS replacement semantics。D-269 又冻结 scheduled sync 为 QRESYNC → CONDSTORE →
  new-occurrence-only，且禁止用 full UID scan 冒充增量 removal sync。当前澄清 occurrence locator UIDVALIDITY 与空
  Mailbox 也需要的 sync-checkpoint UIDVALIDITY 已由 D-270 以不同 scope/lifecycle 分别冻结在 Relation 与 Source
  state。D-271 又冻结 remote MIME reconciliation safety：Message-ID-only match 一旦涉及 attachment/inline metadata
  就 lazy-duplicate，只有 exact occurrence/scoped EMAILID 或 sparse anchor completion 可以复用；Resolver 不再通过
  metadata 猜测 UID。D-272/D-273 已冻结单一 Mail Source / protocol-neutral Mail Resolver family 作为
  同级调用者依赖 Source config 选择的 Mail protocol adapter，Resolver 不调用 operational Source；
  IMAP 是当前 concrete adapter，未来 POP3 不产生第二套 Source/Resolver domain。D-274 进一步
  冻结 adapter 解释 typed protocol checkpoint 并提出 next-state，Mail Source 独自拥有持久 state、推进时机
  与 accepted-effect boundary。D-275 又明确每个 Source instance 对应一个公开标准 protocol；Source 配置
  不持久内部/versioned adapter ID，当前也不引入 MailManager/adapter registry/catalog。D-276 已冻结
  `protocol` + typed `parameters` + outer common Mail policy 的 config 形状，并将其与 Peer inbound 的同类经验记为
  U-038，但不把公开 protocol 强行变成 InKCre ID。D-277 又将当前 exact `MailProtocol` 收窄为
  `Literal["imap"]`；已知但未实现的 POP3 不进入当前 config validity。D-278 保留极浅的
  `create_mail_adapter(protocol, parameters)` 共享构造 seam，但不引入 Manager/registry/catalog。D-279 已冻结
  factory 无 I/O、每个 Source collect / Resolver materialization command 使用一个 fresh async-context adapter，
  并将语言原生 resource scope 提炼为 U-039。D-280 已冻结 Adapter 对上暴露 canonical Mail
  remote-access/materialization operations 而不是 IMAP primitives，且不生产 graph 或持久 state。D-281
  又纠正 Adapter `collect()` 草案：`Source.collect()` 独占 collection 语义，Adapter 只提供 canonical Mail
  remote read/change/part-fetch operations；exact interface 已委托到 plan/preflight，越过已冻结边界才回讨论。先前的
  [solved-content rendering](technical-design/block-rendering.md) edge 已完成当前设计讨论：`BlockInspector` 与 resolver-selected
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
  account，只能保证它代表一套 local IMAP access context。D-262 已恢复 best-effort canonical Email，同时保留 exact occurrence
  locator 作为 collection idempotency 与 remote-access authority；未知 locator 可以 best-effort 选择现有 canonical
  endpoint。D-263 已冻结 local exact locator → comparable cross-Source exact occurrence → scoped EMAILID → Message-ID
  → create 的线性顺序。`Block.id` 仍是 local identity。D-239 已冻结
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
  Sources 不合并 Mailboxes；D-262 允许不同 Mailboxes 的 occurrence locators 复用 canonical Email Block，但同一
  Mailbox 内的多个 live UIDs 不合并，也不弱化 Mailbox 的 permanent Source scope。
  D-249 的 Mailbox shape 已由 D-258 按 collection-value audit 收窄：`extensions.mail.mailbox.v1` 只保留
  `name/special_uses/mailbox_id`，删除 transient delimiter/generic attributes 与由 `manages` 重复表达的 access
  scope。D-250 将 Email root 收窄为 authored scalars；D-260 加入、D-262 保留 optional server evidence `email_id`，
  形成 `{message_id,email_id,subject,authored_at}`。text/HTML body 变为 semantic content Blocks，
  attachment/inline MIME parts 变为
  metadata Blocks 并在 materialize 后指向 semantic content；同时冻结 source-native decomposition / “collect graph，
  not just Block” common pattern。D-251 冻结 text/HTML body 直接复用 `core.text.v1` / `core.html.v1`，Email-body 角色
  只由 Relation 表达；复用只是边界正确性的信号而非拆分理由。D-259 已按 source-order authority 纠正 D-252/D-253：
  Email → MIME component 统一使用 `{role,part_id}`，MIME tree path 同时拥有结构位置、顺序与 IMAP fetch locator；
  MIME-part Block content 不再保存 part_id/disposition，只保留
  `media_type/charset/filename/content_id/description/transfer_encoding/encoded_size/content_location`。HTML body 对
  Content-ID/Location 的实际引用另建 `{type:"embeds",reference}` Relation。D-254–D-255 冻结纯地址 EmailAddress 与
  `{role,order,display_name}` participant Relations。D-261 在实证比较后撤回 D-260 的 one-Email-per-locator hard cut；
  D-262 又以 plain MailFlag Relations 取代 locator-qualified tags：不同 Mailboxes 可以共享 canonical Email，但同一
  Mailbox/Email pair 至多一个 live `contains`，同-Mailbox duplicate 创建另一个 Email Block。D-263 保留既有 canonical
  reconciliation ladder 并补入 scoped EMAILID rung；D-264 又冻结 exact-one reuse，D-265 冻结 identity
  compatibility 并记录 Source-domain ladder utility 的高 ROI 实现压力。D-266 已恢复 D-256 Message-ID-only
  incomplete Email anchor：zero/many 创建普通 sparse Email，exact-one 复用，later collection 走同一 ladder；不新增
  placeholder lifecycle。

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

## Accepted Access-Context and Mailbox Boundary

- 一个 Mail Source 表示一套 configured IMAP access context/credentials，用户界面可以把它呈现为一个邮箱账号；
  不按 folder 拆成多个 Sources，也不把多套独立配置隐藏在一个 Source identity 后面。但协议不能证明两个
  Source 看见的 remote account/mailbox namespaces 不重叠，因此 Source identity 不参与跨 Source remote identity
  证明；D-239 是对早期“一 Source 一 protocol account”措辞的技术纠正。
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
- `\Seen`、`\Answered`、`\Flagged`、`\Deleted`、`\Draft` 与 observed keywords 都是独立 MailFlag Blocks，通过
  plain `tags` Relations 连接 canonical Email，不进入 Email root content 或 `contains`。owning Mailbox + unique
  Mailbox/Email membership derives the exact locator；它们的产品行为不同，
  但共享 IMAP FLAGS/STORE authority 与 persistence shape；deprecated `\Recent` 不持久化。
- `\Deleted` 存在时仍有 membership；可靠 EXPUNGE 后才删除 exact `contains` 与同 locator 的 flag Relations，不创建
  tombstone。

## Accepted Collection Freshness

- 本轮提供 manual 与 scheduled collection；scheduled collection 通过创建 ordinary collect job 实现，不存在另一个
  scheduler-owned collection semantic。
- collection frequency 可配置；当前不要求 IMAP IDLE 或 near-real-time long-lived connection。
- global Cron 在 deployment timezone 中按当前 minute 由任意 Cron-capable Peer 检查，并以 Cron row lock、
  `last_scheduled_for` 与 `last_job` 保证同一 occurrence 最多创建一个 Job 且不堆叠未完成执行。错过 occurrence 即
  错过，不补跑；run-now 直接创建普通 Job。
- core-py 与打开中的 client-web 都可作为 Job worker，但只 claim 本地 Handler `can_handle(parameters)` 的 Job；
  atomic pending-to-running update 决定唯一执行者。Mail contract 不锁死到 core-py-only，也不引入 request-response
  Peer delegation、generic invoke 或 Job retry。

## Accepted Collect Job Boundary

- collect job 是 manual/scheduled Source collection 的 CronJob-like execution envelope，不是 mailbox、page、item 或
  remote source completeness contract。
- Source 内部拥有 traversal、partial effects、failure isolation 与 continuation；checkpoint 是建议的 interruption-
  resilience 行为而非 Source capability 要求。generic Job 不理解这些 source-native units，也不检查 checkpoint。
- Source invocation 按其 shallow public completion semantics 正常返回，Job 即 `finished`；异常逃逸或 runtime failure
  为 `failed`；执行预算耗尽为 `timed_out`。这些终态都不承诺同步了多少邮件或完成了哪个 horizon。
- mailbox 局部失败可以在 Source 内部隔离并继续其他工作；不为此给 generic job 增加 mailbox-scoped transaction
  或 `completed_with_errors` outcome。
- Job 是 one-shot；`finished`、`failed`、`timed_out`、`aborted` 都是 terminal，不 retry/reopen。下一次
  manual/scheduled run 创建新 Job；支持 checkpoint 的 Source 可从自己的 state 继续，较弱的 Source 可以重扫并
  依赖 identity/reconciliation。不新增 attempt、backoff 或 retry lineage。

## Accepted Attachment Boundary

- collection 创建 attachment metadata graph，但默认不下载实际 bytes，也不写入 Storage。exact metadata/remote
  reference shape 已冻结到 D-259/D-271；不新增 per-part fetch binding，弱 Message-ID reconciliation 通过 lazy
  duplication 保持 remote access exactness。
- 对既有 Email/Attachment graph 持久增加 semantic content Block，可以分类为 Organization enrichment；该分类不
  拥有实现。Mail attachment Resolver 执行/封装 materialization，并与 Mail Source 一样依赖 extension-owned
  shared protocol adapter 取得远端 bytes，再使用 Storage 与 InfoBase 的通用能力；Resolver 不调用 Source
  instance。
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
- D-262 恢复 best-effort canonical Email 后，“Message-ID-only incomplete Email 之后被 occurrence 补全”的 D-256 mechanism
  再次可行。D-266 已明确恢复并约束它：In-Reply-To/References 必须采集；exact-one target 复用，zero/many 创建
  ordinary incomplete Email；later collection 只在 D-263–D-265 允许时原位补全。

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
| Product | **Closed for current delivery** | 新 implementation evidence 或真实 use pressure 才重新打开 |
| Technical | **Closed for implementation** | 新 evidence 若改变 domain ownership、observable behavior 或 accepted graph/runtime contract 才重新打开 |
| Acceptance | **Closed** | D-313/D-314：Dovecot real-IMAP hard gate + 四条纵向 journey + optional provider smoke；本 unit 不增加 focused negative-path suite |
| Implementation Plan + Preflight | **Closed** | D-315：R5 slices、preflight and first extension-owned exact Peer delegation accepted |
| Impact Handshake + Start | Pending | durable/code state diff 获批且 Sir 明确开始 |
| Execute / Verify / Promote | Pending | 实现、证据与 owner-specific durable projection 完成 |

完整决定由 [program decision authority](../../decisions/index.md) 的 D-198–D-315 拥有；本 packet 只保留
 unit control 与 approved implications。
