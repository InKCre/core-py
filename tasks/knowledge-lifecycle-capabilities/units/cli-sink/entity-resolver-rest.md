# 基础实体读取与 Resolver REST

状态：2026-09-13 按 [D-583](../../decisions/D581-D590.md) 获 Sir 确认，尚未实现。沿用 D-575 的 get / Resolver
职责分离、D-577 的动态输入合同和 D-579 的内容交付原则。本页先收敛读取操作与逻辑结果，binary 的 HTTP
编码、文件引用和导出回执在下一段设计中补齐，不能把下面的 bytes 当作 JSON 原生值。

## 从领域能力接出普通 REST

`BlockManager.get_many` 与 `RelationManager.get_many` 已有按 ID 批量读取；`BlockModel.get_hydrated_content`
已有 Storage 语义。`ResolverManager.get_method_contracts`、`get_method_contract`、`invoke_method` 已拥有
公开读取方法发现、Pydantic 参数合同与执行。REST 调用这些 owner，不调用 MCP Tool 或 Organization Agent
Tool，也不新增 CLI 专用业务 Manager。CLI 仅经 HTTP 调用，不导入这些 Core 模块。

以下路径相对配置的 Core API 根地址。继续使用既有认证依赖，不注册新的 Peer capability；既有 Peer inbound
消费者不因增加这些普通 REST 入口而迁移。

## 批量取得基础记录

`POST /entities/get`，请求为：

```json
{"entities":[{"type":"block","id":42},{"type":"relation","id":8}],"content":"raw"}
```

CLI `get block:42 relation:8` 将 shell 引用转换为有类型的 ID，HTTP 不通过整数值猜实体种类。
`entities` 是显式 ID 数组；空数组得到空结果，不复制内部 Agent Tool 的空输入随机选择行为。
JSON body 使用 POST，而不是给 GET 添加 body；这不表示创建实体。

默认 `content=raw`，使 get 默认取得原始记录且不发起 Storage 内容读取。三个选项如下：

| 选项 | Block 响应 | Relation 响应 |
| --- | --- | --- |
| `none` | 不含 content / hydrated_content | 不含 content |
| `raw` | `content` 是原始字符串，包括可能的 pointer | `content` 是原始关系字符串 |
| `hydrated` | 不含 content，以 `hydrated_content` 返回本次 str/bytes | 仍返回原始 content；Relation 不存在 hydration |

这些是响应投影，不是改变 BlockModel。任何出现的 `content` 都保持持久字段的意义；未请求的字段省略，
不返回 null 来暗示内容不存在。`storage` 与 exact `resolver` 在所有 Block 成功结果中保留；不因 hydration
清空 storage、不解析 canonical JSON string，也不额外调用 Resolver 生成 label 或 graph context。

响应及 CLI `--json` 的逻辑结果为有序数组，单项请求仍返回数组。每项保留 `type`、`id`，成功项平铺基础
记录字段，失败项包含 `error`，不新增 success/status、entity 包装或 results envelope。数据库查询可以按
ID 集合读取，再按输入关联；不承诺数据库自然返回顺序。重复引用保持输入位置，不静默去重输出。

Block 成功字段为 `type="block"`、`id`、`resolver`、`storage`、`created_at`、`updated_at`，加选定内容字段。
Relation 成功字段为 `type="relation"`、`id`、`from_block_id`、`to_block_id`、`updated_at`，加选定 content。
端点命名沿用已有 MCP 投影的明确身份表达，只在 HTTP DTO 映射 `from_` / `to_`，不重命名数据库或领域模型。
这里不为 Relation 虚构当前没有的 created_at。

缺失引用返回同位置的 `{type, id, error: {code: "not_found", message: ...}}`。单个 Block hydration 失败
也保留同位置的错误，不丢弃其它成功项；整批共享的认证/数据库故障仍是 HTTP 请求失败，不能伪装成实体缺失。
本批次不是 graph snapshot，不承诺跨 Storage 与数据库的原子观察。字段级错误细节及退出码沿 D-597 的
[整体错误合同](list-error-contract.md)：保留逐项成果，存在逐项错误时退出 1，不建立新的业务失败状态体系。

## Resolver 发现与调用

| 普通 REST | 用途与 CLI 映射 |
| --- | --- |
| `GET /resolvers` | 当前进程已注册的 exact Resolver 目录；`resolver list` |
| `GET /resolvers/{resolver_id}/methods` | 指定 exact Resolver 的方法合同；`resolver methods --resolver …` |
| `GET /blocks/{block_id}/resolver/methods` | 从 Block 当前 resolver 取得相同方法合同；`resolver methods block:42` |
| `POST /blocks/{block_id}/resolver/methods/{method}` | 调用选定方法；`resolver invoke block:42 --method …` |

方法发现返回 `{resolver, methods: [{name, description, input_schema}], next_cursor}`，按 D-600 支持可选分页。
CLI 的短目录只投影名称与说明；
`resolver invoke … --schema` 从同一合同取选定方法的 input_schema，不执行内容方法。先沿用现有完整方法合同
读取，不为尚无传输瓶颈的目录另建 schema 缓存、逐方法路由注册或发现会话。Resolver 目录不需要先有 Block；
实际调用必须有 Block。未知 Resolver 与没有方法要区分，不能仅凭 get_method_contracts 返回空 tuple 混为一谈。

调用 body 就是方法参数，例如 `{"refresh":true}`，不额外包 arguments 或重复 method。无参数调用由 CLI
发送 `{}`。已知方法可以直接 invoke，不强制预先 discovery。Core 交给现有方法 input_model 校验一次；
CLI 不复制 Extension 模型，也不将 JSON Schema 反向编译成另一份运行时业务校验器。

成功结果保留方法自身的值：str 是 str，null 是 null，对象/数组保留结构，不加 `{result, status}`。
模型与 dataclass 是序列化对象，不把动态字段过滤为固定内容模板。含 bytes 的结果使用下一段待定的 HTTP
内容编码，CLI 再履行已确认的本地文件交付；不返回 MCP URI，也不为取回文件重执行 Resolver 方法。

POST 适用于这类实际调用：公开 get_/read_ 方法仍可能按已有合同 lazy materialize。REST 不把方法名当作
绝对无副作用承诺，也不扩展到任意 Python 属性或未被既有反射合同支持的方法。参数错误保留 Pydantic 的
字段路径，未知方法/不存在 Block/实际执行故障仍可区分；详细 HTTP 错误映射不在本页另造一套例外层。

## 实现前核验与证据

- `app/routes/block.py`、`relation.py` 当前只有部分单条/邻接入口，不能冒充已有普通 REST 批量接口。
- `app/business/info_base/{block,relation}.py` 的 get_many 返回已有记录，缺失项与输入顺序由边界投影补齐。
- `app/schemas/info_base/block.py` 的 hydration 返回 str/bytes，且保持持久 content 和 storage 不变。
- `app/business/info_base/resolver/main.py` 是方法 registry/reflection/invoke owner；实现时维持 validation 一次。
- `app/business/sink/projection.py` 已采用 from_block_id/to_block_id，但 MCP Resource 的 live reread 不能满足本
  CLI 的同次结果交付，不能直接把整个投影模块当普通 HTTP adapter。
- `pyproject.toml` 当前声明 FastAPI `>=0.139.2,<0.140.0`、Pydantic `>=2.11.7,<3.0.0`。
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/) 不推荐 GET body；POST + Pydantic request
  model 足以承载这里的异构 ID 数组。既有 Resolver 使用的动态模型也是
  [Pydantic 原生能力](https://docs.pydantic.dev/latest/examples/dynamic_models/)，不需要另建 schema 编译设施。

预演须覆盖混合成功/缺失、重复 ID、inline 与 storage-backed 的 raw/hydrated、有 bytes 的 solved object、
空/null 返回，以及 Extension 方法注册前后。这里只记录核验面，不新增自动化测试或宣称验收已冻结。
