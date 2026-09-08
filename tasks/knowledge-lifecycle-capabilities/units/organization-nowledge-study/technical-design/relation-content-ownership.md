# Relation content 的代码权威与消费方式

- **状态**：D-520 accepted Technical contract。
- **问题**：exact Organization behaviors 的 Relation content 会同时出现在写入、查询、读取投影、跨模型一致性检查与
  tests 中；如何避免 raw string 散落，同时不引入全局 Relation content registry。

## 这是真实问题，但范围比 registry 小

当前仓库已有两种对照：

- RSS 的 `FEED_RELATION` / `ENCLOSURE_RELATION` 与 Memos 的 `PARENT_RELATION` / `REFERENCE_RELATION` 由各自 graph
  owner 的模块常量承担，producer 与 resolver 复用；
- media interpretation 的 `"interpretation"` 同时出现在候选过滤、结果检查与 tests，修改时容易漏掉。

本 unit 的 `synthesis`、`duplicates assertion`、`supersedes` 等还会被多个行为或 use path 精确过滤，因此不能让每个
caller 自己重复字符串。但这些语义没有一个全局枚举、发现、统一解析或 dispatch 需求；散落风险不能推出 registry。

## 四种权威必须分开

```text
exact Organization model / BehaviorResolver
  -> owns applicability、direction、admission and interpretation law

owner-local relation constant
  -> owns the exact persisted token used by runtime code

generic Relation / Graph Navigation
  -> stores and filters opaque content；owns no Organization vocabulary

consumer
  -> imports the exact owner's token or semantic read API；applies its own current use
```

Sir 所说“写方作为权威”在**语义准入**上完全正确：只有 duplicate assertion behavior 能决定何时写
`duplicates assertion`。但 durable token 同时是 writer/readers 之间的持久合同，所以更精确的代码位置是
**writer 所在 exact behavior module 的公开 `Final` 常量**，而不是散落的 literal，也不是 generic RelationManager 的
枚举。

首版直接使用普通常量：

```python
# exact duplicate-assertion behavior module
DUPLICATES_ASSERTION_RELATION: Final = "duplicates assertion"

# exact synthesis behavior module
SYNTHESIS_RELATION: Final = "synthesis"

# exact evidence-stance behavior module
SUPPORTS_RELATION: Final = "supports"
CHALLENGES_RELATION: Final = "challenges"
```

对应 BehaviorResolver 的 writer、candidate/replay queries 和同模块 semantic reads 全部引用这些常量。其它行为或
Application 需要精确消费时，从 owner module 导入它；Graph Navigation 仍只接收普通 `contents: Collection[str]`，不
import Organization。

这不是 registry：没有 central mapping、枚举所有 Relations、动态注册、handler lookup、metadata table 或未知值拒绝。
Extension 可在自己的 exact behavior module 定义自己的常量，不修改 Core catalog。

## 为什么不把常量只藏在 Resolver class attribute

`DuplicateAssertionBehaviorResolver.RELATION_CONTENT` 看起来最直接，但会让一个只需要持久 token 的低层 query/test
import 整个 orchestration class；该 class 可能同时拥有配置、Agent 调用和 registration side effects。多关系行为还会
迫使 class 暴露泛化的 `RELATION_CONTENTS` mapping，逐渐长成隐性 registry。

因此 authority 是 **exact behavior module**，BehaviorResolver 是其中的准入 writer。常量可由 behavior package
`__init__.py` 窄 re-export；消费者无需依赖 Agent/Job orchestration。若实现最终证明 Resolver class 本身没有这些 import
side effects，class attribute 也不是语义错误，但 module constant 的 dependency surface 更小。

## 两级消费，而不是一个 `consume_relation()`

### 1. 只需要图事实时

调用 generic read 并传 owner constant：

```python
GraphNavigationRetrievalManager.get_connected_components(
  seed_ids,
  contents=(DUPLICATES_ASSERTION_RELATION,),
)
```

或：

```python
RelationManager.get(block_id, content=SYNTHESIS_RELATION)
```

这种调用只是精确过滤，不需要 behavior wrapper。为了隐藏一行 constant 而增加一层 forwarding method 没有 ROI。

### 2. 读取需要模型解释时

当消费不是“取得 exact edges”，而是要执行 current frontier、完整 basis、scope/truncation 或其它模型规律时，由 exact
behavior 提供 typed semantic read，例如：

```text
Supersession behavior -> read_lineage(focal_block_id, bounds)
Synthesis behavior    -> read_basis(synthesis_block_id)
Graph Navigation      -> generic connected-components topology only
```

这些 read APIs 可以内部复用 owner constants 和 generic managers。它们必须返回真正的模型 projection，而不是只转发
`RelationManager.get()`；否则不新增方法。

duplicate component query 仍属于 Graph Navigation，因为它只计算 caller 指定 content 的拓扑。`count once`、临时
representative 或 synthesis 不虚增独立佐证属于调用方解释，不进入 query。

## 对先前 `Resolver.read_supersession_lineage()` 位置的修正

若把 `read_supersession_lineage()` 直接实现到所有 information content Resolver 的 base，它必须知道
`SUPERSEDES_RELATION` token，从而产生 `Resolver base -> Organization behavior` 的反向依赖，或在 Resolver 内复制 literal。
现在已经有 exact `SupersessionBehaviorResolver` 作为 behavior carrier，更干净的 candidate 是：

```text
SupersessionBehaviorResolver.read_lineage(focal_block_id, bounds)
  -> generic graph reads filtered by SUPERSEDES_RELATION
  -> typed current/history projection
```

focal Block 仍是查询输入和意义中心，但 content Resolver 只负责解释 Block；behavior Resolver 负责解释 Organization
Relation。这个位置修正 D-500 的实现选择，不改变已接受的 Product current/history contract。它需要单独 material review，
不能由常量重构暗中带入。

## Relation content 变更不是普通 rename

Relation content 已持久化到共享数据库，并参与 exact fetchsert/filter。把：

```python
DUPLICATES_ASSERTION_RELATION = "duplicates assertion"
```

直接改成另一个字符串，只会改变新 writer/readers；历史 Relations 会立即变成旧调用方看不见的数据。因此代码常量
解决的是**调用点一致性**，不解决**持久数据演进**。

稳定纪律是：

1. 已发布 token 默认不可随意改名；措辞审美不是迁移理由；
2. 语义不变而必须改 token 时，代码变更与显式数据 migration 同属一个变更，并验证历史 graph；必要时在混合版本窗口
   dual-read，但只写一个 canonical token；
3. 语义实质改变时使用新 token/新 contract；只迁移能够证明等价的旧 edges，不能用全表 rename 假装语义相同；
4. runtime tests 大多复用 owner constant，但至少一个 contract/migration test 用 literal 固定已发布持久 spelling，避免
   “常量和所有测试一起改绿了、历史数据却失联”。

这仍不需要 Relation registry；migration 只属于发生变化的 exact owner。

## 不建立的东西

- no global `RelationContent` enum / registry / metadata table；
- no `Relation.resolver` merely for constant lookup；
- no generic `consume_relation()` or behavior dispatcher；
- no class-level mapping that enumerates all relation outputs；
- no wrapper that only forwards an exact constant to `RelationManager.get()`；
- no automatic rewrite of Human/source-authored Relations that happen to use the same words。

## 已接受的 material choice（D-520）

1. relation semantic/admission authority remains the exact behavior；runtime token authority is one public `Final` constant in
   that behavior module，shared by writers and exact consumers；
2. generic graph layers remain vocabulary-blind；plain filtering uses the constant，non-trivial interpretation earns a typed
   behavior-owned read API；
3. changing a persisted token requires an owner-specific compatibility/migration decision，not merely a constant rename；
4. because the constant exposes an existing dependency contradiction，move the planned supersession lineage projection from
   information Resolver base to `SupersessionBehaviorResolver.read_lineage()`，without changing Product semantics。
