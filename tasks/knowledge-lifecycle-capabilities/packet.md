# Knowledge Lifecycle Capabilities

- **Objective**: 增强 InKCre 的收集、整理与应用能力，并让每个可实现单元从产品设计、
  技术设计、验收、实现计划与 preflight 可审计地进入实现。
- **Guardrails**: 收集、整理、应用是能力动作而非信息状态；block / relation graph 是
  info-base 的持久 authority；横切机制只由具体单元的真实压力推动；durable docs 与业务代码
  各自只有在完成对应 Impact Handshake 且 Sir 明确“开始”后才修改，并按 owner 分离操作。
- **Verification**: 每个 active unit 必须拥有自己的可执行验收合同、阶段 gate、Impact
  Handshake 与验证结果；program 完成还要求所有获批 durable truth 回到唯一 owner。
- **Current Truth**: program 拆分和术语基线已经形成；当前产品不建立 terminal-user、tenant
  或 per-user ownership/ACL，deployment 是单一 owner context，多个 `client` 只是 runtime
  peers（D-033）。唯一 active unit 是
  [Memos extension](units/memos-extension/packet.md)，其 backend MVP Product gate 已通过；
  extension enable/disable 采用同进程 hot route mutation（D-038）；Memos PAT、CanonicalMemo、
  PostgreSQL binary storage、relation grammar、client-web path 与 partial-graph boundary 已由
  D-039–D-045 关闭；D-046–D-048 又关闭 owned deletion、exact fixtures 与 future product/access-mode
  seams。Technical/Acceptance/preflight 已完成，implementation plan 已冻结。
- **Next Step**: Sir reviews the prepared Memos extension Impact Handshake；implementation explicit start
  尚未授予。

## Program Boundary

- **Collection**: 现有 sources、memo-like、CalDAV、Nextcloud Files、Apple Notes。
- **Organization**: 以改善 use 为目标；breakdown、merge、linking 是已知能力，不是完备枚举。
- **Application**: 特征检索、语义检索、图导航检索；indexing 是应用支撑，不属于
  organization。
- `block.content` 或 storage 提供 raw content；resolver 联合 raw content 与 local relations
  得到 use-facing interpretation。这是联合信息语义，不是第四条能力主线。
- Hub 现有内容和 Sir 的判断都是需要核验的证据；二者都不是自证前提。
- deployment-scoped single-user 是当前产品边界；外部 source account 或协议中的 `user` 不
  自动成为 InKCre core domain user。

## Active Implementable Unit

| Unit | Track | Phase | Gate | Next decision |
| --- | --- | --- | --- | --- |
| [Memos extension](units/memos-extension/packet.md) | Collection | Impact Handshake review | Product/Technical/Acceptance approved；Execution baseline frozen | Sir review + explicit start |

同一时刻只有一个 unit 在此表中标记 Active。supporting documents 不维护独立 phase 或
`Current question`；它们由 unit packet 路由。

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

- Product 明确用户旅程、范围、非目标、成功和可观察失败。
- Technical 明确 owner、topology、data/API contract、compatibility 与 failure/partial-effect semantics。
- Acceptance 在实现前固定输入、持久 graph、resolver/native output、错误与重复执行 fixture。
- Implementation-plan probe 可以在 Technical/Acceptance 审查中提前展开增量、代码地址、依赖与
  验证顺序，用它暴露遗漏的设计；此时它不授权实现。
- Preflight 可以在 design probe 后执行，核实版本、地址、运行环境并遍历实现分支；它发现新的
  owner/behavior 时必须退回相应 Technical/Acceptance gate，而不是把问题留到 Execute。
- 只有 Technical/Acceptance 获批、preflight 暴露的 questions 关闭后，plan 才冻结为 Execution
  baseline。若计划后来又暴露新的 owner/behavior 分叉，继续退回对应 gate。
- Execute 必须同时具备完成的 Impact Handshake 和 Sir 对该 state diff 的明确“开始”。

## Program Navigation

- Capability topology and queued work: [capability-map.md](capability-map.md)
- Single decision authority: [decisions.md](decisions.md)
- Cross-cutting pressures: [pressure-ledger.md](pressure-ledger.md)
- Terminology and repository evidence: [terminology-audit.md](terminology-audit.md)
- Durable-doc promotion queue: [documentation-promotion.md](documentation-promotion.md)
- Track maps: [collection](tracks/collection.md), [organization](tracks/organization.md),
  [application](tracks/application.md)

## Retention and Promotion

- Task files are working memory, not durable truth owners。
- 获批决定只在 `decisions.md` 陈述一次；unit/design/evidence 通过 decision ID 或链接引用。
- 讨论中发现的 durable-doc pressure 只进入 `documentation-promotion.md`；按 PRD、Product TDD、
  Unit TDD 等 owner 形成内聚批次后再单独执行。
