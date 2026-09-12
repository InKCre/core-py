# Organization Behavior Resolver 与图内执行入口

- **状态**：D-505 accepted Technical contract。
- **纠正**：Sir 所说的“Organization 作为 Resolver 方法”是 `resolver.ruminate()`、`resolver.supersede()`、
  `resolver.synthesis()`，不是只读 `read_candidates()`。代码调查也纠正了“Resolver 是纯读取器”的错误前提：现有
  Resolver 已允许惰性 materialization、AI 辅助和 graph authoring。
- **问题**：实际 Organization logic 应位于信息 Block Resolver、behavior Block Resolver，还是由 Source-like
  projection/pointer 再路由到独立 capability？

## 三种形状的关键差别是分派轴

### A. 信息 Block Resolver methods

```text
Resolver(candidate_block).ruminate()
Resolver(successor_block).supersede(predecessor_block)
Resolver(one_source_block).synthesis(other_blocks)
```

这里按**信息 content type**分派 operation。调用形式自然，但会把两个独立维度绑在一起：

```text
这个 Block 是什么 / 如何解析？      content Resolver 回答
应对它执行哪一种 Organization？     behavior model 回答
```

若放在同一 Resolver，base 必须认识所有 behaviors，或者每个 content Resolver 分别实现它们，形成
`content types × behaviors` 的组合耦合。n-ary synthesis 也没有天然主 source Block；任选一个 receiver 会把集合 operation
伪装成 Block-local 能力。因此，不推荐这个形状。

### B. Exact behavior Block Resolver methods

```text
H --candidate for--> synthesis_behavior_block

ResolverManager.get(synthesis_behavior_block)
  -> SynthesisBehaviorResolver
  -> consider_candidate(H)
  -> consider_synthesis(candidate_set)
```

这里按**Organization behavior**分派，target Block 正是 operation 的诚实 receiver。每个 exact behavior 使用自己的
Resolver type，例如：

```text
core.organization.rumination.v1
core.organization.supersession.v1
core.organization.synthesis.v1
```

concrete Resolver 可以包含实际 orchestration：形成/扩展 candidates、调用确定性逻辑、直接 AI 或 Agent，再调用该
behavior 的 exact graph command。依赖仍保持单向：

```text
Concrete BehaviorResolver
  -> optional Agent / direct AI / deterministic judge
  -> exact behavior operation / graph command
  -> Resolver、retrieval、InfoBase

Resolver base / ResolverManager
  -X-> Organization、Agent、Job
```

也就是说，允许一个 concrete Resolver 依赖外层能力，不等于让 Resolver base 反向依赖它们。actual graph command 仍应
独立于 Agent，使未来其它调用者能够复用。

### C. Source-like projection/pointer

现有 Source 是：

```text
core.source.v1 Block + SourceResolver
  -> SourceModel identity
  -> SourceManager / registered SourceBase
  -> collect()
```

这个额外 pointer 有真实对象可指：Source 拥有多个持久化实例、用户配置、storage 和运行 state，Source Block 只是它们
在 info-base 中的 projection。

Organization behavior 当前没有对应的独立实例或 state owner。若 behavior Block 的 pointer 最终只指向一个
`identity -> callable` code registry，我们就是在 Resolver registry 之外复制第二套分派机制，而 exact behavior Resolver
本身已经能完成同一件事。

因此，首版不推荐 Source-like pointer。只有出现下列具体需要时才增加这一层：

- 同一种 behavior 存在多个持久化实例；
- 每个实例拥有独立配置或 state，且生命周期不同于 Block；
- behavior implementation 可以更换，但同一实例 identity 必须保持；
- 已有 Resolver registration 无法表达所需的 Extension contribution。

## 推荐的最小结构

```text
[information H]
    --candidate for-->
[exact behavior Block]
    resolver = exact behavior identity
              |
              v
ResolverManager.get(target)
              |
              v
Exact BehaviorResolver.consider_candidate(H, execution_context)
    |- rumination:    H 就是 focal input
    |- supersession:  以 H 为 seed 扩展并判断 candidate pairs
    `- synthesis:     以 H 为 seed 扩展并判断 candidate sets
              |
              v
exact graph command -> ordinary Blocks / Relations
```

### Behavior Block

Block 本身就是 graph-addressable behavior descriptor，不再包含一个额外 capability pointer。它的 exact Resolver type
就是稳定、命名空间化、版本化的 behavior identity；content 只保存该 behavior 确实需要的 instance-free 描述信息。
prompt、model、Tools、预算、Cron 和 Job 状态仍属于各自 owner。

### Exact BehaviorResolver

它至少提供：

- `get_text()` / `get_label()`：让 Human/Agent 理解 behavior；
- `consider_candidate(candidate_block_id, execution_context)`：实际处理 `candidate for` seed；
- exact behavior 自己需要的方法，如 `ruminate()`、`consider_supersession()` 或 `consider_synthesis()`。

`read_candidates()` 可以存在，但只是以 behavior Block 为 focal receiver 的便利读取，不是完整 behavior，也不是这个
方案成立的理由。

### 最小 capability detection

不新增第二套 behavior registry 或 `OrganizationBehaviorModel` 表。Organization execution layer 从 Relation target 取得
Resolver，并检查它是否提供 `consider_candidate()`。实现时可以在 Organization owner 内用一个很小的 Protocol 做静态
约束；Resolver base 不需要新增所有 Organization 方法，也不需要认识这个 Protocol。

Extension 已经可以贡献 exact Resolver，因此其新增 Organization behavior 的最小形状是：

```text
exact BehaviorResolver + behavior Block materialization + optional Job/config/Agent definition
```

这让 Extension 能影响 Organization，又不要求 Core 维护 behavior registry、统一生命周期或通用 semantic dispatcher。

## `candidate for` 的运行

Agent 可以谨慎选择任何已经存在、可解析且实现 candidate-consumer capability 的 behavior Block，不限 rumination。
Agent runtime 只注册一个 `record_organization_candidate(information_id, behavior)` Tool。它通过动态 input schema 只接受
已注册 exact BehaviorResolver type，再调用该 class 的共享 `record_candidate(information_id)`；该方法在同一事务中惰性
fetchsert 自身 empty-content descriptor 和精确 candidate Relation。它不能创造未注册 behavior 或提交任意 Relation，也
不会随 behavior 数量增加 Tool。

执行层随后：

1. 从 target Block 得到 exact BehaviorResolver；
2. capability 不存在或 runtime requirement 不满足时沿用既有 availability/claim 与诊断路径；
3. 调用 `consider_candidate()`；
4. target behavior 自己决定 no-op、继续探索或修改图。

admission 继续遵守 D-504 的五项谨慎条件。首版不增加 candidate completion state、queue table、硬性 fan-out policy 或
通用级联引擎。

### Automatic carrier：D-515 对 D-512 的扁平化修正

D-505 关闭了 receiver 与调用入口，但没有让 Relation 自动执行。D-512 已拒绝 candidate-only Job、同步 cascade 与
generic dispatcher；D-515 又撤回了其中的 combined Evolution Job。三种载体不能混为一谈：

| 方案 | 后果 | 当前判断 |
| --- | --- | --- |
| 写入 `candidate for` 后同步调用 target | attention fact 变成命令；递归跨模型调用需要 cascade/termination law | reject |
| Core generic candidate dispatcher 扫描所有 targets | Core 替 Extension 决定自动执行与 availability；重建统一 Organization runner | reject |
| 每个 exact behavior-owned Job 将指向自己 descriptor 的 edges 纳入自己的候选来源 | target 自己拥有候选规律、bounds/config/diagnostics；Relation 保持非命令式 | accepted by D-515 |

Core 的最小自动运行拓扑由 exact behaviors 直接推出七条独立 Organization Jobs：rumination、supersession、refinement、
evidence stance、synthesis、existing-referent anchoring 和 duplicate assertion。三种 evolution model 没有被证明共享候选、
availability、预算、失败或诊断边界，因此不为推测的扫描摊销建立 Evolution Job；真实重复只抽取普通 query function。
Rumination Job 不是只扫描 `candidate for` 的窄载体；它拥有完整的 recent/changed seeds、少量 random fallback 以及指向
自身 descriptor 的高优先级 candidate seeds，并复用显式 focal rumination 所调用的同一行为实现。

其它 behavior-owned Jobs 同样可把指向自身 descriptor 的 edges 作为额外的高优先级 seed，与各自正常的
model-specific seeds 一起处理。Extension 若希望其 behavior 自动消费 candidates，随 Resolver/descriptor 提供自己的 Job；
没有 Job 时 edge 可读但执行 unavailable。

不删除 edge、不写 completion state，也不要求 candidate producer 确认目标当前可运行。Agent runtime 只注册一个
`record_organization_candidate(information_id, behavior)` Tool；它动态解析 target BehaviorResolver class 并调用共享
`record_candidate()`，不会按 behavior 数量扩张 Tool。重复 reconsideration 由每次 Job bound 控制；已有 exact result/edge
让 behavior 快速 no-op。只有三处以上出现相同 incoming-edge selection mechanics 后，才抽取私有 query helper，不新增
Job dispatcher/base class。

## Relation 传导力与反应式图

```text
持久化 graph distinction
  -> target BehaviorResolver 可观察并消费
  -> exact semantic judgment
  -> Resolver-owned exact mutation method 增长图
  -> 新 graph distinction 促使其它 behavior 重新考虑
```

Relation 传导的是可观察的语义压力，不直接拥有命令权。`candidate for` 表示“值得目标 behavior 考虑”；`synthesis`
可以让 source change 传播成重新综合的输入。图因此参与执行和生长，但任意 Block content 不会被当作代码执行。

## Accepted material choice

首版选择 **exact behavior Block + actual BehaviorResolver methods**：

- 不把 Organization methods 加到信息 content Resolver；
- 不新增 Source-like pointer、第二套 capability registry 或 behavior table；
- concrete BehaviorResolver 同时实现实际 candidate orchestration 与 Agent-neutral exact graph mutation methods；
- 只为 graph-routed candidates 约定最小 `consider_candidate()` capability；
- 当出现独立持久化 behavior 实例/config/state 时，再升级为 Source-like projection/pointer。
