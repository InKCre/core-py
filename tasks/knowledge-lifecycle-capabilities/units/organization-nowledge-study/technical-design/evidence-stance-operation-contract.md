# Evidence Stance Operation Contract

- **状态**：D-508 accepted exact-model Technical contract。
- **范围**：关闭 `supports` / `challenges` 的 candidate、evidence、judgment、command、replay 与 use；不产生 truth score、
  currentness、supersession 或 consensus。

## 要产生的区别

```text
evidence --supports--> assertion
evidence --challenges--> assertion
```

这两条 Relation 表示一项有 provenance 的信息对一个完整、scope 明确的 assertion 具有正向或负向的证据意义。它们
不表示系统宣布 assertion 为真/假，也不删除、降级或替代任一端点。

同一个 Block 可以在一条 Relation 中是 assertion，在另一条中是 evidence；这是信息所具有的关系性质，不是 Block
的 primary type。

## 不是“文本同意/矛盾”

```text
A：生产环境 API 的 p95 延迟低于 200ms。
E1：同一版本生产压测记录的 p95 为 180ms。
E2：同一版本生产压测记录的 p95 为 350ms。

E1 --supports--> A
E2 --challenges--> A
```

E1/E2 的价值来自测量与 A 的指标、环境、版本和单位对齐，而不是数字或文字看起来相似。以下情况不能机械写边：

- staging 的 180ms 与 production assertion：scope 不可直接比较；
- “我也觉得延迟很低”：可能没有可辨 evidence basis；
- 另一篇复制同一压测报告的文章：可能是同一 provenance occurrence，不能当作新增独立证据；
- “下一版应把目标改成 150ms”：这是 proposal/decision，不是当前测量；
- 新政策明确撤销旧政策：属于 supersession，不是 challenge 的替代写法。

## Whole-Block 与 stance 边界

Relation 对完整 endpoints 成立。若 target Block 同时断言“延迟低于 200ms 且错误率低于 1%”，而 evidence 只测量
延迟，则不能对整个 target 写 `supports`；应先由已有 Organization behavior 形成可独立寻址的 assertion。

同一完整 evidence/assertion pair 在这个 exact model 中必须形成一个可确定 stance。若一项研究在不同子人群中既有
正向又有负向结果，或者证据只削弱 assertion 的一部分，它应 unresolved 或先物化 scope-specific findings，而不是
对同一 pair 同时写 `supports` 和 `challenges`。不同 evidence Blocks 分别支持和挑战同一 assertion 则完全合法，且
disagreement 必须保留。

## 候选形成

`EvidenceStanceBehaviorResolver.consider_candidate(seed)` 从以下位置形成有界 pairs：

1. 新出现/变化的测量、观察、研究结果、引文、testimony、argument 或 assertion；
2. lexical/semantic retrieval 找到的同 referent、命题角色与 scope 邻域；
3. `refers to`、source/provenance、`edited`、`duplicates assertion`、已有 evidence/evolution/synthesis Relations；
4. Agent 在预算内继续进行 Resolver 读取、检索与走图。

seed 不预设 evidence/assertion 角色；Agent 必须确定方向。文本相似度只用于减少搜索空间，不形成 stance。

## 语义判断 SOP

对一个候选 pair 依次确认：

| 条件 | 必要原因 | 要确认的事实 |
| --- | --- | --- |
| **完整可寻址性** | Relation 不能只支持/挑战 Block 内的一句话 | evidence 与 assertion 都是当前 stance 完整覆盖的信息单元 |
| **角色不对称性** | 两个观点相似不自动构成证据 | source 端确实是 observation、measurement、testimony、argument 或其它有 basis 的信息；target 是可评价 assertion |
| **命题对齐** | 同一 referent 可有许多无关断言 | evidence 实际涉及 assertion 所声称的属性、事件、因果或规则 |
| **scope 可比性** | 不同版本、环境、时间、主体或单位可能同时成立 | scope 相同，或差异本身能诚实地作用于 target 的完整 assertion |
| **推理相关性** | 同现、引用或重复不等于理由 | 若 evidence 内容及其来源成立，它会真实增加或减少对 assertion 的理由，而不是只提供主题邻近 |
| **provenance / attribution 可恢复** | later use 必须知道是谁、凭什么支持/挑战 | source、speaker、测量或形成路径能从 endpoints/graph 读取；Relation 不把其立场冒充系统立场 |
| **stance 可确定** | 简单 Relation 不能诚实表达混合结果 | 整个 evidence 对整个 assertion 明确是正向或负向；混合、部分或不足时 abstain |

结果只有：

- `supports`：七项成立且 evidence 提供正向理由；
- `challenges`：七项成立且 evidence 提供负向理由；
- `unresolved`：角色、scope、provenance、推理链或方向不足；
- `no-op`：已知只是 duplicate-only、related、refinement、supersession、synthesis basis 或无证据意义。

首版由 purpose-built Agent 作开放世界判断；确定性层不建立 source rank、credibility score、NLI threshold 或 truth
classifier。Relation 本身也不声称 evidence 独立；若多个 Blocks 来自同一 provenance occurrence，duplicate model 与
下游 consumer 负责不重复计数。

## BehaviorResolver 与 exact command

```text
EvidenceStanceBehaviorResolver.consider_candidate(seed)
  -> bounded pair candidates + resolved provenance/scope context
  -> Agent applies the seven conditions
     |-> unresolved / no-op
     |-> record_organization_candidate(...) for missing addressability/context
     `-> record_evidence_stance(evidence_id, assertion_id, stance)
```

Tool proposal：

```python
EvidenceStanceProposal(
  evidence_id,
  assertion_id,
  stance: Literal["supports", "challenges"],
)
```

`record_evidence_stance()` 在调用者事务中：

1. 验证两个不同 Block 存在；
2. 验证 stance 只有 `supports` / `challenges`；
3. 若同一 pair 已有相反 stance，拒绝制造这个 exact-model 内的自相矛盾，并让调用者重新检查 granularity/scope；
4. `RelationManager.fetchsert()` 创建或复用 exact edge；
5. 返回 Relation ID 与本次是否创建。

这里不做 graph cycle check。证据图可能形成多层 argument/evidence 网络；机械 DAG 约束既不能证明非循环论证，也会
误伤合法引用结构。Agent 负责避免把 assertion 自身的改写当作它的 evidence，later use 则读取真实 provenance 与路径。

## Replay、变化传播与 use

exact pair + stance replay 由 fetchsert 收敛；unresolved/no-op 不持久化。graph、JobStatus 与结构化日志分别表达持久效果、
运行生命周期和过程诊断；不增加 BehaviorReport 或成功 `Job.state`。

新 `supports` / `challenges` edge 不自动修改 assertion、产生 confidence、选 winner 或触发 supersession。它作为可观察
graph change，可以被 synthesis 等具有明确 reapplication law 的 exact consumer 当作“值得重新考虑”的输入；具体结果
仍由那个 consumer 判断。

later use 通过普通 graph traversal/retrieval 取得：

- 所有 supporting/challenging evidence 与 direction；
- 每项 evidence 的 source、speaker、scope 和相邻 provenance；
- 可能同时存在的 disagreement 与 uncertainty。

Core 不提供全库 truth/confidence score。若具体应用需要计数或排序，它必须按自己的 scope 和目的解释，并通过
`duplicates assertion` connectivity 避免把同一 provenance occurrence 重复计算。

## Accepted material choice

1. `supports` / `challenges` 是有 provenance 的 evidence 对 assertion 的 defeasible stance，不是系统 truth label；
2. 同一个完整 pair 不同时写相反 stance；mixed/partial evidence 先 abstain 或物化 scope-specific findings；
3. Relation 不声称 evidence 独立，也不保存权重；duplicate-aware counting 与 request-specific weighting 留给后续 use。
