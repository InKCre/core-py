# Organization Nowledge Vertical — Impact Handshake

> **状态**：accepted by D-527；Sir explicitly authorized implementation on 2026-09-08。

## 要改变的对象

```text
Resolver capability reflection
  From: MCP Sink-local authority
  To: ResolverManager-owned discovery / schema / invocation

Organization runtime
  From: one OrganizationManager-centered rumination module
  To: seven exact BehaviorResolvers + seven independent thin Jobs

Graph query
  From: neighborhood/path only
  To: bounded connected-component query added to the same Graph Navigation owner

Agent surface
  From: rumination graph-authoring Tools only
  To: three read meta-tools + behavior-specific exact writes + one candidate Tool

Rumination carrier
  From: OrganizationManager
  To: RuminationBehaviorResolver; existing HTTP/Peer entry remains stable
```

## 预期副作用与影响面

- `app.business.organization` 从 module 变为同名 package；所有已知 imports 必须保持或显式迁移；
- MCP Sink 内部 imports 改变，但 Resolver method external Tool/Resource result 不得改变；
- Core runtime 增加 Resolver/Tool/Job registration imports 和七个 Job profiles；不自动创建 schedule；
- 图中可以新增普通 Block/Relation：behavior descriptors、candidate edges、六类 exact organization results 与 rumination
  outputs；不新增数据库实体或隐藏状态；
- deployment 需要提供七个 Agent definitions/configs 才能运行对应 automatic behavior；缺失时 Job 保持不可运行；
- fixtures/tests 增加，但 credentialed acceptance 不进入默认 `pdm run check`。

blast radius 限于 `core-py` 的 Resolver、Organization、Graph Navigation、Job bootstrap/profile、MCP adapter 和相关 tests/docs。
不修改 MCP protocol、Peer contract、generic Block PATCH、media interpretation product、Source、Collection、AI provider 或 shared
Hub truth；shared docs 只在实现产生证据后由 Hub-first workflow 单独处理。

## 必须维持的不变量

1. 普通 Block/Relation graph 是 Organization 持久结果的唯一 authority；不新增 behavior state/report/table/registry。
2. `ResolverManager` 管理 reflection；`Resolver` base 和非 Organization Resolvers 不获得 Organization dependency。
3. MCP Sink 与 Organization 都向内依赖 Resolver owner；Organization 不依赖 MCP Sink。
4. Agent 是 concrete behavior 的可替换实现手段，不进入 Graph/InfoBase/Resolver base、exact command 或 Job runtime 的依赖方向。
5. 每种 behavior 保留独立语义、SOP、Job 和 exact write；不合并成 generic evolution/rumination/graph command。
6. exact write 接受模型语义参数，而非任意 Relation content；多写操作遵守 caller-owned transaction 与完整 rollback。
7. append-only/history 是本 unit producer guidance，不全局 enforce，也不改 generic PATCH。
8. relation content vocabulary 由写方 behavior module 负责；不创建 registry。
9. candidate 只表达“值得被某 behavior 考虑”，不命令执行，不保证产生修改。
10. Agent 可从初始 candidates 继续检索、Resolver 读取和图探索；初始集合不是其视野上限。
11. 不依赖 MCP Sink；Extension 可通过注册 compatible Resolver/behavior 影响 Organization。
12. 接受不完美：storage pointer 可能失效、LLM 可 no-op/unresolved、黑盒验收是带 residual 的 best-effort 证据。

## 实施验证

- 每个依赖阶段先运行相应窄检查；最后运行 source lint、typecheck、受影响 suites 与尽可能完整的 `pdm run check`；
- 用真实 PostgreSQL graph journey 验证 connected components 与组合 exact operations；环境不可用则明确保留未验证项；
- 重跑现有 rumination HTTP/Peer observable journey；
- 用 MCP external Resolver discovery/invocation Journey D 验证 authority move 未改变 transport outcome；
- 验证一个测试 Extension Resolver 能通过既有 registration mechanics 被 typed read 和 candidate target 发现；
- 最终 credentialed black-box acceptance 从普通信息写入和 automatic Jobs 开始，由 Sir 审阅 graph/use before-after 与 residual。

## 已知不确定性

- LLM-driven behaviors 在小 corpus 上的实际 precision/coverage，只有实现后的真实 provider run 才能观察；
- 当前 database dev target 和本地 PostgreSQL fixture 不可用，可能限制实现期数据库证据；
- MCP Resolver reflection 目前只有 implementation evidence，没有 checked-in automated regression；
- relation “force” propagation 仍是未来研究方向；本 vertical 只实现明确的 candidate routing 和 synthesis reapplication，不建立
  通用传播引擎。

## 授权边界

D-527 已授权上述范围内的源码、测试与 core-py local durable docs 修改，以及非破坏性的实现验证。它不授权：

- commit、push、PR 或 release；
- 删除/停止现有 database runtime 或 volume；
- 修改 `docs/_shared/**`；
- 创建生产 Agent definitions/configs/schedules；
- 为获得绿灯而修改无关的本地 skill copy 或既有测试环境。
