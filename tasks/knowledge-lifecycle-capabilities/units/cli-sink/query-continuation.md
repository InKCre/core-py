# 查询的长输出与续读覆盖

状态：2026-09-13 按 [D-600](../../decisions/D591-D600.md) 确认。D-597 已确认通用长输出原则，D-586 的文件交付、
D-594 的检索边界及 D-598 的可信响应消费保持。这里检查整个 CLI 查询范围，不新增查询会话或通用分页框架。

## 枚举集合与交付一次结果不同

管理清单和图邻域可以继续枚举当前集合；recall 返回本次选出的候选，path/components 返回一次有界探索的
结果，Resolver 则返回其方法定义的值。接口应提供适合这些结果的续读方式，而不是给每个操作机械增加 cursor。

| 查询范围 | 逐步读取方式 |
| --- | --- |
| Source、Cron、Agent、Peer、Extension、deployment config、AI model、embedding profile 列表 | 可选 limit/cursor，保留列表元素的既有 DTO |
| Source/Job type、Resolver、Agent Tool、config schema 目录和 Resolver methods | 同样支持枚举分页；精确对象与 schema 读取不变为目录遍历 |
| 本机 connection list | 同一可选分页语义，在本地清单上执行，不访问 Core |
| Job 历史 | 沿 D-597 的默认 20 条、Job ID 降序与 next_cursor |
| Block neighborhood | 复用现有 Relation ID cursor，每页仍包含所返回 Relations 的两端 Blocks |
| Relation neighborhood | 一个 Relation 与其两端，整体返回；若记录内容过大，沿文件交付读取 |
| lexical/semantic recall | limit 仍是各模式的候选数量；完整返回本次 matches，不伪造候选范围外的下一页 |
| graph path / components | 整体交付本次图与查询边界；长结果保存后分段检查，不切碎 GraphModel 冒充完整图 |
| 显式 ID 批量 get | 完成调用者提交的批次，保留顺序、重复引用与逐项错误；不在读取后静默丢掉后半批 |
| 单对象详情、单个 schema、Resolver invoke | 完整值交付；方法自身若有分页参数则按发现的合同传入，不另套 CLI 分页参数 |

get 的调用者可以主动把 ID 分成多批，或明确选择 content=none，但 CLI 不偷偷替它修改请求。单个对象包含
长数组、schema 或正文时，不因它不是 list 指令就忽略长输出；同样沿完整文件交付读取。本地文件不是服务器
查询的下一页，不能用“文件已保存”宣称已经完整枚举尚有 next_cursor 的集合。

## 为所有清单补上可选分页

除 Job 沿既定默认 20 条外，保留 D-597 的小清单默认完整返回。调用者可用 --limit N 指定本次条数，
--cursor 指向上一页位置；REST 对应同名 query parameters。省略 limit 就返回 cursor 之后的剩余清单，
不增加另一个隐式上限。所有这些调用仍受默认可读呈现预算和显式文件交付控制。

为使 JSON 本身携带续页位置，这些枚举结果由裸数组调整为“领域清单 + next_cursor”。没有指定分页
时也保持同一形状，不因结果大小或是否传入 limit 改变类型。它不是所有命令的 success/data/meta 包装。

```sh
inkcre-cli source list --limit 10 --json
inkcre-cli source list --limit 10 --cursor 42 --json
```

示意结果为 {"sources":[...],"next_cursor":42}；没有后续记录则 next_cursor=null。其它列表使用自身的
清单字段，例如 agents、peers、configs、resolvers；Resolver methods 在既有 resolver/methods 对象上加
next_cursor。详情、schema 精确查询、Resolver 返回值、批量实体结果和 recall 模式数组不跟着改成分页包装。

除已有 Job/邻域降序外，沿 D-597 的自然 identity 升序。数字 ID 使用数值，Peer 使用 UUID，配置使用 key，
Extension 使用完整 coordinate，类型/Tool/Resolver 使用 exact ID，方法和本机连接使用 name。cursor 就是
该查询最后返回的 identity；不增加 Base64 编码、签名或游标存储。返回格式保留实际 identity 的 JSON 类型。

有 limit 时读取 limit + 1 个元素判断下一页，不计算 total；分页条件与排序使用同一个 identity。数据库查询
留在相应 Manager；内存目录或 Host 已提供的完整清单可以排序后切页，不为此改外部 Extension Host 协议。
不存在全局 QueryManager，不要求调用者理解每个清单的存储方式。精确 schema 查找仍按已知 selector 取得，
不能先分页后在第一页里寻找目标并误报不存在。

分页是实时读取，不是跨请求快照。删除上一页的 cursor 对象后，后续比较仍可继续；并发增加、删除或修改
过滤字段可能改变后续可见集合。保留相同过滤条件、显式决定是否继续由调用者负责；不自动取完全部页面，
不增加分页重放或稳定快照机制。字符串的比较与排序必须由同一实现完成，不能混用数据库和 CLI 的不同排序。

## 有界查询和完整内容不增加第二份生命周期

目前 lexical limit 最大 20，semantic limit 最大 100，混合 recall 的 limit 对每个模式独立生效。
这两个值来自当前 schema，不是 CLI 新增限制。它们没有下一页合同；本轮不重开检索算法，也不因打印预算
重新生成 query embedding，或以逐次扩大 top-k 的方式伪装 continuation。

Graph path 的 limit_reached 和 components 的 truncated 表达本次探索边界，不是保存了待续跑的遍历。
调用者可明确修改下一次查询，但那是新查询。Block neighborhood 则已有真正的 next_cursor，直接沿用；
每一页保持端点闭合，不能只为减少字数把 Relations 与它们的 Blocks 拆到互不完整的页面。

默认可读输出超预算时，按 D-586 保存同次结果的完整入口文件并给有限预览；Agent 可用自己的文件工具或
shell 对该文件逐段读取。--output-dir 可主动选择这种交付。--json 保持完整紧凑 JSON，不自动替换为路径、
不截断；实际 bytes 仍用 file 引用。不增加 CLI 专用文件阅读器、结果缓存数据库或服务器 TTL。

Resolver 结果尤其不能通过重复调用取得“下一段”：get_solved_content 等方法可能 materialize，重复执行
不是对同次返回的续读。若一个具体 Resolver 方法本身定义了 cursor/limit，这些仍是方法 arguments，按其
动态 schema 调用，而不是 CLI 猜测所有方法都可分页。

## 核验依据与后续验证

- app/business/graph_navigation_retrieval/main.py::get_block_neighborhood 已按 Relation ID 降序取页，返回
  next_cursor，并读取两端 Blocks；Relation neighborhood 最多一条边与两个端点。
- app/schemas/{lexical_retrieval,semantic_retrieval}.py 定义各自 limit；SemanticRetrievalManager.retrieve_local
  每次执行 AIManager.embed，随后选出本次 matches，没有查询结果会话。
- app/schemas/graph_navigation_retrieval.py 中 path/components 没有 continuation；components 的 proof_graph
  与成员集合必须和同次探索结果一起解释。
- app/schemas/source/main.py、cron.py、agent.py、ai/main.py 的管理记录使用数字 ID；PeerRef 为 UUID，
  deployment config 使用 key。app/routes/extension.py::list_extensions 当前直接返回 Host 的完整记录。
- 当前 API 并未普遍具备本页的分页能力；不能因 packet 已列举全部命令就宣称实现覆盖完成。

实现计划应逐项核对“分页输入、查询 owner、续页输出、长字段文件交付”，而不是只检查 Job。预演选择一个
持久清单、一个动态目录、已有图邻域和一次较大 Resolver 结果检查完整调用链；运行验收沿手工/脚本黑盒，
不为每种清单的相同包装和映射新增自动化测试。CLI 响应继续只解码与转换，不按 Pydantic 再验证业务输出。
