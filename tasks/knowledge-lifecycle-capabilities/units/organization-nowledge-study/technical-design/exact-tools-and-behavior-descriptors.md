# 精确修改入口与 Behavior Descriptor 物化

- **状态**：D-515–D-518 close flat Jobs、Resolver-owned mutation、descriptor identity、registration-aligned lazy
  materialization and the no-BehaviorReport observability boundary。
- **问题**：D-512 的五条自动 Job、已经关闭的精确模型、图内 `candidate for` target 和 Agent Tool 到底如何对应；如何在不新增
  behavior table、第二套 registry 或静态 migration authority 的前提下，让 target Block 稳定存在并可执行。

## 先分开三种数量

这三种东西的数量没有一一对应关系：

| 层次 | 数量 | 边界 |
| --- | ---: | --- |
| 自动 Job | 7 | 每个 exact behavior 一条：rumination、supersession、refinement、evidence stance、synthesis、existing-referent anchoring、duplicate assertion |
| 精确 behavior descriptor | 7 | 图内可寻址的语义执行目标：rumination、supersession、refinement、evidence stance、synthesis、existing-referent anchoring、duplicate assertion |
| 精确修改入口 | 7 | 六个已关闭模型的写入命令，加一个跨模型 `candidate for` 命令 |

对应关系是：

```text
Rumination Job --------------------------> rumination descriptor
Supersession Job ------------------------> supersession descriptor
Refinement Job --------------------------> refinement descriptor
Evidence-stance Job ---------------------> evidence-stance descriptor
Synthesis Job ---------------------------> synthesis descriptor
Existing-referent anchoring Job ---------> existing-referent-anchoring descriptor
Duplicate-assertion Job -----------------> duplicate-assertion descriptor
```

此前的 Evolution Job 试图只合并候选读取和运行调度成本，不合并三个语义问题；但当前没有证据表明三者真正共享同一
候选规律：supersession 寻找完整取代，refinement 寻找兼容增量，evidence stance 寻找证据与断言角色。为了尚未测量的
扫描节省先绑定三种参数、availability、失败和诊断边界，收益是推测的，耦合却是立即的。

因此当前推荐更扁平的七 Job 结构。三条 Job 可以各自从同一批 recent/random/change facts 开始；若实现中确实出现
重复的低成本读取，抽取一个普通私有 query function 即可，不必共享 Job lifecycle。同一 candidate pair 仍可被三种
模型分别考虑并得到多个互不冲突的 distinctions；exact command replay 会抑制重复结果。

图中同样不物化泛化的 `evolution` descriptor，否则 `candidate for` 会丢失“究竟值得哪一种精确判断”的信息，并重新
引入“让一个 Agent 选择 Organization model”的已拒绝形状。

同理，不物化 contextual linking、dependency response、append-only 或 normative-authority descriptor：它们分别是
model family、synthesis 的重新应用规律和跨模型 invariant，不是当前可单独调用的精确 behavior。

## 七个稳定 behavior identities

Core 首版提供七个 exact Resolver types；名称在实现前仍可按仓库惯例微调，但语义边界不再合并：

```text
core.organization.behavior.rumination.v1
core.organization.behavior.supersession.v1
core.organization.behavior.refinement.v1
core.organization.behavior.evidence-stance.v1
core.organization.behavior.synthesis.v1
core.organization.behavior.existing-referent-anchoring.v1
core.organization.behavior.duplicate-assertion.v1
```

现有 `core.organization.rumination.v1` 是 Peer execution capability ID，不复用为 Resolver type；二者属于不同接口层。
behavior identity 由版本化 Resolver type 承担。Block content 不复制 prompt、model、Tool、Job 参数或可变的人类描述，
否则这些运行配置变化会制造新的行为身份。D-516 接受空字符串作为 canonical instance-free content；`get_text()` / `get_label()`
由 exact Resolver 投影代码拥有的稳定说明。

这不是“空信息”：该 Block 表征的是一个已安装、可寻址的操作能力，其含义像其它异质 Block 一样由 Resolver type +
Resolver projection 给出。它也不是 Source-like pointer，因为没有另一个持久 behavior instance 可供它指向。

## 按真实使用惰性物化，而不是 startup sync

Resolver subclass 已通过 `Resolver.__init_subclass__()` 在类定义时注册；这个过程纯内存，也可能发生在数据库 bootstrap
之前。把 Block 写入塞进 class registration 会制造 import-time I/O，而在所有 Resolver 注册后额外调用
`sync_behavior_descriptors()` 又为 behavior 发明了其它 Resolver 不需要的全局 catalog synchronization。D-516 明确没有
接受这两个形状。

D-517 直接复用现有 Agent Tool dynamic input-model pattern：

```text
BehaviorResolver subclass 自注册
  -> single candidate Tool definition 绑定时读取已注册 exact behavior Resolver snapshot
     -> Tool schema 将 behavior 限制为这些 versioned Resolver types
        -> Agent 选择 behavior type
           -> target BehaviorResolver.record_candidate()
              -> 同一事务 fetchsert canonical descriptor Block
              -> fetchsert information --candidate for--> descriptor
```

单一 Tool input 因而改为：

```python
record_organization_candidate(information_id, behavior)
# behavior: one currently registered exact BehaviorResolver type
```

这里 Agent 选择的是已注册的 code-owned behavior identity，不是任意字符串，也不是数据库 Block ID。Tool binding 使用
与当前 `draft_graph` 相同的 `input_model_factory` 思路，把快照写进 schema enum/`oneOf`，并附上各 BehaviorResolver
code-owned description，让 Agent 能理解 Extension target 而不增加另一个 mutation Tool；执行时再次解析 exact class。该 class
的共享 classmethod 在一个事务中先通过 `BlockManager.fetchsert(BlockForm(resolver=cls.__rsotype__, content=""))` 取得
canonical descriptor，再写 candidate Relation。成功后，图内 authority 仍是
`information --candidate for--> persisted descriptor Block`；Resolver type 没有取代 Relation endpoint。

这不是允许 Tool 任意创造 behavior。只有已经通过 Resolver 注册机制进入当前 runtime 的 exact BehaviorResolver 才能
物化自己的 descriptor；Extension 注册新 Resolver 后会自然出现在此 Tool 下一次绑定的 schema 中，不调用 Core sync、
不增加 Tool，也不要求 ExtensionHost 依赖 Organization。

每条 behavior Job 在需要读取指向自身的 incoming candidate edges 时，调用同一个 class-owned
`get_or_create_descriptor()` mechanics；没有候选写入、Job 运行或其它真实 graph use 时，descriptor 不必提前存在。显式
behavior invocation 若不需要图内 receiver，也不为了目录完整而物化它。

物化只承诺顺序幂等。当前 Block 表没有 `(resolver, content)` 唯一约束；本 unit 不为了理论上的多 Peer 同时首次启动而
增加数据库约束。preflight 应实际测量该风险；若出现真实重复，再为这个精确 identity 增加窄约束或协调机制。

## 修改入口属于 BehaviorResolver

```python
record_supersession(successor_id, predecessor_id)
record_refinement(refinement_id, predecessor_id)
record_evidence_stance(evidence_id, assertion_id, stance)
create_synthesis(text, source_ids, previous_synthesis_id=None)
anchor_existing_referent(source_id, selected_text, referent_id)
record_duplicate_assertion(left_id, right_id)
record_organization_candidate(information_id, behavior)
```

前六个 exact model command 实现为对应 concrete BehaviorResolver 的方法：

```text
SupersessionBehaviorResolver.record(...)
RefinementBehaviorResolver.record(...)
EvidenceStanceBehaviorResolver.record(...)
SynthesisBehaviorResolver.create(...)
ExistingReferentAnchoringBehaviorResolver.anchor(...)
DuplicateAssertionBehaviorResolver.record(...)
```

它们不需要另建一层 Organization Manager/command classes。各 Agent Tool handler 只是参数验证与结果序列化适配，直接
调用相应 Resolver method。方法本身只依赖 Resolver/InfoBase/transaction mechanics；调用它不要求 Agent、AI Provider、
Job 或 Thread 正在运行。

第七个 `record_organization_candidate` 不是第七种模型写入，而是跨模型的 attention signal。Agent runtime **只注册
这一份 candidate mutation Tool**；它不会按 Core behaviors 枚举七份 Tool，也不会为 Extension behaviors 动态注册新
Tool。该单一 adapter 从动态 schema 接收 `behavior` Resolver type，通过 ResolverManager 取得目标
BehaviorResolver class，然后调用其共有的 classmethod：

```python
target_behavior_class.record_candidate(information_id)
```

该方法在自己的事务中按需 fetchsert descriptor，并写
`information --candidate for--> descriptor.block_id`。这样 Relation 的真实 receiver 仍是 target descriptor，Extension
behavior 可以自然成为 target。共享方法只负责验证 information endpoint 和精确 Relation identity；它不选择 behavior、
不调度 Job，也不实现任何模型语义。

Rumination 保留其开放式 graph authoring 能力，不虚构 `ruminate` mutation method：它是行为入口，可通过现有 Resolver
drafting + atomic `submit_graph` 产生普通图修改。因此“七个 Jobs”“七个 descriptors”“七个 mutation Tool entries”的
数字相同只是巧合，三者不能做一一映射。

每个 Tool input 使用 `extra=forbid`、frozen 的 Pydantic schema，只接收上述精确参数；Agent 不提交 Relation content、
任意 GraphForm、任意 behavior 字符串或 Block ID。`record_organization_candidate` 的 target type 必须来自当前绑定的
exact BehaviorResolver enum，执行时再次验证 capability。

## 结果可观察性：图、JobStatus 与日志已经足够

前一版为了把运行分类成 completed-with/without-effects，要求每个 Tool result 共享 `changed: bool`，再让
BehaviorResolver 产生 BehaviorReport、Job 保存到 `Job.state`。当前没有该 report 的程序化 consumer；这条链只是在
复制已经存在的三项 authority：

```text
图                 -> 到底产生了哪些持久 Organization effects
JobStatus          -> 这次执行 pending / running / finished / failed / timed_out
结构化日志 / trace -> 选择了什么、为什么 no-op、创建/复用了什么、哪里失败
```

因此 D-518 删除 BehaviorReport、Job effect report 和跨 Tools 的 `changed` 约定。七条 Organization Job Handlers 遵守
现有最小合同：检查 BehaviorResolver availability，调用一次 bounded behavior operation，正常返回即由 JobManager 标记
finished，异常由既有 Job lifecycle 标记 failed/timed_out。Handler 不写 `Job.state`；现有 JobManager 在失败时保存 error 的
行为不改变。

调用链退化为：

```text
JobHandler
  -> BehaviorResolver.run_bounded(...)
     -> no return value required
     -> exact graph effects + structured logs
```

Job 与 Agent Thread 没有直接或间接的数据合同：不读取 Thread、不认识 Tool IDs、不接收 Thread-derived report。Agent、
direct AI 或 deterministic implementation 都是 BehaviorResolver 内部选择；它们只通过持久图效果、异常和日志离开该边界。

精确 mutation method 仍应返回其调用者真正需要的 model-specific result，例如 relation ID 与 created/reused、synthesis
Block ID 与 basis Relation IDs、fragment ID 与两条 anchoring Relation IDs。薄 Agent Tool 原样序列化它，方便 Agent 确认
调用结果并继续本次推理；但这些结果不汇总为 common result，也不进入 Job。重复运行是否产生新效果，由每个方法的
`created`/具体 ID 语义表达，不再统一成 `changed`。

每个 behavior 在 candidate selection、no-op、unresolved、mutation、replay 和 recoverable candidate error 处写结构化日志，
并继承 Job trace context。日志记录 behavior/operation、相关 Block/Relation IDs、outcome/reason code 和 bounds，不记录完整
信息内容或 chain-of-thought。用户查看一次 Organization 行为的效果时，以 trace/log 定位过程、以 graph 复核持久结果；
不需要第二份可过期的 report。

`RelationManager.fetchsert()` 现有返回值没有 created flag。BehaviorResolver modules 可以共用一个私有小函数，比较
proposed object 与返回 object 并产生 `(relation, created)`；不修改通用 RelationManager 的公共返回
合同。Synthesis 和 anchoring 仍保留各自的 replay query，因为它们的 identity 分别是 text + exact source basis 与
source + selected text + referent path，不能退化成全局 Block content fetchsert。

## 依赖方向

```text
Job / explicit route / Agent Tool adapter
  -> exact BehaviorResolver entry
     -> exact candidate/evidence/judgment orchestration
     -> Resolver-owned exact mutation method
        -> BlockManager / RelationManager / retrieval / Resolver

ResolverManager
  -X-> Organization / Agent / Job
exact Resolver mutation method
  -X-> Agent / Tool / Thread
```

动态 Tool binding / behavior invocation layer 可以读取 Resolver registry，但不把 Organization capability 加进 Resolver base。最小 capability 的 Protocol/检查
由 Organization owner 持有；普通 content Resolver 不因此获得 `ruminate/supersede/synthesis` 方法。

## Accepted and active choices

1. D-515 以七条 exact behavior Jobs 取代 D-512 的五 Job 结构，不创建 Evolution Job 或 generic evolution descriptor；
2. D-516 规定 behavior Block 的稳定身份只由 exact versioned Resolver type 承担，content 为 canonical empty value；
3. D-517 不做 import-time DB write 或 post-registration global sync；单一 candidate Tool 以动态 enum 接收已注册
   behavior type，由 target class 在 candidate transaction 内惰性物化 descriptor；behavior Job 需要图内 receiver 时复用
   同一 class-owned mechanics；
4. D-515 将六个 exact model mutations 放在相应 concrete BehaviorResolver；跨模型 candidate 写入由 target
   BehaviorResolver 的共享 `record_candidate()` 接收；Agent 侧始终只有一个动态分派的 candidate Tool；
5. D-518：不产生 BehaviorReport、不写成功 Job.state、不建立共享 `changed`/effect result；exact methods 只返回
   model-specific IDs/created state，graph + existing JobStatus + structured logs 构成完整观测面。
