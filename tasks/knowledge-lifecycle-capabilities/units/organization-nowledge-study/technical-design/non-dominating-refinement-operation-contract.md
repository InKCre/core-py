# Non-Dominating Refinement Operation Contract

- **状态**：D-507 accepted exact-model Technical contract。
- **范围**：关闭 non-dominating refinement 的 candidate、evidence、judgment、command、replay 与 use；不借它表达
  supersession、support/challenge、duplicate 或 synthesis provenance。

## 要产生的唯一区别

```text
refinement --refines--> predecessor
```

这条 Relation 表示：`refinement` 延续 `predecessor` 的同一演进主题与信息角色，在兼容 scope 内增加了可复用的
细节、约束、解释、条件或操作精度，但不取得替代它的默认适用地位。两个 Block 都继续作为可用信息；不存在
current/history frontier。

例如：

```text
A：客户端在请求超时后会重试。
B：客户端在请求超时后采用指数退避，最多重试三次。

B --refines--> A
```

B 使重试机制更具体，但以后继续把 A 当作较粗粒度概述并不会出错。

## 为什么它不是其它模型

- 若 B 表示“客户端不再重试”，A 不应继续默认适用，候选属于 supersession 或 challenge；
- 若 B 只是另一来源确认客户端会重试，它可能 support A，而不是 refinement；
- 若 B 复制 A 的同一 provenance occurrence，它可能是 `duplicates assertion`；
- 若 B 从多个材料形成独立结论，其来源依据由 `synthesis` 表达；`refines` 本身不声称 provenance derivation；
- 若 B 只与 A 主题相关但没有增加 A 的可复用精度，应 no-op，不为图形丰富而连接。

这些 Relation 可以在各自语义独立成立时并存，但 refinement behavior 不替其它模型代写。

## Whole-Block 与 scope 边界

Relation 必须对两个完整端点成立。若 A 同时描述重试与熔断，而 B 只细化重试，一条 `B --refines--> A` 会暗示 B
细化了整个复合信息，因此应 unresolved/no-op；已有 breakdown/rumination 将重试断言物化为独立 Block 后再判断。

scope 不要求完全相等。refinement 可以在明确包含于 predecessor 的较窄 scope 中增加细节，例如从“部署”细化到
“生产部署”，但必须满足：

- 窄化是 B 含义中可见的，不把局部细节伪装成全局规则；
- A 在未被 B 覆盖的其余 scope 中继续有效；
- B 没有悄悄改变单位、主体、环境、时间或信息角色。

scope 扩大、scope 交叉但互不包含或隐含冲突都不能由一个干净 `refines` 表达。

## 候选形成

`RefinementBehaviorResolver.consider_candidate(seed)` 形成有界 candidate pairs：

1. `edited` endpoints 提供强 continuity 候选，但不证明新版本只是 refinement；
2. lexical/semantic retrieval 寻找同一 referent 与演进主题的不同粒度表达；
3. exact graph neighborhood 提供来源、scope、referent anchor、已有 evolution/evidence/synthesis 线索；
4. 已存在的 exact `refines` edge 跳过机械 replay，并为 Agent 展示 lineage；
5. Agent 可以在预算内继续检索、Resolver 读取和走图。

seed 不预设谁是 refinement；较晚收集或更长的文本都不是方向依据。

## 语义判断 SOP

对每个 pair 依次确认：

| 条件 | 必要原因 | 要确认的事实 |
| --- | --- | --- |
| **完整可寻址性** | Relation 作用于整个 Block | 两端都是这次细化关系诚实覆盖的完整信息单元 |
| **演进主题连续性** | 同一 referent 仍可能谈不同属性 | 两端延续同一状态、规则、决定、程序或断言线 |
| **scope 兼容** | 不同环境/主体的细节可能只是并列事实 | refinement scope 与 predecessor 相同或明确包含于其中，且不存在隐藏冲突 |
| **信息角色兼容** | 评论、预测、观测不能悄悄变成政策或事实本身 | assertion、proposal、decision、procedure 等角色与 attribution/authority 能够延续 |
| **实质增益** | Organization 不为结构美建立边 | 后项确实增加会改善复用的细节、约束、解释、条件或精度，而非改写/重复 |
| **非支配性** | refinement 的定义要求 predecessor 仍可独立使用 | 继续把 predecessor 当作较粗概述不会造成错误；若会，则应由 supersession 判断 |

结果只有：

- `refines`：六项均有充分依据；
- `unresolved`：缺少 subject、scope、role 或 compatibility 证据；
- `no-op`：已知是 supersession、evidence stance、duplicate、synthesis-only、无实质增益或不相关。

首版把这些开放世界判断交给 purpose-built Agent；确定性层只形成 candidates、提供 evidence 和执行 graph mechanics。
不新增 scope parser、refinement score 或持久 classification。

## Agent、Resolver 与 exact command

```text
RefinementBehaviorResolver.consider_candidate(seed)
  -> bounded candidates + resolved context
  -> purpose-built Agent applies the six conditions
     |-> unresolved / no-op
     |-> record_organization_candidate(...) for an independently useful prerequisite
     `-> record_refinement(refinement_id, predecessor_id)
```

Agent definition 只组合共享读取 Tools、`record_refinement` 与已接受的谨慎 candidate-marking Tool；不取得 generic
`submit_graph`。Agent 提交的最小 proposal 是：

```python
RefinementProposal(refinement_id, predecessor_id)
```

`record_refinement()` 在调用者事务中只做机械验证：

1. 两个不同 Block 均存在；
2. 新增 `refinement --refines--> predecessor` 不会在当前事务可见 `refines` graph 中形成 directed cycle；
3. `RelationManager.fetchsert()` 创建或复用 exact edge；
4. 返回 Relation ID 和本次是否创建。

命令不接受 scope/role payload，不读取时间戳，不建立 transitive closure，不写 sibling-model Relations，也不重新执行
LLM 判断。Generic Relation writers 仍可能形成异常 cycle，因此这里只保证 exact command 不主动制造已知 cycle。

## Replay、自动运行与 use

exact pair replay 由 fetchsert 收敛；unresolved/no-op 不持久化。graph、JobStatus 与结构化日志分别表达持久效果、运行
生命周期和过程诊断；不增加 BehaviorReport、成功 `Job.state` 或 evaluation ledger。

每个 exact behavior 的自动路径可以从新/变化信息、自己的 incoming `candidate for` 和已有 lineage 附近取有界 seeds。
对无结果的 seed 允许以后重新考虑；一次运行的结构化诊断只声明本次 bound 与实际选择，不声称完整扫描。

`refines` 的 Product use 是可遍历的 additive lineage，不是 currentness：

- ordinary graph navigation/retrieval 可以从粗略信息发现更具体信息，也可以从 refinement 回到 predecessor；
- 不新增 `read_current_refinement()` 或默认检索抑制；
- 不自动持久化 transitive edges；需要多层 refinement 时有界遍历实际路径；
- graph 出现异常 cycle 时遍历用 visited set 终止并诚实返回观测拓扑，不发明 hierarchy。

## Accepted material choice

批准上述六项 refinement law，尤其是两个容易混淆的边界：

1. scope 可以明确窄化，但不能交叉、扩大或隐藏冲突；predecessor 在剩余 scope 中继续有效；
2. `refines` 只表达非支配的语义细化，不同时声称来源依据、证据支持或 currentness。
