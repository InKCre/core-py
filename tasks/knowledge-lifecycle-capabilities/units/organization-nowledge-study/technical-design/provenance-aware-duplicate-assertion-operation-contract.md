# Provenance-Aware Duplicate Assertion Operation Contract

- **状态**：D-511 accepted exact-model Technical contract；D-510 owns the count-once consumer correction。
- **范围**：关闭 provenance-aware duplicate assertion 的 candidate、判断、命令、重放与 count-once use；不设计物理
  compaction、canonical representative、全局内容去重、可信度评分或通用 equivalence framework。

## 要产生的唯一区别

```text
lower Block ID --duplicates assertion--> higher Block ID
```

`duplicates assertion` 表示两个完整、可寻址的 Block 复现同一次 provenance occurrence 中的同一项断言，因此对于依赖
证据独立性的 use，它们不是两份独立依据。方向只为稳定写入取较小 ID -> 较大 ID；语义本身对称，并且在所有边都正确时
具有传递性。

这个关系不表示两个 Block 在存储上相同、可以删除、所有邻接关系等价，或其中一个是 canonical copy。两个 Block 及其
各自来源/语境继续保留。

## 例子与 provenance occurrence

```text
R：runbook R1 中的一次发布段落：“公共 API 请求超时为 30 秒。”
A：从 R1 导入的原文片段：“公共 API 请求超时为 30 秒。”
B：另一导入渠道复制同一段落：“Public API requests time out after thirty seconds.”

A --duplicates assertion--> B
```

这里的 provenance occurrence 是产生这项断言作为依据的那一次可追溯事件，例如一次观测、测量、发言、决定或发布
段落；不是数据库行、URL 或传播副本的数量。B 即使经过改写，只要其依据仍完全来自 R 的同一次发布，就没有增加一份
独立证据。

### 更精确的定义：断言来源事件

`occurrence` 容易被误解为“文本又出现了一次”。本模型实际需要的是更窄的 **断言来源事件（assertion provenance
occurrence）**：相对于某一项具体断言，一次独立产生其信息依据、证据依据或权威依据的现实事件。

```text
现实中的一次来源事件
  -> 产生断言及其依据
     -> 可能经过复制、转发、翻译、格式转换或无新增依据的改写
        -> 形成多个 Block
```

前三类容易混淆的“次数”必须分开：

| 层次 | 例子 | 是否自然产生新的断言来源事件 |
| --- | --- | --- |
| 表征次数 | 同一封邮件由两个 collector 各形成一个 Block | 否；只是两份系统表征 |
| 传播次数 | 同一句话被转发、截图、翻译或转载 | 通常否；传播事件是新的，但被复述断言的依据仍来自上游 |
| 来源事件 | 独立测量一次、作出一次决定、给出一次证词、发表一次原始分析 | 是；它能为断言提供不依赖另一候选的来源基础 |

它是 **assertion-relative**，不是整个文档的固定标签。同一篇文章可以：

- 对引用自 R1 的 “timeout = 30s” 继续使用 R1 的来源事件；
- 同时包含作者自己运行测试得到的另一项独立来源事件；
- 再包含没有证据资格的背景说明。

因此整篇文章不能因为其中一处引用而与 R1 成为 duplicate；只有先独立可寻址的引用断言片段可能建立关系。

一个实用的反事实问题是：**如果那个上游观测/发言/决定/发布从未发生，A 与 B 是否会同时失去这项断言的来源基础？**
若会，并且没有任一方自己的独立形成过程，它们很可能属于同一断言来源事件；若任一方仍可凭自己的测量、推理或
权威决定成立，则是不同来源事件。这个问题是 Agent 的判断方法，不是机械授权规则。

### 它怎样被判断，而不是怎样被建模成实体

首版不持久化 `ProvenanceOccurrence` 实体或 occurrence ID。Agent 从现有信息恢复来源链：

1. Resolver 读取两个 Block 的完整含义、作者/频道/时间、source-native identifiers 和可用引用；
2. 图与检索寻找共同上游 Block、明确引用/转发关系、同一消息/发布标识、原始测量或决定；
3. LLM 区分“复制同一依据”与“独立地产生同一结论”，并检查是否存在新增观测、推理或权威；
4. 来源链足够清楚才写 `duplicates assertion`；只有内容相同而来源不可恢复时保持 unresolved。

共同 URL、相同作者、接近时间、相同文字乃至同一错误拼写都只是强弱不同的 evidence。它们可以帮助定位同一来源
事件，却不能单独成为 occurrence identity。首版持久 authority 仍只是经过判断的 duplicate Relation 及其可恢复邻域；
若未来多个模型都必须直接引用同一个现实来源事件，再考虑把该事件本身物化为普通 Block。

以下不是重复断言：

- 两个团队独立测量后都得到 30 秒；命题相同，但 provenance occurrence 不同；
- 一个 Block 说公共 API，另一个说批量导出 worker；数值相同但 referent 不同；
- 后来的正式决定把超时改为 60 秒；它应进入 evolution 判断；
- B 除复述 A 外还加入独立测量或 materially distinct assertion；整个 B 不能与 A 建边；
- 一篇文章引用 R1 并作独立分析；只有其中来自 R1 的可寻址断言片段可能重复，整篇文章不重复。

## Whole-Block 与 selected-text 边界

关系必须对两个完整 endpoint Block 的断言成立。若 A/B 只有其中一部分复制同一 occurrence，duplicate behavior 不对
原始复合 Block 建边；它可通过 D-504 的 `candidate for` 请求现有 rumination/另一个适当 behavior 先形成来源可恢复的
断言 Block，随后再判断这些新 Blocks。

这与 D-509 的 selected-text 模式同源：先让真正参与关系的部分可寻址，再建立 whole-Block Relation；但本模型不因此
新增一个通用 extraction command、`has assertion` 词汇或 span schema。只有出现第二个已经关闭的精确写入合同后，才
评审是否存在值得共享的提取 primitive。

## 判断条件

对每个候选 pair 依次确认：

| 条件 | 必要原因 | Agent 要确认什么 |
| --- | --- | --- |
| **完整可寻址** | 部分重叠不能授权 whole-Block 等价 | 两个 Block 各自完整承载待比较断言；附带的独立信息不会被关系吞掉 |
| **同一命题** | 相似主题、同值或互相支持不等于复现同一断言 | referent、predicate、polarity、modal force、单位和关键限定相同；措辞可不同 |
| **适用范围一致** | 同一命题模板在环境、版本或时间上可能是不同事实 | scope、时间适用性、版本/环境和说话者归属相容 |
| **同一 provenance occurrence** | 相同结论可能来自独立证据 | 可恢复的来源/传播链表明两者最终复现同一次观测、发言、决定、测量或发布片段 |
| **无独立证据增量** | “引用后独立验证”不能被压成一份来源 | 任一 endpoint 都没有为该断言增加独立形成的观察、推理或权威决定 |
| **无 material asymmetric gain** | 一边增加关键限定/信息时，整体不再等价 | 差异只是表达、格式或非实质上下文；否则路由 refinement、synthesis 或其它 owning model |
| **可复用非独立性** | Organization 不为表面重复或图形整齐建边 | 该关系预期能防止 evidence multiplication 或恢复被副本分散的 provenance/context 路径 |

结果只有：

- `duplicates assertion`：七项均有充分依据；
- `unresolved`：命题、scope、attribution 或 provenance chain 不能可靠恢复；
- `no-op`：已在同一 duplicate component、独立来源、仅相似/相关、存在 material difference，或没有可复用价值；
- `candidate for`：已证明 endpoint 粒度不足，或明显属于另一个 Organization behavior。

首版由 purpose-built Agent 进行这些开放世界判断。完全相同的 hash、共同 URL、相同 source-native ID、引用关系或高
embedding similarity 都只能分别构成 candidate/evidence；没有一个信号单独证明同一 assertion occurrence。

## Candidate、BehaviorResolver 与 exact command

```text
DuplicateAssertionBehaviorResolver.consider_candidate(seed)
  -> exact/source identity + lexical/semantic overlap + provenance neighborhood
  -> Agent explores source chains and competing explanations
     |-> unresolved / no-op
     |-> record_organization_candidate(...) for a proven prerequisite/sibling model
     `-> record_duplicate_assertion(left_id, right_id)
```

automatic run 从新/变化信息、来源身份冲突、语义近邻以及显式 `candidate for` 的有界 seeds 开始；不做全库两两比较，
也不把 similarity cluster 当成 compaction authority。Agent 可继续搜索最初候选集之外的原始来源与传播链。

`record_duplicate_assertion()` 在调用者事务中：

1. 验证两个不同 Block 已存在；
2. 将较小 Block ID 规范为 `from_`、较大 ID 规范为 `to_`；
3. fetchsert exact `duplicates assertion` Relation；
4. 返回 Relation ID 与本次是否创建。

命令不重新判断语义、不删除/改写 Block、不搬移其它 Relations、不选 representative、不写 transitive closure，也不检查
cycle。ID 方向天然不会形成 directed cycle；undirected component 中的冗余边没有状态含义。候选阶段通常跳过已在同一
component 的 pair，但 command 只保证 exact-edge sequential replay。

## Count-once consumer：为什么 induced subgraph 不够

该查询的完整返回形状、block/relation 双重 bound 与 use-law 边界见
[重复断言的连通分量读取与解释边界](duplicate-component-query.md)。

已接受的 Product use law 是：一个 duplicate-connected provenance occurrence 在证据 use 中只计一次。考虑：

```text
A --duplicates assertion--> B --duplicates assertion--> C

本次 evidence seeds = {A, C}
```

如果 Graph Navigation 只读取 `{A, C}` 的 induced subgraph，B 被排除，两者之间没有直接边，于是 Application 会错误地
计作两份证据。该失败不是 presentation 问题；它违反了关系被持久化的唯一 use promise。

D-510 因此把 D-500 的 induced-only query 改为：

```text
get_connected_components(
  seed_block_ids,
  contents=("duplicates assertion",),
  max_explored_blocks=...
)
```

Graph Navigation 从调用方 seeds 出发，只沿精确指定的 Relation contents 双向扩展，并返回：

- 输入 seeds 的 component partition；
- 为证明连通性而发现的 Blocks/Relations；
- 是否因 bound 截断。

外部发现的 duplicate Blocks 只证明 seeds 的连通性，不会自动加入调用方的 evidence set。任何 evidence-sensitive
consumer 都用完整 component 防止副本虚增 independent corroboration；synthesis 只是一个集成案例。若扩展被截断，结果不能声称
partition 完整，Application 也不能据此给出精确独立份数；它可以提高 bound 或把 multiplicity 报为 unresolved。普通
Graph Navigation 只计算拓扑，不理解 `duplicates assertion` 或“计一次”；Application 仍拥有当前请求中的计数与临时
representative 选择。

不新增 duplicate index、canonical component row、并查集持久状态或 representative pointer。只有实际规模证明有界
图扩展不足时，才重新评审索引/物化投影。

## Replay、变化与 use

- exact pair replay 由 canonical direction + fetchsert 收敛；unresolved/no-op 不持久化；
- `edited` 任一 endpoint、来源链变化或新 provenance Relation 都可以使 duplicate judgment 值得重新考虑，但 Relation
  自身不执行级联；
- append-only edit 不删除旧 duplicate edge；若新版本不再重复，它不继承旧边。旧边仍正确描述旧 Blocks；
- false positive 会错误折叠独立证据，损害大于漏边，因此 provenance ambiguity 保持 unresolved；
- later use 可沿 component 找回每个副本的来源/语境，但不得把一项邻接关系机械复制到所有 component members。

## D-511 关闭的选择

1. `duplicates assertion` 是对完整断言和同一 provenance occurrence 的非独立性关系，不是内容相似或 storage duplicate；
2. storage direction 只使用 lower ID -> higher ID；consumer 按无向连通性解释，不物化 canonical representative；
3. exact command 不承担部分断言 extraction；粒度不足时先形成可寻址 Block；
4. D-510 已确认：为兑现 count-once，`get_connected_components()` 必须从 input seeds 沿 exact Relation 有界补全外部
   连接路径，而不是只分割 input-induced subgraph；截断结果不声称精确独立份数。
