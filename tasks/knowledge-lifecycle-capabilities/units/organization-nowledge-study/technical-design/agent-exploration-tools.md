# Agent 初始候选之外的探索工具

- **状态**：D-521/D-522 accepted Technical contract。
- **问题**：低成本机制只能给 Agent 一个起点；若当前 Agent definition 没有继续搜索、读取和导航所需的能力，它看到的 candidate 就会从成本
  优化手段意外变成语义边界，违背已接受的 open-ended Agent law。

## 因果链

```text
初始 seeds 只优化自动运行成本
  -> 某些有效证据位于 seeds 或一跳邻域之外
     -> Agent 必须能发现对象、理解信息、检查图上下文和验证路径
        -> 这些能力直接复用现有 info-base 读取 authority
           -> exact behavior 仍独立判断并调用自己的精确修改入口
```

如果只给 mutation Tool，Agent 只能把预装上下文换一种说法。这里需要增加的只是当前行为实际要用的读取接口；
“Agent 不得任意访问数据库”不是 Product 或依赖边界，未来出现真实需要时增加更广能力并不违反本设计。首版不增加
数据库 Tool，是因为现有 Product contracts 已足够且新增接口没有已证明收益。

## 已有实现依据

- `AgentManager` 只绑定 definition 声明的 exact Tool IDs；它自身保持 graph-blind。
- lexical/semantic retrieval 已有独立结果和 bounds，不需要新的统一检索引擎。
- Resolver 的 public typed methods 才是异构 Block 的完整读取能力；`get_text()` / `get_label()` 只是其中两个共同方法。
- Graph Navigation 已有单 Block 邻域和有界 shortest path；不需要 Agent 自行拼数据库查询。
- MCP Sink 已证明相近能力可以组成外部读取接口，但它是 transport/外部 consumer adapter。本 unit 必须只复用底层
  Managers 和 contracts，不让 Organization 依赖 Sink，也不为两个 adapter 提前抽取新 facade。

## 首版三个 owner-coherent 元工具

### 1. `retrieve`

```python
retrieve(
  query: str,
  mode: Literal["lexical", "semantic", "hybrid"] = "hybrid",
  limit: int = 20,
  semantic_profile: EmbeddingProfileID | None = None,
  semantic_options: VectorRetrievalOptions | None = None,
)
```

lexical 与 semantic 的调用意图、query 和结果 bound 一致，适合共享一个 Tool ID。`hybrid` 并行执行两者，但返回值保留
两个独立分支：

```text
lexical -> LexicalRetrievalResult | mode error
semantic -> SemanticRetrievalResult | mode error
```

它不融合 rank/score、不制造统一排序，也不改变两个 retrieval owner 的现有合同。`semantic_*` 参数只影响 semantic 或
hybrid 分支；lexical 分支仍只有 query/limit 语义。这里采用的是相同 query intention 的 Tool composition，不依赖 MCP
Sink 的 `recall` 实现。

### 2. `resolver`

```python
resolver(action="describe", block_ids=..., resolver_types=...)
resolver(action="invoke", calls=(ResolverMethodCall(...), ...))
```

一个 discriminated action union 合并已经接受的 discovery/invocation：

- `describe` 返回 exact Resolver 的 public typed methods、description 与 input schema；
- `invoke` 重新读取 Block、选择 exact Resolver、验证 method arguments，并返回原 method 的 JSON-projectable result 或
  独立 error；
- `get_solved_content()`、`get_relations()` 和 Extension-specific `get_*`/`read_*` 不被压成 `label + text`；
- method 自己拥有 refresh、materialization、bounds 和返回语义；不能 JSON-project 的结果诚实 unavailable。

现有 MCP Sink 的 sink-local method reflection/invocation 只是机制证据。`ResolverMethodContract`、capability discovery 和
typed invocation 归 Resolver owner；MCP Sink 与 Organization adapters 各自向内依赖它，彼此无依赖。

### 3. `graph_retrieval`

```python
graph_retrieval(action="describe")
graph_retrieval(action="invoke", method="...", arguments={...})
```

Graph Navigation owner 以一个元工具公开其 public typed query methods，而不是为 neighborhood、relation neighborhood、
shortest path、random focal、duplicate components 分别增加 Tool ID：

- `describe` 返回当前 method name、description 与 input schema；
- `invoke` 以 schema 校验 arguments 并返回原有 Pydantic result；
- `db_session` 等执行依赖不成为 Agent 参数；
- 当前 `get_random_block()`、`get_block_neighborhood()`、`get_relation_neighborhood()`、`find_path()`，以及本 unit 增加的
  `get_connected_components()` 都由同一 Tool 到达；
- 后续 Graph Navigation owner 新增可公开的 typed query 时，不再增加 Agent Tool ID。

这不是把多个 Product owner 合成一个万能工具：它只覆盖 presentation-neutral graph-navigation retrieval。Relation
meaning、Resolver 内容解释和 exact Organization mutation 仍不属于它。

## 为什么首版不直接接受 SQL / Cypher

当前 Core 使用 SQLModel 和 PostgreSQL，不使用 Neo4j；Neo4j 的图查询语言是 Cypher，而不是 SQL。若目标是“让 Agent
直接表达任意图 pattern”，有三种档位：

| 档位 | 收益 | 当前成本 / 缺陷 | 判断 |
| --- | --- | --- | --- |
| Graph Navigation 元工具 | 一个 Tool 到达所有现有/新增 typed graph queries | 复杂新 pattern 仍需 owner 增加 method | **首版推荐** |
| 原生 PostgreSQL query Tool | 表达力强，几乎不需新增 Manager method | prompt 绑定 table/column/migration；任意 row shape；丢失 endpoint closure、`limit_reached` 等 Product result law | 暂无足够回报 |
| 引入 Neo4j/Cypher 或自建 translator | 原生 variable-length pattern language | 新数据库/同步 authority，或 parser/planner/runtime；远超当前 graph shape 的需要 | 不进入本 unit |

这不是禁止 Agent 访问数据库。若未来反复出现“Graph Navigation 每增加一种 pattern 就增加大量低价值方法”的真实
摩擦，raw PostgreSQL query 或正式 graph query engine 可以重新比较；当前四个已有方法加一个 component query 还没有
证明这个问题。为尚未出现的查询生态提前引入 SQL/Cypher，会把存储 schema 变成 Agent contract。

## Tool 组合与写入边界

这三个元工具是可复用能力，不是每个 Agent definition 的强制集合。每个 purpose-built definition 只声明它实际
需要的子集，并另外声明自己的 exact mutation Tool：

```text
retrieval/read/navigation Tools    # 观察 authority
  + exact behavior mutation Tool   # 写入该模型允许的区别
  + record_organization_candidate  # 谨慎路由已证明的其它整理需要
```

Rumination 可继续选用现有 `draft_graph` / `submit_graph`，因为开放 graph authoring 是它自己的行为合同；其它 exact
behaviors 不因此获得 generic `submit_graph`。三个共享元工具不认识 behavior token、SOP、candidate law 或 mutation，
也不 import BehaviorResolver。

## 依赖方向与落点

```text
purpose-built Agent definition
  -> Agent Tool registry 中的 meta-tool adapters
     -> lexical/semantic retrieval + Resolver + Graph Navigation

BehaviorResolver -> AgentManager.run(definition)
AgentManager      -X-> Resolver / graph / Organization
meta-tool adapters -X-> exact behavior semantics / mutation
Organization      -X-> MCP Sink
```

Resolver capability discovery/invocation 放在 Resolver owner；Graph query capability discovery/invocation 放在 Graph
Navigation owner；Agent adapters 放在 Organization-owned Agent integration module，而不是 `app/business/agent/`，后者
继续保持 graph-blind。首版不抽取 `OrganizationContext`、`Information`、`RecallFacade` 或共享 MCP projection layer。
这是当前实现选择，不是禁止其它 Agent Tool 访问数据库的能力边界。

## 验收要证明的差别

1. 初始 seed 的一跳邻域不含关键证据时，Agent 能经现有 lexical/semantic retrieval 发现 Block/Relation、通过该
   Block 的 exact Resolver 读取意义、导航其关系并产生正确 exact proposal；
2. `retrieve(mode="hybrid")` 同时返回 lexical/semantic 独立分支及 mode-local error，不融合 score；
3. 至少一个测试 Resolver 暴露 `get_text/get_label` 之外的 structured typed read，Agent 能发现并调用它，证明
   Organization 没有另造更窄的 Block read abstraction；
4. 一个无法解析的方法调用不取消同批其它 call；不能 JSON-project 的结果明确 unavailable；达到 path bound 返回
   `limit_reached` 而非 `not_found`；
5. 没有任何读取结果被持久化成新的 info-base authority；Agent definition 的实际 Tool IDs 证明不同 behavior 可选择
   不同子集；非 rumination definition 不含 generic
   `submit_graph`；
6. Resolver capability/invocation 与 exact behavior mutation 可以在不 import Agent Tool registry 或 MCP Sink 的情况下
   直接执行；MCP Sink 与 Organization 之间没有依赖边。

先前逐 method 建立六个 Tool ID，以及把 Block read 压成 `get_label/get_text` 的候选均已撤回；它们只保留在 D-521/D-522
的 correction history，不作为当前实现说明。

## 已接受的 material choice（D-521 / D-522）

1. 首版共享三个 Agent 元工具：`retrieve`、`resolver` 和 `graph_retrieval`；
2. `retrieve` 用 `lexical`、`semantic`、`hybrid` mode 复用同一 query intention；hybrid 保留两个原生结果分支，
   不融合 rank/score；
3. `resolver` 与 `graph_retrieval` 各以 `describe/invoke` 两种 action 提供当前 owner 的 public typed methods；新增
   Resolver/Graph Navigation method 不再增加 Tool ID；
4. 元工具只合并同一能力 owner；retrieval、Resolver、Graph Navigation 和 exact mutation 不折成一个万能工具；
5. 原生 PostgreSQL/Cypher 没有被禁止，但当前会把 storage schema 变成 Agent contract，且没有超出 Graph Navigation
   typed methods 的已证明 query need，因此不进入首版；
6. Organization 必须不依赖 MCP Sink。
