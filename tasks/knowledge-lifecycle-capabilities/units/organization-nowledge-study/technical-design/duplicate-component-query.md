# 重复断言的连通分量读取与解释边界

- **状态**：D-510/D-511/D-520 accepted Technical contract。
- **目的**：让 `duplicates assertion` 具有可恢复的查询方式和明确 use law，而不是只把 Relation 写进图；关闭有界
  连通分量查询的精确返回合同，但不为 Organization behavior 强行指定当前具体消费者。

## 真实失败与因果链

假设 synthesis 候选取得三项信息：

```text
A：原始发布中的断言
B：转载 A 的同一断言
C：独立测量得到相同结果

A --duplicates assertion--> B
```

如果 synthesis 只读取三个 Block 的文本，它可能把 A、B、C 误写成“三个独立来源一致”。这个错误不会被普通相似度
或来源数量修复；`duplicates assertion` 已经表达 A/B 共享同一断言来源事件，但 consumer 必须实际读取它。

```text
错误的 synthesis corroboration
  -> duplicate relation distinguishes non-independence
     -> bounded component query recovers A/B grouping
        -> synthesis treats {A,B} as one provenance basis for independence claims
           -> copied occurrence no longer multiplies evidence
```

这是该 Relation 的一个清晰集成案例，不是它的 Product 起点或指定消费者。`duplicates assertion` 的稳定承诺是：未来
任何依赖证据独立性的 use 都能把一个完整 component 解释为一次来源贡献。synthesis 若碰到这项区别，必须遵守该规律；
但 duplicate behavior 不依赖 synthesis 存在，也不需要新建“证据应用”来证明自己。

## 为什么不是 induced subgraph

调用方本次 seeds 可能是 `{A, C}`，而实际图是：

```text
A --duplicates assertion--> B --duplicates assertion--> C
```

只读取输入 seeds 之间的 Relation 会漏掉 B，并把 A/C 错分成两个来源。查询必须从 seeds 向外沿指定 Relation content
补全连通路径；外部发现的 B 只用来证明连通性，不自动成为 synthesis source。

## Graph Navigation 合同

新增一个 presentation-neutral 的 Manager 方法：

```python
GraphNavigationRetrievalManager.get_connected_components(
  seed_block_ids,
  *,
  contents,
  max_explored_blocks=1_000,
  max_explored_relations=10_000,
  db_session=None,
) -> ConnectedComponentsResult
```

`contents` 必须非空；调用方必须明确自己要沿哪些 exact Relation meanings 计算无向连通性。方法不内置
`duplicates assertion`、provenance 或计数语义，因此仍属于 Graph Navigation，而不是 Organization。

返回值为不可变 projection：

```python
class ConnectedSeedComponent(BaseModel):
  seed_blocks: tuple[BlockID, ...]
  member_blocks: tuple[BlockID, ...]

class ConnectedComponentsResult(BaseModel):
  components: tuple[ConnectedSeedComponent, ...]
  proof_graph: GraphModel
  missing_seed_blocks: tuple[BlockID, ...]
  truncated: bool
```

- `components` 始终只 partition 本次存在的 input seeds；每个 seed 恰好出现一次；
- `member_blocks` 包含本次已观察到的完整 component members，包括 seeds 和为确认连通性而发现的外部 Blocks；
- `proof_graph` 只需返回证明已观察连通性的 spanning Relations，并保留其真实持久方向；它不伪装成完整 induced
  subgraph；
- `missing_seed_blocks` 显式保留删除竞态或错误输入，不静默丢弃；
- 任一 block/relation exploration bound 到达时 `truncated=true`。此时 components 只代表已观察到的连通性，不能证明
  不同 components 确实独立。

同时限制 `len(distinct seed_block_ids) <= max_explored_blocks`；否则输入本身已经超出调用者声明的 bound，直接拒绝，
而不是返回一个连 seeds 都无法完整表示的结果。

## 读取算法

首版在一个调用方 session 中做普通 breadth-first expansion：

1. 批量读取并去重 input seeds，记录 missing IDs；
2. 从一个尚未归组的 existing seed 开始，双向读取 exact `contents` Relations；
3. 只把第一次发现某 Block 的 Relation 加入 `proof_graph`，形成 spanning proof，避免把 component 内所有冗余边都
   返回给 caller；
4. 若扩展遇到另一 input seed，把它加入同一 seed component；
5. component 完整结束后再从下一个尚未归组 seed 开始；
6. 达到任一 bound 时停止向外扩展、标记 `truncated`，并把尚未观察为相连的 input seeds 保留为各自 provisional
   component。

Relation scan 必须分页并计入 `max_explored_relations`。只限制 Block 数而不限制高 degree 节点的 Relation 扫描，并不是真正
的有界查询。实现可复用现有 `RelationManager.get_endpoint_page()`；不增加递归 SQL、持久并查集、component table 或
duplicate-specific index。

当 `truncated=false` 时，返回的 partition 对当前 exact Relation filter 和当前事务可见图是完整的；它不对调用完成后的
并发新边提供 snapshot 之外的保证。

## 一个重要集成案例：synthesis 怎样使用

`SynthesisBehaviorResolver` 在形成候选来源区域后调用：

```python
result = GraphNavigationRetrievalManager.get_connected_components(
  candidate_source_ids,
  contents=("duplicates assertion",),
  ...,
)
```

然后把每个 input source 的 `duplicate_component`、可恢复 provenance context 和 `truncated` 明确交给 synthesis judge：

1. 同一完整 duplicate component 内的 Blocks 不能被当作多份 independent corroboration；
2. Agent 可选择当前最可读、来源路径最清晰的一个 Block 作为临时 source representative；这个选择不持久化，也不
   由 lower ID storage direction 决定；
3. 因 duplicate relation 已要求 whole-Block 等价且无 material asymmetric gain，最终 `source_ids` 通常只保留一个；若
   Agent 认为另一个仍有材料增量，说明现有 duplicate edge 或 endpoint granularity 有问题，不能一边保留 duplicate
   语义一边把它当独立贡献；
4. `truncated=true` 时仍可综合互补内容，但不得声称精确的来源独立数量或“多方独立证实”；必须保留不确定性，或在
   成本允许时提高 bound 重试；
5. 外部 member Blocks 只用于连通证明和 provenance context；除非 Agent 独立选择并验证其 material contribution，
   它们不进入 synthesis basis。

查询结果不直接删减 source IDs，也不替 Agent 选择 representative。Graph Navigation 只提供拓扑事实；synthesis model
拥有“一个 component 不增加独立佐证”的解释规律和最后 source-basis 判断。

## 为什么首版不增加 HTTP / MCP 接口

当前没有外部调用者需要单独请求 component，因此不增加 route、MCP Tool 或公共 transport schema。以后出现证据审阅
UI、Application 或 Extension consumer
时，再复用同一个 projection 增加边界适配；不能以潜在可用为由提前扩大 API。

## 验收要证明的区别

1. `{A, C}` 通过外部 B 连通时，返回一个 seed component 和能证明路径的 endpoint-closed `proof_graph`；
2. 独立 D 保持另一 component；singletons 不被遗漏；
3. 外部 B 不自动进入调用方 synthesis basis；
4. lower-ID Relation direction 不影响无向 component；返回 proof 保留真实方向；
5. missing seeds 显式返回；block/relation 任一 bound 截断都禁止精确独立计数；
6. synthesis 对 A/B/C 只能声称两项来源基础，且 A/B 中至多一个作为 whole-Block material source；
7. 不创建 component、representative、count 或 evaluation 持久状态。

## 已接受的 material choice（D-520）

1. Organization behavior 只需提供可复用区别、query projection 与稳定 use law，不要求绑定一个当前具体消费者；
2. Graph Navigation 返回 seed partition + spanning proof + missing + truncation，并同时限制 Blocks 与 Relations；
3. complete component 在任何 evidence-sensitive use 中只贡献一次 independence；若 synthesis 使用它，representative 是
   本次判断，不持久化；
4. 首版只提供内部 Manager 方法，没有 HTTP/MCP transport。
