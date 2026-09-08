# BehaviorResolver 的 Agent definition 选择

- **状态**：D-523 accepted Technical contract。
- **问题**：一个直接实现为 BehaviorResolver 方法的 Agent-backed Organization behavior，怎样选择完整 Agent definition；
  同时保持 Job 扁平、rumination 不再成为 `OrganizationManager` 特例，并让精确图命令可脱离 Agent 单独调用。

## 从已接受结构推导

```text
Organization behavior 是具体 BehaviorResolver 上的可执行方法
  -> 自动 Job 和显式 route 都只需调用该方法
     -> 若该方法采用 Agent，必须为本次 deployment 选择一个完整 Agent definition
        -> 现有 AgentManager.run() 以 Agent ID 寻址 persisted definition
           -> 复用现有 DeploymentConfig 保存这项 deployment selection
```

这里没有新的 `ExecutionAdapter` 类、协议或运行层。HTTP route、Peer inbound 和 Job Handler 仍是既有薄调用入口，但它们
不再被包装成一个新抽象；真正的 organization operation 是 BehaviorResolver 方法本身。

## 配置形状与语义

每个首版 Agent-backed behavior 使用独立 key：

```text
core.organization.rumination
core.organization.supersession
core.organization.refinement
core.organization.evidence_stance
core.organization.synthesis
core.organization.existing_referent_anchoring
core.organization.duplicate_assertion
```

每个 exact versioned config schema 的首版值只有：

```json
{"agent": 42}
```

`42` 是对现有 persisted Agent definition 的逻辑引用。definition 自己完整拥有 system prompt、AI model、exact Tool IDs、
tool choice 与 per-turn budget；behavior config 不复制这些字段，也不增加第二份 Tool allowlist。独立 key/schema 允许某个
behavior 日后单独演进，并允许 Extension 注册自己的 `core.organization.<behavior>` 配置，而不建立一个中心 behavior ->
Agent registry。

配置属于具体 BehaviorResolver 的 Agent-backed 运行方法，不属于 Organization 的产品定义，也不属于 behavior descriptor
Block。descriptor 的 exact Resolver type + empty content 仍是稳定图身份；更换 Agent definition 不改变 descriptor ID 或
既有 `candidate for` Relations。

## 直接运行拓扑

```text
ExactJobHandler.handle(max_seeds)
  -> ExactBehaviorResolver.run_automatic(max_seeds)
     -> 读取 core.organization.<behavior>
     -> 选择 seeds / 组装证据
     -> AgentManager.run(config.agent, initial_message)
        -> shared read meta-tools
        -> exact mutation Tool
           -> 同一 BehaviorResolver 的精确图命令
```

Handler 的 `can_handle()` 调用具体 Resolver 的 availability method；Handler 不读取 config、不 import Agent/Thread，也不知道
Tool IDs。Resolver method 读取 config，并通过 `AgentManager.can_execute()` 判断当前 peer 是否能运行该 definition。配置
缺失、Agent 不存在、Tool binding 或 provider capability 不可用时，本 peer 不 claim 自动 Job；真实运行期间发生的共享失败
沿用现有 Job failed/timed-out 与日志/trace。

配置不可用与语义判断后的 `unresolved` / `no-op` 不同：前者表示 operation 没有运行能力，后两者表示判断已经执行但没有
足够依据修改图。

## 方法级依赖，而不是把 Agent 变成图命令前提

一个 concrete BehaviorResolver 可以同时具有两类方法：

```text
Agent-backed orchestration
  run_automatic(...) / ruminate(...)
  -> DeploymentConfig + AgentManager

Agent-neutral semantic surface
  record_candidate(...) / supersede(...) / synthesize(...) / read_lineage(...)
  -> Resolver + retrieval + Graph Navigation + InfoBase
```

因此 concrete BehaviorResolver 允许依赖 Agent runtime，但它的精确 proposal/command/read methods 必须仍可在没有 Agent
definition、Agent Tool registry 或 AI provider 的情况下直接调用和测试。Agent Tool 只是这些方法的调用者，不是唯一 API。
Resolver base、ResolverManager 和普通 information content Resolvers 都不反向依赖 Organization 或 Agent。

这个区分替代了两个错误极端：既不为了“Agent-neutral”再造 ExecutionAdapter，也不把 exact mutation 变成只能由 Agent
触发的内部实现。

## Rumination 迁移

当前 `OrganizationManager.ruminate()` / `ruminate_local()` 混合了 route、证据组装、deployment config 和 Agent 调用。
本 unit 将 rumination 与其它六个 behavior 对齐：

- 新增 graph-addressable `RuminationBehaviorResolver`；
- `ruminate(focal_block_id)` 和 bounded automatic method 由该 Resolver 实现；
- 它读取现有 `core.organization.rumination` config，不改变已有配置数据形状；
- HTTP/Peer 入口直接调用该 Resolver method；
- rumination Job 调用同一个 bounded method，并加入 recent/changed、random fallback 与 incoming `candidate for` seeds；
- rumination 不再由 `OrganizationManager` 承载；该迁移不要求删除与本 unit 无关的 media-interpretation 能力。

## Extension 生长

Extension 可注册自己的 exact BehaviorResolver，并自行选择：

- 使用 `core.organization.<behavior>` + Agent definition；
- 使用直接 AI 或确定性实现而不提供 Agent config；
- 是否提供一个调用该 Resolver method 的 exact automatic Job。

Core 不维护 Extension behavior 映射，也不要求所有 BehaviorResolver 继承 Agent-backed base class。共享的是既有
DeploymentConfig、Resolver registration、Agent definition 和 Job mechanics，不是一个新的 Organization runtime。

## 验收要证明的差别

1. rumination 显式 route 与自动 Job 都到达 `RuminationBehaviorResolver` 的同一 operation；`OrganizationManager` 不再承载
   rumination orchestration。
2. 两个 BehaviorResolvers 配置不同 Agent definitions 后，各自只运行自己的 definition；修改一个 config 不改变 behavior
   descriptor、既有 candidate edge 或另一个 behavior。
3. exact Job Handler 不 import Agent/Thread/config，只检查并调用 target Resolver method。
4. exact mutation/read methods 在无 Agent config/provider/Tool registry 时仍可直接调用；只有 Agent-backed orchestration
   methods 需要这些运行依赖。
5. 缺少配置与已经执行后的 unresolved/no-op 可区分；不可用 peer 不 claim Job，运行期失败由既有 Job lifecycle 观察。
6. 测试 Extension 可注册自身 Resolver/config/Job；一个确定性 BehaviorResolver 不被迫提供 Agent ID。

## Accepted material choice（D-523）

1. Agent-backed behavior 复用 `core.organization.<organization-behavior>` deployment config，值只选择完整 Agent definition；
2. organization operation 直接实现为 concrete BehaviorResolver method，不增加 ExecutionAdapter 抽象层；
3. Job/route 薄调用 Resolver method，Resolver 自己读取 config 并按需调用 AgentManager；
4. rumination 从 `OrganizationManager` 迁移到 `RuminationBehaviorResolver`；
5. Agent-backed orchestration 可以依赖 Agent runtime，但 exact graph mutation/read methods 保持可独立调用；
6. config pattern 可被 Extension 复用，但 Agent-backed 不是 BehaviorResolver 的公共基类合同。
