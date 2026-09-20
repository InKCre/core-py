# Knowledge Lifecycle Capabilities

- **Objective**: 增强 InKCre 的收集、整理与应用能力，使三条 capability action axis 都能由准确的 Core / Extension
  owner 扩展，并让每个可实现单元从产品设计、技术设计、验收、实现计划与 preflight 可审计地进入实现。
- **Guardrails**: 收集、整理、应用是能力动作而非信息状态；block / relation graph 是
  info-base 的持久 authority；Extension contribution 不创建第二套 graph authority，也不因 first-party status 自动
  成为 Core；横切机制只由具体单元的真实压力推动；durable docs 与业务代码
  各自只有在完成对应 Impact Handshake 且 Sir 明确授权实施后才修改，并按 owner 分离操作。
- **Verification**: 每个 active unit 必须拥有自己的可执行验收合同、阶段 gate、Impact
  Handshake 与验证结果；D-049 要求结构性验证优先交给 static mechanisms，runtime acceptance
  black-box-first。Program 完成还要求所有获批 durable truth 回到唯一 owner。
- **Current Truth**: program 拆分和术语基线已经形成；parallel Unit sessions 是平等、默认正交的 owner，没有 standing
  coordinator；parent task 没有统一的 Product / Technical / Execute phase，每个 implementable Unit 独立拥有 delivery
  loop。各 session 维护自己的 Unit packet，并只为本 Unit 的登记、阶段或集成结果最小更新共享 task control。
  InKCre 的长期产品事实是不建立 terminal-user、tenant
  或 per-user ownership/ACL domain；deployment 是单一 owner context，runtime nodes 称为 peers（D-033/D-109）。
  Memos、RSS、Mail、semantic retrieval、feature/lexical retrieval、graph-navigation retrieval 与 Agent Query Sink
  均已关闭；
  能力划分见 [capability-map.md](capability-map.md)，当前状态见本页下方；details stay in each unit packet and the
  [decision register](decisions/index.md)。GitHub extension 的 collection-side correction remains queued, but no longer
  blocks root-usability selection after ownership corrections merged。
- **Next Step**: [Agent Query Sink](units/agent-query-sink/packet.md) 已完成正式交付并关闭；回到下一 implementable
  unit 选择，不从本 unit 的残余自动推导新范围。

## Program Boundary

任务级可复用模式：[Agent Tool 设计与诊断](common-patterns/agent-tools.md)。这是当前 task 的共同设计依据；
具体工具的批准状态与落地仍归对应 unit，不因模式沉淀而扩大实施范围。

- **Collection**: 现有 sources、memo-like、CalDAV、Nextcloud Files、Apple Notes。
- **Organization**: 以改善 use 为目标；breakdown、merge、linking 是已知能力，不是完备枚举。
  Organization 与 Collection、Use 一样是 Extension growth axis；exact contribution seam 必须由获批的具体 behavior
  及其 authority/effect/Acceptance 反推，不预设 generic organization hook。
- **Use / Application**: info-base query 与 sink。Query 包含特征检索、语义检索、图导航检索；indexing 是应用支撑，
  不属于 organization。Sink 是相对 source 的 downstream delivery capability：让 downstream actors 在自己的工作
  上下文中使用被选择的 info-base information，而不接管 graph authority。
- `block.get_hydrated_content()` 统一提供 actual content；resolver 联合 hydrated content 与 local relations
  得到 use-facing interpretation。这是联合信息语义，不是第四条能力主线。
- Hub 现有内容和 Sir 的判断都是需要核验的证据；二者都不是自证前提。
- deployment-scoped single-owner 是长期产品边界；外部 source account 或协议中的 `user` 不自动成为 InKCre core
  domain user，也不引入 tenant 或 per-user ownership/AC。

## 当前 Unit 的入场

2026-09-20，Sir 选择 `agent-query-sink`，由 AI 组合 info-base 原始查询，服务检索而非下游创作；见
[D-611](decisions/D611-D620.md)。已从干净、与 origin/main 一致的 `676886a` 切出 `feat/agent-query-sink`。
当前已完成实现、Preview、正式发布与 production 复验；Hub #29、Core #111 与 Release #109 已合并，unit 关闭。
环境入口仍为 `AGENTS.local.md` 与 `svc.local.json`。

Organization 保留 D-461–D-570，CLI 保留 D-571–D-610，新 unit 保留 D-611–D-650，不复用历史空号。
已关闭 session 不再持有源码锁，历史授权和 deferred 项也不自动成为新 unit 的实施范围。

[Organization 的 Hub 待提升项](documentation-promotion/organization.md)、语义误判与已知 SQL 性能残余继续保留，
但不是所有下一 unit 的前置任务。涉及已实现 Organization 能力时，先读
[本地 Organization TDD](../../docs/30-unit-tdd/organization.md) 和对应最新 decision，而不是从研究稿重新猜实现。

## Unit 状态与选择

[Agent Query Sink](units/agent-query-sink/packet.md) 已关闭。D-611–D-631 的合同、工具归属、controller/service
与文档 authority 修正均已实现；Preview A1–A4、Hub/Core/Release 合并、Core 0.5.0、CLI 0.2.0、production
stable admission 与已发布 CLI 的有依据查询均已通过。

[CLI sink](units/cli-sink/packet.md) 已关闭，公开接口、实现、四条本地旅程、跨 owner 正式交付及 PyPI 安装
连接生产 Core 的复验均通过。研究依据包括本任务 Agent Tool 模式、xiaoland/svc 的 CLI 实践及一手公开材料。

[MCP sink](units/mcp-sink/packet.md) 已通过 PR #88 合并并关闭。

MCP sink MVP 复用现有 retrieval primitives，让外部 Agent/tool client 检索 InKCre 并取得可用的
block/relation/solved-content context；最终用于写作、设计、编码还是 chat，由 caller 拥有。它不授权 generic sink
framework。

[Organization Nowledge vertical](units/organization-nowledge-study/packet.md) 已完成并关闭。逐项 Nowledge study 与
D-493 transfer audit 是它已完成的 Product phase；D-495 修正了将其误判
为 research-only Unit 的错误，D-496 修正了继续拆 delivery slices 的错误。整组实现及多轮真实 preview/provider
验收已执行；PR #100 已随 `915be5a` 合入 main，Release PR #101 的 `b3ccb00` 已完成 Core 0.2.0 生产发布、
探针及 stable 接纳，unit 按 D-562 关闭。Parent task 保持 active，Hub promotion 未被隐含标记为完成。
递归环检测已修复；D-561 的 lineage 同步读取
线程修正已推送，小图实际读取与并行健康响应通过，临时资源已清理。已知 SQL 性能问题延期，不增加大图验收门槛。
整组 Job 均结束不等于所有 seeds 或图语义正确；保留语义误判、预算耗尽
未观测项与未覆盖输入的残余，不能写成
整组语义验收通过。内部平行行为不获得独立 phase/gate。

[GitHub extension](units/github-extension/packet.md) 的首轮实现和真实账号 acceptance 已随 PR #80 合并；durable
owner 与 core/Extension catalog 错误已由独立 correction 关闭，但 batch graph interface、PyGithub integration、
Extension-local Unit TDD 与 re-acceptance 尚未落地。它保留为候选，不代表已选为下一 unit，也不视为完成。

[Graph navigation retrieval](units/graph-navigation-retrieval/packet.md) 已完成 core-py PR #78、client-web PR #85、
`@inkcre/ui-web@1.4.0`、preview/production acceptance 与 durable closure。

[Feature retrieval](units/feature-retrieval/packet.md) 已完成实现、J1–J7、真实 NASA/DashScope、core/client promotion、
独立 Render + Neon fork/cold-start 与 exact-main Pages delivery 验收；perceptual/hybrid future pressure 不重新打开其
已关闭 lexical increment。

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

每个 session 同一时刻最多推进一个 active Unit；parallel sessions 是默认正交的 peers，program 可以在
[parallel roster](collaboration/roster.md) 中声明
多个并行 active Units。每个 Unit 必须拥有独立 branch/worktree、decision range、owner surface 与 dependency/overlap
说明。supporting documents 不维护独立 phase 或 `Current question`；它们由 unit packet 路由。

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
  behavior。优先由静态机制证明可机械检查的事实；需要动态证据时，先以真实 transport + persistence 的手工或
  脚本化 black-box journey 验证，反复成熟且证明回归收益后才考虑提升为自动化测试。新增自动化测试需要 Sir
  显式批准；white-box fixture 只有在 D-049 exception 成立时保留。
- Implementation-plan probe 可以在 Technical/Acceptance 审查中提前展开增量、代码地址、依赖与
  验证顺序，用它暴露遗漏的设计；此时它不授权实现。
- Preflight 可以在 design probe 后执行，核实版本、地址、运行环境并遍历实现分支；它发现新的
  owner/behavior 时必须退回相应 Technical/Acceptance gate，而不是把问题留到 Execute。
- 只有 Technical/Acceptance 获批、preflight 暴露的 questions 关闭后，plan 才冻结为 Execution
  baseline。若计划后来又暴露新的 owner/behavior 分叉，继续退回对应 gate。
- Execute 必须同时具备完成的 Impact Handshake 和 Sir 对该 state diff 的明确“开始”。

## Program Navigation

- Collaboration protocol and parallel session control: [collaboration](collaboration/index.md)
- Active design/discussion filter: [design taste](design-taste.md)
- Architecture understanding provenance: [architecture-understanding](architecture-understanding/index.md)
- Capability topology and queued work: [capability-map.md](capability-map.md)
- Single decision authority: [decision register](decisions/index.md)
- Cross-cutting pressures: [pressure-ledger.md](pressure-ledger.md)
- Terminology and repository evidence: [terminology-audit.md](terminology-audit.md)
- Peer terminology migration evidence: [peer-terminology-migration.md](peer-terminology-migration.md)
- Durable-doc promotion queue: [documentation-promotion](documentation-promotion/index.md)

## Retention and Promotion

- Task files are working memory, not durable truth owners。
- An active task packet is nevertheless the current collaboration authority。Cleanup follows the parent task lifecycle；a
  completed child unit、large file count、age or the volatility of `tasks/` does not authorize deleting an active packet。
  Split content when needed，but retain one program control authority。
- 获批决定只在 `decisions/` register 陈述一次；unit/design/evidence 通过 decision ID 或链接引用。
- 讨论中尚未稳定的 durable-doc pressure 只进入 `documentation-promotion/`；design 冻结且 implementation
  提供证据后，按 PRD、Product TDD、Unit TDD 等 owner 形成内聚批次并随 unit closure 应用。Commit/push、
  Hub publication 与 shared-ref bump 仍按 owner 独立授权。
