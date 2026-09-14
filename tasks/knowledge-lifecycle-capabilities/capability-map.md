# Knowledge Lifecycle Capability Map

本文只解释 program 如何拆分、各能力的价值与压力，以及候选工作在哪里。它不维护 active
phase、当前问题或具体单元的设计；这些由 [program packet](packet.md) 与 active unit packet
负责。

## 1. Decomposition Basis

### Capability trunks

收集、整理、应用是本任务要增强的三组**动作能力**，不是信息状态，也不是一个强制的信息
生命周期。

| Trunk | Goal | Known units |
| --- | --- | --- |
| Collection | 把 source-specific information 可靠地持久化到 info-base | 现有 sources、memo-like、CalDAV、Nextcloud Files、Apple Notes |
| Organization | 打理已经存在的 info-base，以改善 use 效果，而非结构美观 | Nowledge study 的整组组织能力；允许由真实目标发现其他能力 |
| Use / Application | 查询 info-base，并让下游使用被选择的信息 | 特征检索、语义检索、图导航检索；sink vertical；indexing 只是支撑 |

### Vertical implementable units

讨论与实现以一个有明确目标的产品功能组为纵切，可以是具体 source、retrieval mode、sink，或 Nowledge study
这样覆盖多个 organization behavior 的同一实现单元。每个 unit 必须能够独立说明：

```text
Product goal / value / observable behavior
  → input, automatic trigger or explicit request
  → owner and cross-boundary contracts
  → graph / projection / delivery behavior
  → best-effort acceptance
  → 整组功能的实现与约定交付
```

这样拆分的依据是产品价值、明确的责任边界和端到端闭环，而不是文件夹、抽象层或先造公共框架的便利。
Unit 内部行为可分别执行，但不因此拆成独立 delivery slices；验收难度不反过来选择产品设计。

### Cross-cutting pressures

block、relation、resolver、storage、source、extension/registry 与跨仓合同不是第四条主线。
它们只在具体 vertical unit 打破现有假设时进入设计：

`上游需求 → 被打破的假设 → 候选 owner → blast radius → evidence → decision`

压力先记录到 [pressure-ledger.md](pressure-ledger.md)。一个通用机制通常需要两个真实 unit
重复证明；单个 unit 若没有它就无法正确交付，也可以推动最小局部改造，但不能借机设计
万能框架。

## 2. Joint Information Semantics

所有 unit 共享的已确认约束是：

```text
block.content ───────────────┐
                            ├─ resolver ─→ solved / use-facing representation
storage ─→ hydrated content ┤
local relations ────────────┘
```

- block 是 info-base 的基本持久信息单元；source-native Tweet、GithubRepo、FeedItem 等不会
  另外形成并行 durable object store。
- relation 使多个 blocks 形成 graph，并可能参与 root block 的完整意义。
- storage 只负责在需要时按 pointer 取得 actual content；它不是 semantic owner。
- block hydration 隐藏 inline/pointer 分支，resolver 联合 hydrated content 与 local relations 产生明确的
  解释/projection。
- collection 可以为了正确持久化 source information 而拆成多个 blocks/relations；
  organization 则处理已经存在的 info-base，目的不同。

这些语义约束讨论方向，但不预先规定每个 source 的 graph shape。

## 3. Unit 与候选能力地图

| Unit / 候选能力 | 价值与主要压力 |
| --- | --- |
| [Memos extension](units/memos-extension/packet.md) | 原生兼容 backend、memo canonical/graph/read 合同；collector 保留为同一 owner 的后续范围 |
| [RSS extension hardening](units/rss-extension-hardening/packet.md) | source instance → collect job → graph → resolver → state 的 collection 纵切 |
| [Mail extension](units/mail-extension/packet.md) | 真实邮件的 protocol → graph → materialization → InfoBase browser 纵切 |
| [GitHub extension](units/github-extension/packet.md) | 真实账号收集与 Core/Extension 边界；后续修正范围由 unit packet 维护 |
| CalDAV、Nextcloud Files、Apple Notes | 各自暴露不同 access/identity/storage/runtime 压力，不提前压成统一 source framework |
| [Semantic retrieval](units/semantic-retrieval/packet.md) | real-provider 与 local/delegated Peer 上的意义检索 |
| [Feature retrieval](units/feature-retrieval/packet.md) | Lexical 检索；graph facts 与 hybrid composition 保持各自责任 |
| [Graph navigation retrieval](units/graph-navigation-retrieval/packet.md) | bounded neighborhood/path、peer-local topology 与 Graph View |
| [MCP sink](units/mcp-sink/packet.md) | 将已有查询与 Resolver 能力交给下游 Agent/tool client，不预设 generic sink framework |
| [Telegram extension](units/telegram-extension/packet.md) | Telegram 原生交互与信息能力的 Extension 纵切 |
| [Organization Nowledge study](units/organization-nowledge-study/packet.md) | 借鉴思想形成整组功能：rumination 载体迁移、supersession、refinement、evidence stance、synthesis、existing-referent anchoring、duplicate assertion |
| 后续 organization / application 候选 | 先核对已交付能力，再由真实价值与缺口提出范围；不把 breakdown、merge、linking 等宽泛名称直接当成下一 unit |

此表不是排期，也不复制当前阶段。选择与状态以 [parent packet](packet.md) 和对应 unit packet 为准；下一 unit
由 Sir 的目标与实际依赖确定，不按表格顺序自动启动。

### Memo-like queue boundary

- Memo family 的已确定 ownership unit 是 `memos-extension`；已交付的 MVP scope 是 Memos
  0.29.1-compatible backend，MoeMemos Android 2.0.4 是 acceptance client。
- Memos collector 是同一 extension 的 future delivery scope；它会重新打开 external identity、
  reconciliation、cursor 与 delete observation 等问题，但不另建 canonical ownership unit。
- flomo 已校正为正确产品名称，但没有已证明的 official-client replaceable-backend path；
  backend 暂不启动，collector 也不驱动当前 CanonicalMemo v1。
- 未来其他 memo products 通过 product/generation adapter 检验 memo-family canonical
  boundary，不直接复制 Memos shape。

## 4. Why Collection Units Differ

| Unit | Main pressure exposed |
| --- | --- |
| Memos extension / backend MVP | native-compatible API、CanonicalMemo、graph round-trip、deployment single-owner projection、transaction |
| Memos/other collectors (future) | external identity、scan/event reconciliation、cursor、source deletion |
| CalDAV | discovery、sync-token、recurrence、timezone、participants、ETag conflict |
| Nextcloud Files | hierarchy、path vs file identity、rename/move、binary、remote storage、permissions |
| Apple Notes | local macOS runtime、TCC、Notes.app/iCloud eventual sync、offline bridge |

这些压力共同演化 collection 能力，但 source-native semantics 不会为了获得一个统一 schema 而
被压平。

## 5. Discussion and Delivery Order Inside One Unit

每个 unit 使用同一组 gate；approval 顺序稳定，但 supporting artifacts 可以提前作为探针：

1. **Product**：用户旅程、纳入/排除、成功与可观察失败。
2. **Technical**：authority、topology、API/data contract、compatibility、failure/partial-effect semantics。
3. **Acceptance**：native input → persisted graph → resolver/use output，以及错误和重复执行；可在
   Technical 阶段先形成草案以暴露缺口。
4. **Implementation Plan + Preflight**：先形成 design-probing draft，再核实版本、代码地址、依赖、
   环境和失败分支；任何新 owner/behavior 都退回 Technical/Acceptance 讨论，不留到 Execute。
   Technical/Acceptance 获批且 preflight questions 关闭后才冻结为 execution baseline。
5. **Impact Handshake + implementation authorization**：Sir 审查并授权范围后才修改 durable docs 或代码。
6. **Execute / Verify / Promote / Deliver**：实现闭环，核对约定的实际交付终点；稳定 truth 按唯一 durable owner
   提升，跨 owner 尚未完成的事项明确保留，不能由某次合并隐含关闭。

一次聚焦一个关键设计复核面，不机械地每轮制造一个问题。supporting evidence/acceptance/plan 可以提前探索下游
gate，但不能把“已经写成草案”误当作“已经获批”或“可以 Execute”。

## 6. Evidence Boundary

- Hub PRD/Product TDD 含有宽泛的 collection、organization、retrieval 与 extension claims，
  但其中边界可能源自旧设计困境，必须交叉验证。
- core-py 已有 source lifecycle、extension loading、resolver/storage registries、graph
  persistence 与 embedding primitives；具体正确性与承载能力按 unit preflight 验证。
- client-web 有 source/extension 管理与 browser-extension loading，但不能据现状推导完整
  registry 或 retrieval product contract。
- 详细三仓术语/实现证据在 [terminology-audit.md](terminology-audit.md)；讨论结果只在
  [decision register](decisions/index.md) 登记一次。

## 7. Withdrawn Frames

以下内容没有项目术语或已确认需求作为依据，不再用于组织讨论：

- `observation`、audit、replay 或独立“图准入”阶段；
- 把 collection / organization / use 当作信息状态迁移；
- 把 block / relation / resolver / storage 的联合语义升级成一条先于用户能力的工作主线；
- 固定“先写 Hub docs、再造 registry、再批量实现所有 source”的 program DAG；
- 把 `SubGraphForm` 当作完整信息模型或 collection 产品产物。

Durable docs 是获批设计的最终投影，不是讨论顺序的起点。候选更新统一进入
[documentation-promotion](documentation-promotion/index.md)。
