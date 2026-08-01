# InKCre Terminology Audit

> Repository evidence snapshot，最初采集于 2026-07-29；不是 durable product truth，也不维护
> program phase 或当前问题。后续决定以 [decisions.md](decisions.md) 为准。

## 1. 方法与约束

本审计只记录已经能从以下来源证明的语言和行为：

1. Sir 给出的产品语言；
2. Hub `10-prd` 中的产品术语与可观察行为；
3. Hub `20-product-tdd` 中的跨单元合同；
4. core-py / client-web 的本地文档、schema、代码路径和测试；
5. git 历史中可以证明的旧设计含义。

其中 Hub 只能证明“现有文档写了什么”，不能单独证明设计正确；Sir 的产品判断按高置信度
输入记录，也不是无需核验的绝对事实。如果这些来源不一致，本审计记录冲突，不用新术语掩盖冲突。描述外部系统返回的
tweet、image、text、mail 等对象时，暂用“source 原生对象”这一解释性短语；它不是建议加入
glossary 的新领域对象。

`resource` 可以出现在 Memos 等外部 API 的原生语言中，但不是 InKCre 已确认的
通用概念。`source_key` 也已撤回：如果候选模型无法说清 key 在世界中指向什么，
就应回到 source-native identity 与 source instance 的语义，而不是换一个 opaque 名字。

## 2. 当前相对稳定的名词

| 术语 | Hub 产品含义 | 当前实现中的实际指代 | 审计结论 |
|---|---|---|---|
| `info-base` | 存储并链接可复用信息单元的共享记忆中心 | 没有单一 `InfoBaseModel`；由 blocks、relations 及其持久化协调构成 | 产品边界，不是表或 Python package 的同义词 |
| `block` | info-base 中一个持久化信息单元 | `BlockModel`；`content` 是 inline 内容或 storage pointer，`resolver` 指定解释方式 | 当前唯一明确的通用持久信息单元 |
| `relation` | 两个 block 之间有向、有类型的链接 | `RelationModel(from_, to_, content)`；所谓类型目前只是自由文本 `content` | 图的持久边；“typed”尚无独立 schema/catalog 保证 |
| `source` | 从外部系统采集数据的 capability | 又被用于 source class、runtime instance 和 `sources` 表记录 | 产品能力含义稳定，代码/UI 层级严重重载 |
| `source type` | Hub 使用但未定义 | source class 的注册标识及 `sources_types` catalog row | 可复用实现/配置 schema 层 |
| `source instance` | Hub 使用但未定义 | `sources` 表中的一条 type/config/collect_at/state 配置记录 | 一个已配置的采集入口 |
| `collect job` | 一次 source collection 的执行记录 | `sources_collect_jobs` 的 PENDING/RUNNING/FINISHED/FAILED row | 与 source type、source instance 明确不同 |
| `resolver` | 解释 block 及其局部图上下文，产生可用意义 | resolver type string、class、instance；还实际承担去重、graph factory、breakdown | “解释”是已确认职责，其余职责是现状压力，不是已确认公共定义 |
| `storage` | block 未内联内容时，按 pointer 取得 raw content 的组件 | storage type、storage row、handler、`Block.storage` FK；内置实现是 HTTP fetch | 它是 raw-content 访问能力，不等于 PostgreSQL、bucket，也不等于“把信息持久化”这一动作 |
| `sink` | 检索或索引 info-base 内容供 downstream use 的 capability | core-py 的 embedding/reasoning/RAG；client-web 的 graph 可视化代码也放在 sink package | 产品能力词，不是持久对象 |
| `extension` | 可安装并增加 source/resolver/sink 行为的 capability | Python package/class/DB install row/runtime；Web 还有 Module Federation module/runtime | 共享产品词存在，但不同 runtime 的 artifact 与运行模型尚未统一 |
| `client` | 多 runtime 部署中的一个运行节点 | client record、core-py runtime、client-web runtime | 不是 HTTP client 的同义词 |

### 关键内容词

| 词 | 当前可证实含义 |
|---|---|
| `block content` | `BlockModel.content` 持久化字符串；可能是 inline 内容，也可能只是 pointer |
| `raw content` | resolver 实际拿到的原始内容；可能直接来自 block content，也可能由 storage 按 pointer 取得 |
| `solved content` | resolver 解释后的 runtime 表示 |
| `text for embedding` | resolver 为 embedding 生成的文字表示；不必等同 solved content 或 block content |

因此，后续不能笼统地用 “content” 指代以上所有对象。

### 四者的联合语义

分别定义 block、relation、resolver、storage 仍然不够。当前代码和历史共同支持：

1. block 是持久锚点，不等于完整的 runtime 信息对象；
2. `block.content` 没有固定的自解释格式：它可以是 inline source-specific payload，也可以是
   交给 storage 的 pointer；
3. storage 只回答“怎样从 pointer 取得 raw content”，不解释其含义；
4. resolver 由 `block.resolver` 选择，解释 raw content，并可读取该 block 的 local relations；
5. resolver 还可以取得 relation 另一端 block 的 resolver output，因此 relation 可以成为当前
   block 的动态内容，而不只是查询或可视化时使用的边；
6. use 消费的往往是 resolver 生成的 solved content / text / embedding text，未必是
   `block.content`。

直接证据包括：

- Tweet 的基础 JSON 放在根 block，attachments 放在相邻 blocks；`TweetResolver` 沿
  `attachment:*` relations 调用相邻 resolver，重建带附件的 Tweet；
- HTML block 以 URL 为 content、HTTP storage 取得 raw HTML，resolver 优先使用
  `text content` relation，否则把 raw HTML 转成 text；
- Image block 以 URL 为 content、image storage 取得 raw data，`alt:text` relation 可直接成为
  它的 text 表示；
- Mail 把 Email 与 EmailAddress 分成 blocks，以 `from` / `to` / `cc` relations 表达组合结构。

所以 `SubGraphForm` 只是 source / resolver 向 info-base 提交递归写入的表单；它不能替代上述
联合信息模型，也不能直接升格为 collection 的产品输出类型。

## 3. 当前动作语言

### Collection / `collect` / `record`

Hub 当前承诺：

- source 从外部采集数据；
- collection 产生可复用 block 或 relation；
- collect job 记录一次执行；
- observable outcome 是新增或更新的可复用信息单元。

core-py 当前行为：

1. source adapter 从远端 API/协议得到 connector-specific model，例如 `Tweet`、`GithubRepo`、
   `FeedItem`、`Email`、`TelegramMessage`；
2. source 或 resolver factory 将其转换成 `SubGraphForm`；
3. `InfoBaseManager` 持久化其中的 blocks 和 relations；
4. 没有另一种通用、独立持久化的“采集所得对象”。

`collect()` 是主动拉取，`record(data)` 是 webhook 等被动接收；二者在产品语言中都属于收集。

### Organization / `organize`

这个动作在现有文档与实现中没有统一含义：

1. Hub 说 organization 将 collected information normalize 成 blocks/relations；
2. source 的 `collect()` 已经在创建并持久化 blocks/relations；
3. `SourceBase._organize(block_id)` 是 source-specific post-collection hook；
4. `BlockManager.organize(block)` 调用 `Resolver.breakdown()`；
5. 历史实现曾在 source 收集并持久化 block 后，再异步调度 `_organize`；
6. client-web 没有 organize 产品/API/UI 表面。

Sir 已给出新的高置信度产品定义：organization 是打理已经存在的 info-base，使后续 use
效果更好；它不是 collection 的一部分。breakdown、merge、linking 是当前已知能力，不构成
organization 的完备枚举。当前任何一个 `organize` 实现都不应作为新设计约束，但仍可作为
历史证据或可复用实现接受审视。

### Breakdown / Linking / Merge

| 动作 | 当前证据 |
|---|---|
| `breakdown` | Resolver 有 generator contract；只有 ImageResolver 原型会派生 blocks/relations |
| `linking` | 没有同名 domain API；目前通过创建 `RelationModel` / graph arcs 表达 |
| `merge` | 没有 block/relation consolidation 行为；SQLAlchemy `session.merge` 与产品 merge 无关 |

这三个词来自本任务的产品需求，尚未进入 Hub glossary 或跨单元合同。

### Retrieval / Query / Search / Application

当前存在至少四种不同动作，不能混称：

1. 按 ID 取得 block/relation；
2. storage 按 pointer 取得 raw content；
3. sink 用 embedding/reasoning 找相关 blocks；
4. client-web 读取全图并做布局、community detection 和导航。

`search` 在 core-py 还常指 IMAP/Twitter 等外部协议查询；client-web 首页的 search 只是占位。
“应用”是本任务的上位能力语言，但当前没有对应的领域对象或统一 API。

## 4. 当前实际拓扑

```text
extension artifact/class
  -> 注册 source / resolver / storage / sink runtime capability

source type
  -> 配置 source instance
  -> collect job
  -> source collect() / record()
  -> source 原生对象
  -> 编码为 blocks + relations（当前常由 SubGraphForm 承载写入）
  -> InfoBaseManager 持久化
  -> info-base graph

block
  -> inline content，或 storage 按 pointer 取 raw content
  -> resolver 结合 raw content + local relations + 相邻 resolver output
  -> solved content / text
  -> sink 做 embedding / reasoning / RAG

block
  -> BlockManager.organize()
  -> Resolver.breakdown()
  -> derived blocks / relations
```

client-web 大量通过 PostgREST 直接读写 source、job、extension、block、relation；这与 core-py
manager/REST 命令并存，属于跨单元 authority 冲突，不是术语定义本身。

## 5. 已证实的主要冲突

### C1 — source-specific 对象与 graph 的关系已经确认

- 已确认 block 继续是信息进入 info-base 后的基本持久信息单元；
- 已确认不应发明通用“采集所得对象”；
- Tweet、GithubRepo、FeedItem 等是 collection 的 source-specific 输入形状，不是 block
  之外的持久对象；
- collection 通过把 source-specific 数据保存为 block/relation graph 完成收集。

具体 graph 映射、identity 与更新语义仍需讨论，但不再存在并列 source object store 的歧义。

### C2 — “存储”自然语言与 `storage` 组件不是一回事

Sir 所说“收集就是将某物采集（存储）到系统中”的“存储”是持久化动作；InKCre 的
canonical `storage` 却是按 pointer 取得 raw content 的组件。后续中文讨论应使用“持久化到
InKCre”描述前者，保留反引号 `storage` 指后者。

### C3 — Organization 的产品方向已澄清，具体动作尚未定义

source graph construction、source `_organize`、resolver `breakdown` 和 Hub normalization 彼此
重叠但不等价。新设计以“打理已有 info-base、改善 use”为起点，现有实现不构成约束；
linking、breakdown、merge 的具体操作数、结果与正确性仍未定义。organization 不能先被假定
为单纯 graph rewrite：它可能需要 storage 取得 raw content、resolver 取得 solved content，
再形成新的 blocks/relations。

### C4 — Resolver 的核心联合职责与附加实现职责尚未分开

“解释 block”实际至少包括 raw content 与 local relations 的联合解释；这不是普通 blob parser。
代码还把 block identity/dedup、graph construction、breakdown 放进 resolver。后三者是否属于
resolver 必须由具体动作合同推导，不能因现有代码位置而默认接受。

### C5 — Retrieval 既是产品能力又被用于内部取数

raw-content retrieval、graph读取、embedding retrieval、reasoning retrieval、RAG 和 UI graph
navigation 目前缺少上位关系；“特征/语义/图导航检索”需要建立在明确的查询对象和结果之上。

### C6 — Extension 是共享记录，但不是共享 artifact/runtime 模型

core-py 的 Python artifact 与 client-web 的 Module Federation remote 使用同一 extension row；
`installed/enabled/running` 的共享语义已有合同，但 registry、artifact identity 和两个 runtime
如何共同实现它尚未定义。

## 6. Audit Conclusions

- `block` 是 source information 进入 info-base 后的基本持久信息单元；Tweet、GithubRepo、
  FeedItem 等只是 source-native input shapes，collection 通过 graph 持久化它们。
- block row 不独自拥有完整可用含义；resolver 联合 raw content 与 local relations 解释，
  storage 只在需要时取得 raw content。
- collection 可以为了正确持久化而拆分信息；organization 则打理已存在的 info-base、改善
  use。二者都可能读取 resolver/storage，不应用“是否从 graph 开始”做机械边界。
- `resource`、`observation`、audit、replay、通用 collected object 等没有获得项目事实支持，
  不应凭讨论便利引入领域语言。
- relation predicate、resolver 附加职责、extension artifact/runtime 与 retrieval 上位合同仍需
  由具体 implementable unit 证明，而不能从现有代码命名直接推导。

program 拆分与讨论顺序现在由 [capability-map.md](capability-map.md) 统一维护；当前 unit 是
[Memos extension](units/memos-extension/packet.md)，当前 delivery scope 是 backend MVP。
