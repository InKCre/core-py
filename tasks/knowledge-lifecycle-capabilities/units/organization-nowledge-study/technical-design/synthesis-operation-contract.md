# Synthesis Operation Contract

- **状态**：D-503 accepted exact-model contract；后续实现计划仍与整组功能共同推进。
- **范围**：只关闭保留来源的多元综合这一精确模型的候选、证据、判断、提案、命令、重放和依赖响应合同；不为其
  新增通用 Organization 接口。

## 一次运行的合同

```text
新信息 / 新的相关图事实 / 定期有界扫描
  -> 以语义检索、词法检索或已接受的精确 Relation 取得候选来源集合
     -> purpose-built synthesis Agent definition 读取 Resolver 含义并按需继续探索
        -> 判断共同主题、scope、互补贡献、分歧、不确定性、说话者归属与复用价值
           |-> unresolved / no-op
           `-> SynthesisProposal(text, source_ids)
              -> create_synthesis(proposal, previous_synthesis_id?)
                 -> ordinary core.text.v1 Block
                 -> every source --synthesis--> derived Block
                 -> previous --edited--> synthesis when this is a changed reapplication
```

初始候选只引导探索，不限制 Agent 最终可读取的来源。候选集合、图连通性和相似度都不授权综合；精确判断仍要说明
每个成员的实质贡献，并在综合文本中保留分歧、不确定性和说话者归属。一个来源已经足够、集合只是重复、scope
不兼容、综合会抹平分歧或没有可复用区别时，结果是 no-op。

`source_ids` 是完整来源依据，不是 Agent 看过的所有 Block。检索到但未参与推导的上下文不能写
`synthesis`；否则后续依赖响应和来源审计都会扩大为假依赖。

## 端到端运行拓扑

一次自动运行不先枚举信息子集，也不让 Job 判断综合语义：

```text
Cron / caller 创建 exact synthesis Job
  -> JobManager 只检查本地 Handler；Handler 向 SynthesisBehaviorResolver 查询当前 availability
     |-> unavailable：不 claim，Job 保持 pending
     `-> claim Job
        -> SynthesisBehaviorResolver 构造有界候选区域
           |-> 新综合发现：recent seeds + small random fallback
           `-> 依赖响应：change endpoints <- synthesis -> affected synthesis
        -> Resolver 按已选实现对每个候选区域调用 purpose-built synthesis Agent
           -> Resolver-backed read / retrieval / bounded graph navigation
           -> Agent 自己缩小、重组或扩展最终来源集合
           -> unresolved / no-op：不调用 mutation Tool
           `-> proposal：调用 create_synthesis Tool
              -> exact command 在一个事务中校验并写 Block / Relations
        -> Handler 正常返回；JobManager 标记 finished
        `-> timeout / exhaustion / unrecovered error：JobManager 标记 failed / timed_out
```

“候选区域”刻意不是候选集合的穷举。确定性或低成本部分只围绕一个 seed/change 给出一片可探索信息；否则在把
`n` 项信息交给 Agent 前先枚举所有组合，会把 n-ary 的语义判断错误地变成组合搜索。逻辑上每个候选区域是一次
独立 model invocation；一个 Job 是否批量承载多个 invocation 只是调度细节，不改变 proposal、command 或 graph
contract。

Agent definition 只包含共享读取 Tools 和 exact synthesis mutation Tool。它可以主动继续检索和走图，也直接产出图
修改；Job、Agent runtime 和 AI Provider 都不拥有“什么是合格综合”的语义。

`create_synthesis` Tool 只返回本次 Agent 继续运行所需的 synthesis、basis Relation 与可选 `edited` Relation IDs，以及
各对象是创建还是复用。它不返回共享 `changed`，SynthesisBehaviorResolver 不把 Agent/Tool 历史汇总成报告，Job 也不
import Agent/Thread、不认识 Tool IDs、不解析 model-specific results。Agent 正常结束而未调用有效 mutation，或命令复用
同一文本与同一来源依据，Job 都正常 finished；差别留在结构化日志中。语义上的 `unresolved` 表示证据还不足，
`no-op` 表示证据足够但不该产生区别；两者不作为 Block、Relation、cursor、evaluation state 或成功 `Job.state`
持久化。未恢复的无效 mutation、超出 model-call budget、timeout 或异常进入既有 failed/timed-out lifecycle。

持久效果由 graph 表达，运行生命周期由 JobStatus 表达，bounded selection、unresolved/no-op、replay、mutation 与失败
原因由结构化日志/trace 表达。Handler/definition/Tool 不可用时沿用现有 availability/claim 合同；不增加新的终态，
也不把 LLM 自然语言结论提升为机器 authority。

## 新综合的候选与证据

新综合发现不要求 Human 指定主题。一次有界运行：

1. 从最近新增 Block 取得 focal seeds，并用少量随机 Block 补足长期覆盖；
2. 以 Resolver text/label 形成词法与语义检索线索；
3. 合并有界 exact-Relation neighborhood，优先保留能解释 provenance、scope、编辑连续性、证据立场和重复来源的
   邻接；
4. 把 cheap result 交给 Agent 作为起点，允许它继续检索、读取 Resolver 或走有界图路径；
5. 同时读取候选来源已经指向的 synthesis，避免把既有可复用区别换一种措辞再创建一次。

候选结果只限制一次运行的初始成本，不声明“这些就是全部相关信息”。Agent 最终选出的 `source_ids` 可以少于、
重组或在探索后超出 initial candidates，但必须落在本次实际读取并能说明贡献的有界证据内。

判断时对每个最终来源应用一个反事实贡献检查：去掉它后，综合是否会失去一项 material claim、constraint、
exception、speaker/source attribution、uncertainty，或综合明确声称的 independent corroboration？若不会，它不是
`source_ids` 成员。这个检查不是要求 LLM 输出 chain-of-thought；它是 SOP 和 Human-judged corpus 中可评审的结果规律。

`duplicates assertion` connected component 只代表一个 provenance occurrence；集合不能因收录它的多个副本而假装
获得多项独立贡献。等价但来源独立的信息仍可在综合明确表达 corroboration 时共同进入 basis。固定来源数量、
similarity score 或 graph degree 都不能替代这些判断。

一次合格的 proposal 因而必须同时满足：

- 文本本身是可独立使用的新信息，而不是来源标题拼接或“这些内容相关”的说明；
- 每个 source ID 对输出有 material contribution；
- 分歧、不确定性和说话者/来源归属没有被压平；
- 既有 synthesis 没有已经提供同一可复用区别；
- 根据已观察到的主题复现、图邻域和既有组织结果，有理由预测这个组合会被重复使用。

最后一项是 best-effort value forecast，不创建 use-history ledger，也不要求 Organization 知道未来 query。没有足够
理由时 no-op；以后出现新信息或新的使用压力时仍可重新考虑。

## 命令与机械重放

`create_synthesis()` 在调用者拥有的事务中：

1. 校验非空文本、至少两个不同且存在的来源，以及可选 previous synthesis 的存在性和来源依据；
2. 按同一 `core.text.v1` 文本查找现有 Block 候选；
3. 对每个候选读取全部入向 `synthesis` Relations；
4. 只有集合与 `source_ids` 精确相等时复用该 Block，否则创建新的普通 text Block；
5. `fetchsert` 每一条来源依据 Relation；若本次是 changed reapplication，`fetchsert`
   `previous --edited--> synthesis`。

`previous_synthesis_id` 是本次依赖响应的运行上下文，不是综合内容判断的一部分。综合命令不接收
`supersedes/refines` 参数，也不代替 evolution model 作判断。新 synthesis 与旧 synthesis 若另外具有 dominance 或
refinement 性质，由 evolution 的独立候选/判断/命令随后表达；常见共现不构成命令耦合的理由。

这不能复用 `BlockManager.fetchsert()`：当前默认 Block identity 是 `resolver + content`，会把相同文本、不同来源依据
的综合错误合并。这里的 `text + exact source basis` 只是 **synthesis 命令的机械重放键**，不是全库 Block identity、
模糊语义去重或新的持久 identity 字段。

LLM 用不同措辞表达同一综合，不可能由这个键机械消除。Agent 判断前必须读取候选集合已有的综合，并在没有新增
可复用区别时 no-op；残余语义重复属于判断质量，可由来源感知的重复断言模型显式表达。不要为此新增语义哈希、
综合 purpose ID、evaluation ledger 或 fuzzy fetchsert。

## 依赖响应

依赖响应只重新进入上述模型，不直接写 `stale` 或复制上游状态。新出现、且触及既有来源依据成员的已知精确
Organization Relation 可以作为过度召回的候选信号；Agent 再判断该变化是否实际改变综合。当前不建立通用 force
registry 或 cascade engine。

首个精确候选规律只需要两次普通图读取：

```text
新出现的可观察 Block / Relation change
  -> 找到 change 直接涉及的既有 Block
     -> 反向读取这些 Block 的 source --synthesis--> derived Block
        -> 每个命中的 synthesis 成为重新应用候选
```

`edited` 是最强的变化信号，因为它同时给出 old/new 版本连续性；新出现的 support/challenge、supersession/
refinement、duplicate 或其它 incident Relation 也可以过度召回候选，因为它可能改变来源的 scope、证据或解释。
它们都不直接授权 S2。Agent 读取 change、原 basis、`edited` 当前前沿和必要邻域后，仍只能 no-op/unresolved 或
调用同一个 `create_synthesis()`。

这个规律属于 synthesis model 的 candidate function，不推广成所有 Relation 的通用传播语义。它也不要求
`synthesis` 携带 force payload：方向和邻接只负责找到受影响对象，具体变化意义仍由 synthesis 判断。

调度可重复扫描最近的 Block/Relation 和既有 `synthesis` 邻接；正向图结果与上述机械重放规则抑制重复写入。
无持久 cursor、evaluated/no-op state 或全库穷举承诺。对 incident Relations 的宽召回只属于 synthesis candidate
heuristic，不能从这个案例推导出通用传播规则。

## 编辑传播与 best-effort 边界

本 unit 的普通信息编辑模型避免原地覆盖：

```text
A1 --edited--> A2
A1 --synthesis--> S1
```

`edited` 从旧 Block 指向保留的新版本；它只表达编辑连续性，不自动决定 A2 是否 supersedes/refines A1。上游变化
可通过来源依据把重新考虑压力传给综合：

```text
A1 --edited--> A2
A1 --synthesis--> S1
  -> synthesis Agent 重新读取当前相关子图
     -> no-op，或产生 S2
        A2 / B / C --synthesis--> S2
        S1 --edited--> S2
        later independent evolution may add: S2 --supersedes/refines--> S1
```

这里“Relation 是 force 的传路”不表示 `synthesis` 自己改写 S1。它只让受影响的 synthesis operation 成为候选；
同一综合模型重新判断内容、basis 和连续性。S1 与旧 basis 保留，S2 是新 Block。

系统无法总保证观察到变化。Storage pointer 背后的外部 bytes 可以在 Block 和 Relation 都不变时改变；这种情况下
没有 `edited` 信号，旧综合可能暂时或永久不能自动重新考虑。InKCre 对此只提供 best-effort Organization：在变化
通过新 Block、`edited` 或其它可观察图事实出现时收敛；不承诺对系统外静默变化的完整检测，也不为其新增快照、
全局版本身份、监视器或 evaluation ledger。

## 一个完整例子

已有四项普通信息：

- A1：被授权的决定是 10 月 1 日切换支付网关；
- B：切换前必须完成 7 天双写验证；
- C：Lin 负责双写验证；
- D：运维建议若 10 月 1 日不可行则改到 10 月 8 日，但该建议尚未成为决定。

定期 synthesis Job 先从最近的 A1 得到候选区域。词法/语义检索找到 B，图邻域找到 C，Agent 继续探索后读取 D；
这些读取只形成证据。Agent 的反事实贡献检查确认四者分别贡献当前日期、约束、责任人和带归属的备选意见，于是
提出：

```text
S1 = 当前计划是 10 月 1 日切换支付网关，切换前由 Lin 完成 7 天双写验证；
     运维另建议在该日期不可行时改到 10 月 8 日，该建议尚非决定。
```

命令创建一个普通 `core.text.v1` Block S1，并写入：

```text
A1 --synthesis--> S1
B  --synthesis--> S1
C  --synthesis--> S1
D  --synthesis--> S1
```

以后授权决定被编辑为 A2：“改为 10 月 8 日切换”：

```text
A1 --edited--> A2
A1 --synthesis--> S1
```

新的 `edited` 是强候选信号。依赖响应从 A1 反向找到 S1，把 A2、S1 的旧 basis 和相关邻域交给同一个 synthesis
model。Agent 重新判断后产生：

```text
S2 = 当前计划是 10 月 8 日切换支付网关，切换前由 Lin 完成 7 天双写验证。

A2 --synthesis--> S2
B  --synthesis--> S2
C  --synthesis--> S2
S1 --edited--> S2
```

D 没有被机械复制到新 basis：S2 不再表达“尚未决定的备选意见”，去掉 D 也不会损失 S2 的 material meaning。
S1 和它的旧 basis 保留。若另一个 evolution invocation 能证明 S2 在某个 scope 内 supersedes/refines S1，它可以另写
该 Relation；synthesis 本身不替它判断。

若 A2 只修正了不影响综合含义的错字，Agent 可以 no-op，S1 仍可沿 A1 的 `edited` 连续性追到 A2；系统不会仅因
“来源版本号变了”强制制造 S2。若 Agent 确实提出相同文本但采用不同 exact basis，机械重放键不同，命令会创建不同
的综合 Block，而不会错误合并来源历史。若外部 Storage bytes 静默变化且没有任何图事实变化，则这条链不会被可靠
触发；这是已承认的 best-effort 缺陷。
