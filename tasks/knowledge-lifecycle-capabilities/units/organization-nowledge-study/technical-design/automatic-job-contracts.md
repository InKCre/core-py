# 七条自动 Organization Job 的运行合同

- **状态**：D-519 accepted Job/BehaviorResolver responsibility、minimal parameters、stateless selection、failure and
  diagnostic contracts。
- **目的**：关闭七条自动路径的参数、候选读取、调用、局部失败与结构化诊断合同，不建立通用 Organization runner、
  BehaviorReport、cursor 或候选生命周期。

## 从现有运行时得到的约束

当前 `JobHandler.handle()` 返回 `None`；`JobManager` 负责参数校验、可用性检查、原子 claim、timeout 和终态关闭。
`Cron` 只把一个已验证的 Job template 按时间物化为独立 occurrence。现有 media interpretation Job 把 behavior-specific
report 写进 `Job.state`，但 D-518 已确认该局部先例没有为新的 Organization behaviors 证明统一报告消费者。

因此，一条 Organization Job 的自然边界是：

```text
Cron / explicit Job creation
  -> exact Job Handler
     -> can_handle(): target BehaviorResolver 当前是否可自动运行
     -> handle(): await target BehaviorResolver.run_automatic(max_seeds)
        -> normal return: JobManager marks finished
        -> uncaught failure/timeout: JobManager marks failed/timed_out
```

Handler 不读取 Block/Relation、不选择候选、不决定模型、不取得 Agent definition、不读取 Thread，也不持久化成功状态。
这比“Job owns candidate law”更精确：**exact Job type owns the automatic invocation route；BehaviorResolver owns the
behavior and its candidate law**。

## 唯一共同运行参数

七条首版 Job 共用一个很小的不可变参数值对象：

```python
class AutomaticOrganizationJobParameters(BaseModel):
  max_seeds: int = Field(default=10, ge=3, le=100)
```

`max_seeds` 表示本次最多交给对应 behavior 的 focal starting points 数量。它不是候选 pair 数、检索结果数、Tool-call
数或 mutation 数；这些由 exact behavior 的 evidence assembly、Agent definition budget、读取 Tool bounds 和 Job timeout
分别限制。共同参数只表达 Job occurrence 的成本上限，不形成共享候选算法或 behavior base class。

Job parameters 不包含：

- Agent/AI model、prompt 或 Tool IDs：它们属于 target BehaviorResolver 的部署配置和 purpose-built Agent definition；
- descriptor Block ID：identity 来自注册的 exact Resolver type，Block 只在真实 graph use 时惰性物化；
- candidate IDs：自动路径从当前图选择，显式 focal 调用是另一条 invocation entry；
- cursor、last-evaluated time 或 no-op state：首版保持 stateless best-effort；
- schedule：由 Cron 拥有；
- timeout：已有 Job/Cron timeout 字段拥有。

七个 Job types 独立注册，即使参数模型相同也不合并 Handler：

```text
core.organization.rumination.automatic.v1
core.organization.supersession.automatic.v1
core.organization.refinement.automatic.v1
core.organization.evidence-stance.automatic.v1
core.organization.synthesis.automatic.v1
core.organization.existing-referent-anchoring.automatic.v1
core.organization.duplicate-assertion.automatic.v1
```

名称中的 `automatic` 区分 Job occurrence 与同名 Resolver/Peer capability，不表示另一种 Product behavior。

## BehaviorResolver 自动入口

每个 exact BehaviorResolver 自己实现：

```python
@classmethod
def can_run_automatic(cls) -> bool: ...

@classmethod
async def run_automatic(cls, max_seeds: int) -> None: ...
```

当前没有理由为这两个方法增加新的公共基类或第二套 registry。七个薄 Handler 直接引用自己的 concrete Resolver；
Extension-owned behavior 若需要自动运行，随自身 Resolver 注册自己的 exact Job Handler。

`can_run_automatic()` 只做廉价、本地、无副作用的 capability 检查，例如：

- exact behavior 配置存在且能被当前 runtime 解析；
- 选定的 Agent definition / direct AI capability 当前可执行；
- 必要的 Resolver/retrieval capability 已注册。

它不探测远程服务、不物化 descriptor、不扫描候选、不创建 Thread。若返回 false，现有 JobManager 不 claim；Job 保持
pending，配置或 capability 后来恢复时可再次处理。

`run_automatic()` 才拥有完整 behavior-specific 过程：惰性取得 descriptor（若需要 incoming `candidate for`）、从当前
图选有界 seeds、组装异构证据、调用最弱但充分的 judge、执行 exact mutation，并写结构化日志。

## Stateless seed selection law

所有 behavior 都从三类信号中选择，但三类的具体查询和强弱由各模型拥有：

1. 指向自身 descriptor 的 `candidate for`：跨模型明确注意信号；
2. 模型特有的强信号或近期变化：例如 `edited` endpoint、受影响 synthesis、可作 evidence 的新信息；
3. 少量随机 fallback：让旧信息在没有用户 focal request 和 durable cursor 时仍有被重新发现的概率。

自动路径把最小值设为 3，使三类 seed 在都存在时各有一个位置；某类为空时，其位置按本模型优先级回填。
`run_automatic(max_seeds)` 再按本模型优先级填满剩余位置；在长期存在的
`candidate for` 集合内使用随机 offset/sample，而不是永远读取同一批最新 edges。这样不删除 candidate、不记录
evaluated/no-op，也避免一个长期无结果的高优先级候选永久饿死近期与随机探索。重复 exact 结果由图查询和命令
fetchsert 快速收敛。

这仍然是 best-effort：随机覆盖不保证某个 Block 在有限时间内被处理，扫描也不声称完整分类。若未来出现可测量的
饥饿或成本失败，再为那个 exact behavior 引入窄 checkpoint；不能从理论完整性预先推出共享 cursor/ledger。

## 七种 behavior-specific seed laws

| BehaviorResolver | 强信号 / 近期信号 | 从 seed 形成的判断区域 | 明显 replay 抑制 |
| --- | --- | --- | --- |
| rumination | 最近新增/变化 Block、incoming `candidate for` | focal Block + direct relations；Agent 可继续检索/走图 | 无统一正边；已有相同图修改由普通 graph submit 收敛 |
| supersession | `edited` 两端、近期信息、incoming candidate | 同一可能演进对象的 bounded pair neighborhood | 已有 exact `supersedes` pair |
| refinement | `edited` 两端、近期信息、incoming candidate | 同一可能演进对象的 bounded pair neighborhood | 已有 exact `refines` pair |
| evidence stance | 新 observation/measurement/testimony/assertion、近期 incident Relation、incoming candidate | evidence/assertion role candidates + provenance/scope context | 同一 pair 已有 exact stance；相反 stance 仍进入重新判断而非覆盖 |
| synthesis | 最近信息；旧 basis endpoint 的 `edited` 或 incident Relation；incoming candidate | 新综合 discovery region，或受影响 synthesis + 旧 basis + current neighborhood | 同一 text + exact basis；无新增区别的既有 synthesis context |
| existing-referent anchoring | 新/变化且尚无足够 anchor 的 source、incoming candidate | source mention + retrieved existing identity-bearing alternatives | 同一 source + selected text + referent path |
| duplicate assertion | 新/变化 assertion-like information、incoming candidate | lexical/semantic near matches + provenance neighborhood | 已有 canonical `duplicates assertion` pair |

“近期变化”只根据当前可观察的 Block/Relation 时间与图事实过度召回；它不是完整 mutation event stream。Storage pointer
背后的静默 bytes 变化仍不在保证内。表中的类型词只描述候选启发式，不要求 Block 持久 primary type。

## 一次 seed 的边界

一个 seed 最多启动一次该 behavior 的 judge invocation。BehaviorResolver 可在 invocation 内给 Agent 一个 bounded
candidate region，Agent 也可使用有界读取 Tools 继续探索；initial candidates 仍是起点而不是视野上限。Agent 的多轮
模型调用由所选 definition 的现有 per-turn budget 限制，整个批次再由 Job timeout 限制。

Judge 只可产生三类结局：

- unresolved：现有证据不足；
- no-op：证据足够，但不应产生该模型区别；
- 调用一个或多个本 definition 已声明的 exact mutation Tools。

BehaviorResolver 不要求 Agent 输出汇总对象或 chain-of-thought。一个 invocation 的 Tool result 只回到该 Agent，帮助其
继续当前推理；Job 不接收这些值。

## 局部失败与 Job 失败

自动 Job 是有界 best-effort batch，不应因一个坏 Block 抛弃其它已选 seeds：

- 某个 seed 无法 resolve、上下文缺失、Agent 给出可恢复的无效 proposal 或单次模型调用失败：记录
  `organization.seed.considered` 的 reason/outcome，继续下一个 seed；
- 配置在 claim 后消失、共享 retrieval/DB capability 失败、事务完整性错误、取消或无法继续整个 batch 的异常：向外
  抛出，由 JobManager 关闭为 failed/timed_out；只在最有上下文的一层记录异常，避免重复日志；
- 如果所有 seeds 都 no-op/unresolved，Handler 仍正常返回，Job 为 finished；这不等于“证明全图没有可整理信息”。

具体哪些异常可恢复由 exact BehaviorResolver 定义；不增加一个跨行为错误枚举。

## 结构化诊断合同

日志/trace 是过程诊断面，不是新的 durable graph authority。JobStatus 已表达开始/结束，因此日志不再复制
`run.started/run.finished` lifecycle，也不产生一个伪装成日志的汇总 report。首版只需要两个稳定事件：

| Event | 必需字段 | 作用 |
| --- | --- | --- |
| `organization.seeds.selected` | `job_id`、`behavior`、`max_seeds`、各 source 的选择数量与 bounded IDs | 界定本次实际考虑范围 |
| `organization.seed.considered` | `job_id`、`behavior`、`seed_block_ids`、`seed_source`、`outcome`、`reason`、相关 Block/Relation IDs | 解释一次 bounded judgment/no-op/replay/mutation/recoverable failure |

`outcome` 只作为日志低基数值，例如 `unresolved`、`no_op`、`replayed`、`mutated`、`failed`；`reason` 使用
behavior-owned 稳定短码。日志不包含完整 Block content、prompt、模型响应或 chain-of-thought。未恢复异常由既有
JobManager 日志拥有，BehaviorResolver 不再次记录同一 stack trace。

用户检查效果时，以 `job_id`/trace 找到这些事件，再按相关 IDs 查询当前图。日志保留策略决定过程可追溯时长；图中
结果不依赖日志继续存在。

## 不建立的抽象

- no `OrganizationJobBase`、generic behavior dispatcher or Evolution Job；
- no Job -> Agent/Thread/Tool dependency；
- no BehaviorReport、shared `changed`、successful Job.state or per-seed database row；
- no common candidate SQL forced across behaviors；出现三次真实重复后才提取私有 query helper；
- no candidate deletion/completion/retry state；
- no universal availability/error taxonomy beyond existing Job lifecycle。

## Accepted material choice（D-519）

1. 修正 D-512/D-515 的简写：Job 只拥有 exact automatic route；BehaviorResolver 拥有候选与整理语义；
2. 七种 Job type 独立，但首版共用唯一 `max_seeds` invocation parameter；Agent selection 留在 behavior-owned deployment
   config，schedule/timeout 留在 Cron/Job；
3. stateless selection 在每种可用 seed category 保留位置，并在 persistent candidate bucket 内随机化，以不增加状态的
   方式缓解 starvation；
4. candidate-local failure 记录后继续，batch-level failure 才使 Job failed；
5. 两个过程诊断事件取代 BehaviorReport，且不重复 JobStatus 生命周期；graph 仍是效果 authority。

D-523 进一步明确这里的 “behavior-owned” 是直接代码放置：Handler 调用 concrete BehaviorResolver method；该 method 读取
`core.organization.<behavior>` 并按需调用 AgentManager，不新增 ExecutionAdapter。Rumination 同样迁移到
`RuminationBehaviorResolver`，不再由 `OrganizationManager` 作为特殊路径承载。
