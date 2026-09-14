# 检索与 Graph REST

状态：按 [D-594](../../decisions/D591-D600.md) 确认；本页只收敛 CLI / 普通 REST 的新增合同，不重开检索算法或 graph
持久化设计，尚未实施。

## Recall 的模式组合

普通 REST 分别提供 `POST /retrieval/lexical` 与 `POST /retrieval/semantic`，调用对应 Manager.retrieve。
请求沿用 LexicalRetrievalRequest 与 SemanticRetrievalRequest；可选 query parameter route_to_peer 交给领域
门面，不写进业务 body。省略时沿用当前门面的本机执行行为；不增加自动切换能力或新的 Peer capability。

既有 `/lexical-retrieval`、`/semantic-retrieval` 是已发布的 Peer inbound，继续调用 retrieve_local，保持原
请求/响应及路径。不能将这两个 handler 直接改为可委托入口，再让目标 Peer 递归调用同一门面。新增普通 REST
与既有 Peer 路径可以共享同一领域实现，不按 HTTP 客户端、JWT 或隐藏 header 猜请求意图。

```sh
inkcre-cli recall 'Agent 工具' --mode lexical --mode semantic --limit 10
inkcre-cli recall '如何减少工具调用的认知负担' --mode semantic --profile 7
```

mode 必须显式选择，重复的相同 mode 按首次出现去重；只发对应请求。两种模式使用同一已选 connection，
可以并发请求，输出仍按选择顺序。limit 是每个模式的限制，不是合并后的总数，沿各 owner 的合法范围校验。
semantic 的 profile、min_score、entity_types 由相应选项映射到现有 profile/options；不支持它们的模式不能静默
吞掉这些选项。CLI 可提供 --peer，将同一个明确目标分别传给已选检索请求；不是全局执行 Peer 设置。

CLI --json 的顶层始终是模式结果数组，即使只选择一种模式：

```json
[
  {"mode":"lexical","matches":[]},
  {"mode":"semantic","profile":7,"metric":"cosine","matches":[]}
]
```

每项平铺对应 REST 结果并带 mode。lexical match 保留 block、label、excerpt、evidence、rank；semantic match
保留 type、entity、score，模式结果保留 profile 和 metric。不同模式独立保留命中，不跨模式比较分数、去重
实体或重新排名，也不在 Core 增加一个聚合 RecallManager / recall endpoint。普通 REST 单项结果不添加 mode。

某一模式失败时，同位置为 `{mode, error}`，已取得的其它模式结果不丢弃。D-597 已确认保留逐项输出并在
存在错误时退出 1；不把错误冒充空 matches，不自动重试另一种模式。大结果按已确认的同次
文件交付处理，JSON 不为体积而删除 Block content。

显式 profile 选择需要配套只读发现：`GET /embedding-profiles` 与 `GET /embedding-profiles/{id}`，CLI 提供
`embedding-profile list/get`。返回现有 profile 记录，不增加写入管理、可用性探测或配置表。该接口由已有的
SemanticRetrievalManager 提供；当前 profile 消费与选择已在这里，不因模型声明在 schemas/ai 内就把它推给
AIManager。模型本身仍由已确认的 ai models 发现。

## 图查询

| CLI | 普通 REST | 参数和结果 |
| --- | --- | --- |
| graph neighborhood block:42 | GET /blocks/42/neighborhood | query 为 direction、contents、limit、cursor；返回 BlockNeighborhood |
| graph neighborhood relation:8 | GET /relations/8/neighborhood | 无额外遍历参数；返回 RelationNeighborhood |
| graph path --from 42 --to 84 | POST /graph/path | body 为 from_block_id、to_block_id、direction、contents、max_hops、max_explored_blocks；返回 PathResult |
| graph components 42 84 | POST /graph/components | body 为 seed_block_ids、contents、max_explored_blocks、max_explored_relations；返回 ConnectedComponentsResult |

邻域 query 中 contents 使用重复 query parameter；复杂图查询用 JSON body，不给 GET 塞 body，不发明关系
过滤 DSL。REST Form 的 from_block_id/to_block_id 映射到现有 find_path 的 from_block/to_block。components
仍要求选择关系 contents；不把它扩成全图 community detection。默认值和边界沿用当前 Manager/schema。

上述结果沿用 GraphModel 的结构合同：graph.blocks 与 graph.relations 包含已读取的持久记录，关系端点闭合；
不调用 Resolver，不 hydrate，不追加 preview/布局。普通 REST 的 Relation 记录字段沿 D-583 使用
from_block_id/to_block_id，只在边界映射；不改领域 RelationModel 或既有 Peer wire。其它检索结果中嵌套的
Relation 记录也用同一普通 REST 投影，避免不同 CLI 命令为同一字段创造不同输出名称。

BlockNeighborhood 保留 focal_block、graph、next_cursor；RelationNeighborhood 保留 focal_relation、graph。
单个 focal 不存在时返回 404。path 保留 found/not_found/limit_reached；components 保留 components、proof_graph、
missing_seed_block_ids、truncated。未找到路径或达到探索边界仍是正常查询结果，不映射为 HTTP 服务故障。
这些字段说明一次查询所得的证据与界限，不是新增业务状态，也不让 CLI 自己重新遍历补齐结果。

GraphNavigationRetrievalManager 已可直接操作接入 Core 的共享数据库，因此这些查询不增加 --peer 或 Peer
capability；CLI 自身仍不接触数据库。当前模式不需要随机读取 endpoint 或全量导出 graph。

## Graph 写入

`graph submit --input graph.json` 对应 **POST /graph**。body 继续使用现有 GraphForm，不包一层 graph，不将
GraphModel 读取结果直接当作 producer form。成功 200 返回既有 SubmitGraphResult，例如
`{"blocks":[{"local_id":-1,"id":42}]}`，不为成功回执强制重读完整图。

当前 `PUT /graph` 调用的 submit_graph 每次创建新的 Block，所以同一表单重复提交不是替换同一 graph 状态。
将它改为 POST 符合实际的追加 command；不增加独立 Graph row、幂等 key、自动补发或兼容别名。
这里选择 200 表达 command 的完成，沿用可能为空的既有结果，不伪造一份可由 Location 寻址的“本次 Graph”资源。
GraphForm 的签名引用、字段与持久化行为保持其现有合同，最终公开 schema 必须与提交输入一致。

[RFC 9110 §9.3.3–9.3.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.3) 将 POST 的请求内容交给
目标资源按自身语义处理，而 PUT 表达创建/替换目标状态并具有幂等意图；这支持此次 method correction，
不是要求所有 append 操作都实现新的业务幂等机制。

## 核验依据与后续落点

- app/routes/{lexical_retrieval,semantic_retrieval}.py：现有 HTTP 路径就是 non-delegating Peer inbound。
  app/business/{lexical_retrieval,semantic_retrieval}/main.py 已有带 route_to_peer 的 retrieve 门面。
- client-web/packages/core/src/{lexical-retrieval,semantic-retrieval}/main.ts 使用 Peer delegation；普通 REST
  的新 DTO 投影不能直接替换它们消费的 Peer response。
- app/business/graph_navigation_retrieval/main.py 与 app/schemas/graph_navigation_retrieval.py 已拥有本批图查询
  和结果；当前 run.py 未挂载相应普通 REST route。
- app/routes/info_base.py 的 PUT /graph 调用 InfoBaseManager.submit_graph；该方法逐项调用 BlockManager.create，
  最后只返回本地负 ID 到持久 ID 的 mapping。Agent Tools 直接调用 Manager，不依赖这个 HTTP method。
- app/schemas/ai/main.py 的 EmbeddingProfileModel 已持久 id、name、ai_model、dimensions 与 timestamps；
  配套只读发现是使用现有 profile selector 的需要，不增设 profile 生命周期。

本批不修改 MCP 的结果拼装。后续 D-595 已将单实体原地编辑/删除纳入 CLI，详见
[实体修改方案](organization-write-rest.md)；同时修正现有 Block PATCH 把省略 storage 当作清空的输入丢失。
本页的 append graph 保持新增语义，不用于替代已有实体的 PATCH/DELETE。
