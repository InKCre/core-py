# Scoped Supersession Operation Contract

- **状态**：D-506 accepted exact-model Technical contract。
- **范围**：关闭 scoped supersession 的候选、证据、判断、命令、重放和 current/history 读取；不同时设计 refinement
  或 evidence stance，也不改变全局检索排序。

## 要产生的唯一区别

```text
successor --supersedes--> predecessor
```

这条 Relation 断言：两个端点具有足够的演进主题连续性、scope 覆盖和替代权威，并且 `successor` 所表达的信息在该完整
适用范围内取代 `predecessor`。两端 Block 都保留；“current”是 exact supersession graph 的读取结果，不是 Block
状态、record time 或全库真值。

这里的 `successor` 是模型判断出的语义后继，不是较晚写入数据库的 Block。今天收集到的一份历史政策仍可能是
predecessor；`created_at` 只能帮助选择近期 seed，不能授权 Relation 方向。

## 本模型中的几个词

- **referent（指称对象）**回答“这项信息在谈谁或什么”。它可以是一个人、服务、设备、政策、决定、配置、事件或
  其它可辨对象，不要求 info-base 中先存在一个 Entity Block。例如“两段话都在谈支付服务”只能证明 referent 可能
  相同。
- **演进主题**比 referent 更精确，回答“referent 的哪一个可演进状态/属性/决定正在被更新”。“支付服务的生产并发
  限额”和“支付服务的请求超时”有同一 referent，但不是同一演进主题。
- **scope（适用范围）**回答“这项信息对谁、在哪里、何时、在哪个版本/环境、什么条件和单位下成立”。它是从信息
  含义及上下文中得到的判断维度，不要求持久 `scope` 字段或统一结构。supersession 中的时间通常是前后接续而非
  相等：successor 接管变更点之后的默认适用职责，不会让 predecessor 在它原本的历史时段变成错误。
- **successor（后继项）**是这次判断认为应取得默认适用地位的信息端点；它不是“后写入数据库的记录”。
- **predecessor（被替代项）**是这条 Relation 直接声明被 successor 取代默认适用地位的信息端点。它继续作为历史
  保留，不表示被删除、错误或没有其它用途；也不承诺它是全图按时间排序后唯一的“上一版”。
- **替代权威**回答“successor 凭什么能让 predecessor 不再默认适用”。政策/决定可能来自同一或更高授权主体；运行
  状态可能来自负责该状态的系统；文档版本可能来自可验证的版本连续性。它不是全库统一 source rank。

## 可寻址性边界

`supersedes` 没有 scope payload。它只能在 dominance 覆盖 predecessor 这个完整信息单元时成立：

- 若一个 Block 只表达“欧洲区限额为 10”，而同 authority 的新信息表达“欧洲区限额改为 12”，可以建立 Relation；
- 若 predecessor 同时包含欧洲区和美国区规则，而 newer 只修改欧洲区，一条 Block-to-Block `supersedes` 会错误地
  淘汰未变化的美国区信息，因此必须 unresolved/no-op；
- 以后若另一项有独立理由的 breakdown/rumination 已把两条规则变成可独立寻址的信息，supersession 可以在准确
  端点上重新判断，但本模型不为了制造可写端点而隐式拆解来源。

这承认当前 representation 的适用边界，而不是把完整 scope token、claim selector 或 Relation payload 塞进 graph。
若本次 Agent 同时判断另一个 exact behavior 值得改善该粒度，它可以通过独立的跨模型 candidate contract 留下
attention signal；该候选及 behavior descriptor 的 Product/Technical 选择在
[cross-model assistance](cross-model-assistance.md) 单独评审，不扩张 `record_supersession()`。

## 候选形成

一次有界自动调用以新出现或发生可观察变化的信息为 seed：

1. `edited` 的两端形成最强 continuity candidate，但 `edited` 本身不证明 dominance；
2. Resolver text/label 提供词法和语义检索线索，寻找可能描述同一 referent/state 的信息；
3. 有界 exact-Relation neighborhood 补充来源、既有 referent anchor、版本连续性、authority 线索和相邻
   supersession/refinement/evidence；
4. 已存在的 exact `supersedes` 边用于跳过机械 replay，并让 Agent 看见当前 lineage；
5. purpose-built supersession Agent 可以在预算内继续检索、读取 Resolver 和走图。初始结果仍只是探索入口。

候选形成不假定 seed 是 successor，也不声称所有未选中的 pair 已被判断。每一次正向 Relation proposal 必须由 Agent
明确确定语义 successor 与 predecessor。

## 语义判断 SOP

对一个候选 pair，按顺序回答六个问题：

| 条件 | 为什么需要 | Agent 要确认什么 |
| --- | --- | --- |
| **可寻址信息** | Relation 连接整个 Block；只替代其中一段却淘汰整个 Block 会损失仍有效的信息 | 两端各自表达可比较的完整信息，且 successor 的 dominance 覆盖 predecessor 的全部 material meaning |
| **演进主题连续性** | 主题相似或同一实体不足以证明它们属于同一条状态/决定线 | referent 相同，并且被更新的是同一属性、决定、规则、状态或断言角色 |
| **scope 覆盖** | 同一主题可在地区、环境、时期、主体或条件上同时存在多个有效值 | 除语义接续产生的时间边界外，successor 接管 predecessor 原本作为 current 的完整适用职责，而不是只重叠或只更新一个分支；predecessor 的历史适用仍保留 |
| **语义后继顺序** | 收集时间不等于信息发生或生效时间；新导入的历史资料不能替代已知当前信息 | 明确更新/修订语言、有效期、版本、事件顺序或可信连续性足以确定谁是 successor |
| **替代权威** | 评论、预测、观测或低权威来源不能自动废止决定、政策或权威状态 | successor 的来源/角色相对于这项演进主题有权或有足够认识地改变默认适用项 |
| **完整 dominance** | 同主题、同 scope、同 authority 的信息仍可能只是补充、证据或重复 | 后续使用若继续把 predecessor 当默认项会产生错误；它现在只应作为历史保留 |

结果只有：

- `supersedes`：六项均有充分依据；
- `unresolved`：相关信息、scope、时间或 authority 不足以判断；
- `no-op`：证据足够说明没有完整 dominance，例如只是 refinement、support/challenge、不同 scope 或重复表达。

晚记录、文本矛盾、语义相似、同一个作者或 `edited` 单独出现都不充分。若判断属于 refinement 或 evidence stance，
本 invocation 不代替相应模型写 Relation；它只 no-op，并允许它们各自处理同一信息。

## 这些条件怎样被判断

首个实现可以把六项开放世界语义判断全部交给 purpose-built Agent；不需要六个 parser、score 或持久字段。各层责任
如下：

```text
deterministic / low-cost layer
  -> 只提供候选：recent/edited endpoints、lexical/semantic retrieval、exact graph neighborhood
Resolver + graph reads
  -> 提供两端完整含义、来源/说话者线索、已有 referent anchor、edited 和 supersession lineage
supersession Agent
  -> 在临时工作上下文中识别演进主题和 scope
  -> 按需继续检索、读取或走图以解决歧义
  -> 逐项应用六个条件
     |-> 信息不足：unresolved
     |-> 确认任一必要条件不成立：no-op
     `-> 全部成立：record_supersession(successor_id, predecessor_id)
exact command
  -> 只验证 endpoints / visible cycle / fetchsert；不假装重做语义判断
```

Agent 可使用的证据包括但不限于：

- Resolver 返回的完整文本、标签和 source-native metadata；
- `edited`、`refers to`、已有 `supersedes/refines/supports/challenges` 及其邻域；
- 明确的“取代、撤销、更正、自某日生效、旧版本停止适用”等表达；
- actor/speaker、发布渠道、文档或版本谱系、事件/生效时间与单位；
- 为消除同名 referent、scope 或 authority 歧义而主动检索到的其它信息。

这些都是 evidence，不是各自的充分规则。例如同一个 speaker 可能只是补充说明；`edited` 可能只修正错字；两个互斥
值也可能来自不同地区。Agent 必须对组合后的含义作判断。

不要求 Agent 输出或持久化 chain-of-thought。Tool input 只保留两个端点；Thread 中可以有简短诊断，但 graph
authority 只有成功写入的 exact Relation。语义质量由一组 Human-judged cases 验收：正例之外，至少逐项包含同名不同
referent、同 referent 不同属性、scope 部分重叠、authority 不足、record/event time 反转、refinement、challenge 和
多断言 Block 的近似反例。

## Agent 与 exact command

自动路径选择一个只带共享读取 Tools 和 exact `record_supersession` mutation Tool 的 definition。Agent 可以继续探索，
也可以直接产生一个或多个分别成立的 pairwise graph modifications；每次 Tool 调用仍只断言一个 pair。

Agent 提交的最小 proposal 是：

```python
SupersessionProposal(successor_id, predecessor_id)
```

不接收 `scope` 字符串：若 scope 只存在于一个不会持久化的参数中，Relation 对后续 use 不可解释；若需要把它塞进
Relation content，又破坏已接受的干净语义。模型应在调用命令前确认 dominance 覆盖完整 predecessor Block。

`record_supersession()` 在调用者拥有的事务中只做机械验证：

1. 两个不同的 Block 都存在；
2. 在当前事务可见图中，加入 `successor --supersedes--> predecessor` 不会形成已可检测的 directed cycle；
3. 使用 `RelationManager.fetchsert()` 创建或复用 canonical `supersedes` Relation；
4. 返回 Relation ID 以及本次是否实际创建。

现有通用 Relation/graph API 并不把 `supersedes` 保留给这个命令，数据库也没有语义无环约束；并发或其它写入仍可
形成异常 cycle。因此这项检查防止 exact command 主动制造已知错误，不承诺全局无环 authority。

命令不读取时间戳来重做语义判断，不更新 predecessor，不写 `current/stale/archived`，也不顺带创建 `edited`、
`refines`、`supports` 或 `challenges`。同一 pair 的重复运行由 fetchsert 收敛；无持久 evaluated/no-op state。

## 自动运行与可观察性

scoped supersession 拥有独立 Job、candidate law、BehaviorResolver 与 Tool。它可以复用普通查询函数取得的便宜证据，但
不与 refinement / evidence stance 共享 Evolution Job，也不因为另一个 evolution model 成功就推导本 Relation。

正常 unresolved/no-op 和 exact replay 都不制造 graph state，也不写成功 `Job.state`。持久效果由 graph 表达，JobStatus
表达生命周期，结构化日志/trace 记录本次 bound、候选、no-op/replay/mutation reason 和相关对象 ID。无效 proposal、
cycle、超时、model exhaustion 或未恢复 Tool error 沿用既有失败路径；不产生 BehaviorReport。

## Current/history 读取

普通 lexical/semantic retrieval 仍返回其检索到的信息；Core 不因一条 Organization Relation 全局隐藏 predecessor。
需要 current/history 区别的使用方，通过 supersession behavior-owned bounded projection 读取 focal Block 的 exact
`supersedes` lineage：

```text
SupersessionBehaviorResolver.read_lineage(focal_block_id, bounds)
  -> 从 focal Block 沿 incoming/outgoing exact `supersedes` 遍历
  -> 返回保留的 Blocks 与 Relations
  -> 对每个已返回 Block 检查全图是否存在 incoming `supersedes`
  -> 没有 incoming edge 的节点是 confirmed current frontier
  -> 若达到 bound，truncated=true；未返回的其它 branch/frontier 不作不存在声明
  -> 若发现 cycle，cycle_detected=true；不为该 cycle component 声称 current frontier
```

frontier 可以有多个节点，表示分支或并行适用的后继；BehaviorResolver 不按时间戳强选一个。遍历使用 visited set 终止；
异常 cycle 不会被伪装成 current/history。返回的是 immutable projection，不是 ORM rows；它不选择候选、不判断
scope，也不修改 graph。具体调用者仍需读取 Block 含义，选择与当前请求 scope 相符的 frontier。

## 示例与反例

```text
A：被授权的欧洲区政策规定并发限额为 10。
B：同一 authority 后来宣布欧洲区限额改为 12，并明确旧限额不再适用。

B --supersedes--> A
```

以后从 A 或 B 读取 lineage，都能得到 current frontier `{B}` 和 retained history `{A}`。

以下情况不能写这条边：

- C 是工程师预测“限额可能升到 12”：authority 不足；
- D 是美国区限额 12：scope 不同；
- E 解释为什么原限额是 10，但不改变它：可能是 refinement；
- F 提供测量结果表明实际限额不是 10：可能 challenges A，但不自动替代政策；
- G 是今天才导入的旧版政策：record time 更晚，语义上仍是 predecessor；
- H 同时包含欧洲区与美国区旧规则，B 只更新其中一项：端点粒度不足，不能用一条边淘汰整个 H。

## 明确不引入

- Block-level `current/stale/archived` 字段；
- 带 scope/authority JSON 的 Relation content；
- 全局 current-belief 或默认检索抑制；
- 时间戳比较器、confidence threshold 或通用 evolution classifier；
- 为了让本模型可写而自动拆分所有复杂 Block；
- exhaustive pair ledger 或已经评估过的持久状态。
