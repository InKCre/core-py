# Technical / Acceptance Coverage Reconciliation

- **状态**：Technical boundaries closed by D-523；best-effort black-box Acceptance closed by D-525。
- **目的**：六个 exact models 已关闭；现在逐项确认 Acceptance 是否已有 semantic contract、现有实现 owner 和最小实现
  缺口，避免继续按功能名称增加抽象或把 Implementation Plan 偷渡进 Technical design。

## 结论概览

当前没有第七个 Organization model，也没有证据要求新增 graph schema、Organization table、generic dispatcher、统一
planner、occurrence entity 或 Relation resolver。现有普通 Block/Relation、Resolver、retrieval/navigation、Agent definition、
Job/Cron 和 Extension bootstrap 足以作为基础。

当前已知 material Technical 边界均已关闭但尚未实现：BehaviorResolver-owned exact mutations、descriptor Blocks、七条
behavior-owned 自动运行路径、三个探索元工具、两个无状态读取投影、Relation token ownership，以及 D-523 的 per-behavior
Agent definition selection。下一步是做 whole-set Acceptance freeze audit；若对照暴露真实语义/owner 缺口再重开 Technical，
否则进入 Implementation Plan；D-525 后该对照未发现新的 material gap，当前已进入 Implementation Plan。

当前 [Acceptance strategy](../acceptance/index.md) 已撤回 mechanism-by-mechanism deterministic inventory。D-524 只保留
best-effort end-to-end black-box journey：从 ordinary inputs/config/Jobs 进入，读取 graph/use result、JobStatus 和必要
diagnostics。静态结构与针对性回归检查归 Implementation Plan/preflight/implementation verification，不作为替代产品效果的
Acceptance 层。

## Acceptance → Owner → Gap

| Acceptance responsibility | Accepted semantic owner | Existing mechanism to reuse | Remaining implementation / decision |
| --- | --- | --- | --- |
| supersession/refinement/evidence stance | three exact evolution contracts D-506–D-508 | ordinary Relation + Resolver/retrieval/graph reads | three Resolver-owned mutation/operation methods；supersession focal read；three exact Jobs |
| n-ary synthesis + dependency response | synthesis contract D-503 | ordinary text Block、Relation、Job、`edited` vocabulary | proposal/command、exact-basis replay query、affected-synthesis seed query；append-only source meaning remains blocking boundary |
| existing-referent anchoring | anchoring contract D-509 | ordinary text Block + exact Relations | occurrence-local fragment command/replay and behavior invocation |
| duplicate non-independence | duplicate contract D-511 + query correction D-510 | ordinary Relation + Graph Navigation frontier queries | canonical relation command；bounded component projection + stable count-once use law；no designated current consumer required |
| candidate formation/exploration | each exact SOP + initial-seed-not-cap law | lexical/semantic retrieval、public typed Resolver methods、Graph Navigation methods | three accepted owner-coherent meta-tools；Resolver/Graph discovery remains owner-local，with no `Information` wrapper or narrower `label + text` contract |
| exact graph mutation | model contracts | caller-owned DB transaction、Block/Relation create/fetchsert | six narrow model methods on concrete BehaviorResolvers；one candidate Tool dispatches to target Resolver；generic `submit_graph` unchanged |
| cross-model assistance | D-504/D-505 | ordinary behavior Block + `candidate for` + Resolver registry | one dynamically bound candidate Agent Tool、target Resolver lazy descriptor + `record_candidate()`、small capability Protocol；no startup sync or candidate state/queue |
| automatic operation | D-497 and per-model runtime laws | typed Job Handler、Cron、recent/random Block and Relation timestamps | seven independent exact behavior-owned Organization Jobs；`candidate for` is one high-priority seed source rather than a separate Job；typed bounds/config，operator-configured Cron |
| outcome observability | D-518 graph/lifecycle/diagnostic split | persisted graph、JobStatus、logging/trace IDs | structured behavior events only；no BehaviorReport、successful Job.state、shared `changed` or no-op ledger |
| later-use projections | D-500/D-506/D-510/D-520 | behavior-owned typed projection、Graph Navigation | `SupersessionBehaviorResolver.read_lineage()` and corrected `get_connected_components()` only；other models use ordinary graph reads |
| Extension-grown Organization | D-490/D-505 | enabled Extension startup precedes Job type sync；Extensions already register Resolver/Tool/Job | Extension may ship exact BehaviorResolver + descriptor + optional Tool/Job/config；no Core hook for specializing existing exact semantics without a concrete use |
| semantic/live Acceptance | exact contracts D-503/D-506–D-511 | current integration/live-test patterns and controllable Agent provider | deterministic graph/mechanics suite + one Human-judged credentialed corpus across positive/ambiguous/adversarial cases |

## Minimum implementation surface implied so far

This is responsibility topology，not yet the ordered Implementation Plan：

```text
exact model modules
  -> proposal/command + candidate/evidence assembly
  -> depend only on Resolver/retrieval/Graph/InfoBase

exact BehaviorResolvers
  -> graph-addressable behavior identity + consider_candidate()
  -> may call selected Agent/direct AI
  -> call exact model commands inward

Agent Tool bindings
  -> shared read Tools over existing Managers
  -> model-specific mutation Tools over exact Resolver commands

seven exact behavior-owned Organization Job Handlers
  -> availability check + exact BehaviorResolver bounded-operation call

exact BehaviorResolver automatic methods
  -> bounded seed selection + structured diagnostics + optional AgentManager call
  -> incoming `candidate for` edges are one additional high-priority seed source

two read additions
  -> SupersessionBehaviorResolver.read_lineage(focal_block_id, bounds)
  -> GraphNavigationRetrievalManager.get_connected_components()
```

No new database table is presently required。Behavior descriptors and selected fragments are ordinary Blocks；all model results
are ordinary Relations/Blocks；new Job types use the existing catalog projection。A migration becomes justified only if preflight
finds a missing enforceable database invariant，not merely because this feature set is large。

## Confirmed “do not build” list

- generic Organization runtime/base/registry or one Agent that selects the behavior；
- graph-change event bus、cascade coordinator、evaluation cursor/ledger or persisted no-op；
- Entity、Crystal、provenance-occurrence、component or canonical-representative table；
- common Relation JSON envelope、selector-bearing Relation content or Relation Resolver；
- new retrieval engine、OrganizationContext facade or acceptance-only graph index；
- Human approve/reject lifecycle、archive/compaction state or physical merge。

## Closed boundary A：`candidate for` 与扁平自动载体（D-512 / D-515）

D-504 允许 Agent 将信息谨慎标给任何 existing exact behavior descriptor；D-505 让 target Resolver 的
`consider_candidate()` 成为实际入口。但持久 Relation 不会自己执行：

- 当前 rumination 只有显式 focal call，没有自动 Job；
- 先前的 four-Job 计数只覆盖 evolution、synthesis、anchoring 和 duplicate，遗漏了 rumination 自身的自动运行责任；
- 立即调用 target 会把 attention fact 变成同步 cascade command，违反 D-504；
- 一个 generic candidate dispatcher 会重新引入 D-497 已拒绝的统一运行载体，并让 Extension behavior 在未声明 Job/
  availability 时被 Core 自动执行。

accepted design 是 **每个 exact behavior 拥有自己的完整 automatic Organization Job，并把指向自身 descriptor 的
`candidate for` edges 作为一种高优先级 seed**。D-515 撤回 D-512 中为推测的候选读取摊销而建立的 Evolution Job；Core
现在有七条独立自动路径：rumination、supersession、refinement、evidence stance、synthesis、existing-referent anchoring 和
duplicate assertion。真实重复的便宜读取只抽取普通 query function，不共享 Job lifecycle。Rumination Job 同时拥有正常的
recent/changed、少量 random fallback 和 incoming candidate seeds；它不是 candidate-only Job。显式 focal rumination与自动
Job 复用同一个 behavior implementation，但显式调用不是 Job 的候选规律。

Extension behavior 若需要 automatic consumption，就随自己的 Resolver/descriptor 提供 Job；否则 Relation 仍是可读
attention fact，运行时 honestly unavailable。Agent runtime 只注册一个
`record_organization_candidate(information_id, behavior)` Tool；其动态 schema 只接受已注册 exact behavior type，并调用
`record_candidate()`，不会按 behavior 或 Extension 数量复制 Tool。该方法不同步调用 target，也不创建完成状态。
多个 Job 重复出现同一种 incoming-edge query 后，才提取一个私有 helper；generic Job/behavior base 仍不需要。

## Material unresolved boundary B：append-only address meaning

Every accepted Relation assumes an endpoint ID continues to mean the information that was judged：

```text
S --synthesis--> D
A --supports--> X
N --supersedes--> P
```

If `S.content`、`A.content` or `P.content` is later changed in place，the historical Relation remains but its proposition/source
basis changes retroactively。For synthesis this is especially direct：the old derived Block no longer has its recorded source
basis，even though the graph shape did not change。

Current code exposes both generic in-place `BlockManager.edit_block()` / `PATCH /blocks/{id}` and direct Source/Extension writes
to `BlockModel.content/resolver/storage`。D-502 already rejects that as the preferred ordinary information-edit path and requires
`old --edited--> new`。The remaining design question is not whether Organization should notice edits；it is **which existing
mutations are information-version edits and therefore must append，versus producer-owned projection reconciliation whose stable
identity has a separately justified mutable contract**。

The caller inventory、authority derivation and ROI levels now live in
[append-only information edit boundary](append-only-information-edit-boundary.md)。D-513 keeps append-only as
an Organization-local output contract and ecosystem guidance，not global enforcement。Generic PATCH and existing producer paths
remain unchanged in this unit；no shared edit helper is added。A concrete historical-meaning/use failure may later justify opt-in
support or one producer's exact migration。Mutable upstream provenance remains an explicit best-effort residual。

## Closed boundary C：精确 Tool 与 behavior descriptor

[精确修改入口与 Behavior Descriptor 物化](exact-tools-and-behavior-descriptors.md) 已由 D-515 关闭 Job/ownership 部分，并由
D-516 关闭 exact Resolver type + empty content 的 descriptor identity。Sir 拒绝 post-registration global sync 后，D-517
改为复用 Resolver class registration 与 Agent Tool `input_model_factory`：唯一 candidate Tool 接收已注册 exact
behavior type，target Resolver class 在真实 candidate transaction 内惰性 fetchsert 自己的 descriptor；Job 需要自身 graph
receiver 时复用同一 mechanics。没有 import-time DB write、startup catalog sync 或 ExtensionHost dependency。七个 exact
behaviors 仍各自拥有自动 Job，六个 model mutations 仍由相应 concrete BehaviorResolver 实现。当前 observability
review 没有找到 BehaviorReport consumer，因此 D-518 决定不产生 report、不写成功 Job.state，也不建立 shared `changed`：exact
methods 只返回直接调用者需要的 model-specific IDs/created state；graph、existing JobStatus 与 structured logs/traces 分别
拥有持久效果、执行生命周期和过程诊断。

## Closed boundary D：Agent 初始候选之外的探索能力（D-521 / D-522）

[Agent 探索工具](agent-exploration-tools.md) 从已接受的 open-ended Agent law 和元工具原则反推三个 owner-coherent
Agent Tools：`retrieve`、`resolver` 与 `graph_retrieval`。此前的
`read_blocks -> label + text` 会压缩 Resolver 能力，现已撤回。Resolver owner 提供可发现、可调用的 public typed method
contract；Organization 和 MCP Sink 只能分别依赖该 owner。它不增加 `Information` wrapper 或 retrieval facade、不给
通用 Resolver 加 Organization 方法，也不把精确 mutation 合并进一个 generic write Tool。该边界关闭后，继续核对
behavior deployment config，冻结整组 Acceptance，再形成一个 whole-unit Implementation Plan、preflight 与 Impact
Handshake。`retrieve` 以 mode 组合 lexical/semantic/hybrid；`graph_retrieval` 通过 describe/invoke 到达全部 public typed
Graph Navigation methods。SQL/Cypher 不是能力禁令，但当前没有足以抵偿 storage-schema coupling 的 query need；
Organization 不依赖 MCP Sink 仍是必须保持的依赖边界。

## Closed boundary E：BehaviorResolver deployment configuration（D-523）

[BehaviorResolver 的 Agent definition 选择](behavior-deployment-configuration.md) 由 D-523 关闭：具体 Organization
operation 就是 BehaviorResolver method，不新增 ExecutionAdapter。Agent-backed method 读取自己的
`core.organization.<behavior>` config 并选择完整 Agent definition；Job/route 只做薄调用。Rumination 也从
`OrganizationManager` 迁移到 `RuminationBehaviorResolver`。Concrete Resolver 可依赖 Agent orchestration，但精确图
mutation/read methods 仍保持独立可调用。
