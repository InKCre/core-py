# Knowledge Lifecycle Capabilities

- **Objective**: 增强 InKCre 的收集、整理与应用能力，并让每个可实现单元从产品设计、
  技术设计、验收、实现计划与 preflight 可审计地进入实现。
- **Guardrails**: 收集、整理、应用是能力动作而非信息状态；block / relation graph 是
  info-base 的持久 authority；横切机制只由具体单元的真实压力推动；durable docs 与业务代码
  各自只有在完成对应 Impact Handshake 且 Sir 明确“开始”后才修改，并按 owner 分离操作。
- **Verification**: 每个 active unit 必须拥有自己的可执行验收合同、阶段 gate、Impact
  Handshake 与验证结果；D-049 要求结构性验证优先交给 static mechanisms，runtime acceptance
  black-box-first。Program 完成还要求所有获批 durable truth 回到唯一 owner。
- **Current Truth**: program 拆分和术语基线已经形成；InKCre 的长期产品事实是不建立 terminal-user、tenant
  或 per-user ownership/ACL domain；deployment 是单一 owner context，runtime nodes 称为 peers（D-033/D-109）。
  Memos、RSS、Mail、semantic retrieval、feature/lexical retrieval 与 graph-navigation retrieval 均已关闭；
  current summaries live in [capability-map.md](capability-map.md)，details stay in each unit packet and the
  [decision register](decisions/index.md)。GitHub extension 的 collection-side correction remains queued, but no longer
  blocks root-usability selection after ownership corrections merged。
- **Next Step**: 进入 [MCP sink](units/mcp-sink/packet.md) product discussion。当前 selection premise 是：
  info-base query 三类基础 primitive 已经具备；为了让 InKCre 更可用，下一缺口更可能是 sink。MCP sink MVP 的边界是
  **Agent retrieves InKCre**，不是写作、设计或其他最终工作类型。This does not authorize or imply a generic sink
  framework。

## Program Boundary

- **Collection**: 现有 sources、memo-like、CalDAV、Nextcloud Files、Apple Notes。
- **Organization**: 以改善 use 为目标；breakdown、merge、linking 是已知能力，不是完备枚举。
- **Use / Application**: info-base query 与 sink。Query 包含特征检索、语义检索、图导航检索；indexing 是应用支撑，
  不属于 organization。Sink 是相对 source 的 downstream delivery capability：让 downstream actors 在自己的工作
  上下文中使用被选择的 info-base information，而不接管 graph authority。
- `block.get_hydrated_content()` 统一提供 actual content；resolver 联合 hydrated content 与 local relations
  得到 use-facing interpretation。这是联合信息语义，不是第四条能力主线。
- Hub 现有内容和 Sir 的判断都是需要核验的证据；二者都不是自证前提。
- deployment-scoped single-owner 是长期产品边界；外部 source account 或协议中的 `user` 不自动成为 InKCre core
  domain user，也不引入 tenant 或 per-user ownership/AC。

## Active Implementable Unit

[MCP sink](units/mcp-sink/packet.md) 是 active implementable Unit，当前处于 product discussion。

MCP sink MVP 复用现有 retrieval primitives，让外部 Agent/tool client 检索 InKCre 并取得可用的
block/relation/solved-content context；最终用于写作、设计、编码还是 chat，由 caller 拥有。它不授权 generic sink
framework。

[GitHub extension](units/github-extension/packet.md) 的首轮实现和真实账号 acceptance 已随 PR #80 合并；durable
owner 与 core/Extension catalog 错误已由独立 correction 关闭，但 batch graph interface、PyGithub integration、
Extension-local Unit TDD 与 re-acceptance 尚未落地。该 unit 当前是下一轮 selection 的优先候选，不视为完成。

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
