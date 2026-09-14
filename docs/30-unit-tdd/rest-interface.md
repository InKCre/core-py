# 普通 REST 界面

Core 提供普通 REST 供独立消费者使用。`cli/` 是首个完整消费者；它不安装 Core 或直接访问数据库。
普通 route 只拥有 HTTP 参数、响应和错误映射，管理与执行行为留在各领域 Manager。
精确路由及静态输入字段由生成的 [OpenAPI](../openapi.json) 维护，不在本文复制第二份 endpoint 清单。

## 不把 Peer inbound 当成公共 facade

`/retrieval/lexical`、`/retrieval/semantic` 调用领域 `retrieve` facade，可携带明确的 `route_to_peer`。
固定 Peer inbound `/lexical-retrieval`、`/semantic-retrieval` 始终调用 non-delegating local seam。
它们共用 JWT wire contract，但不因此共用 handler 或递归委托。

显式 collection/backfill 和 rumination 受理为 Job。成功创建只证明 Job 已持久化，不要求接入 Peer 能执行它；
异步 worker 扫描在响应之后触发，失败会记录日志，不撤回已受理的 Job。CLI 不调用 rumination Peer inbound。
Extension enable/disable 的普通 REST 可指定目标 Peer，安装、版本、启用意图和运行状态仍由 Host 拥有。

## 输入与发现

Core forms 是静态 HTTP 输入 authority。Source/Job types 读取持久 catalog，Resolver/Agent Tool/config schema
读取当前进程的 owner registry。发现不执行内容方法，也不承诺对应能力当前可成功运行。
schema 目录只投影已有合同，不新建 schema table。普通 config GET 返回保存的 schema/value，不重复验证。

创建输入与记录模型分开；PATCH 只写 `exclude_unset` 的字段，省略 storage 不意味着清空 storage。
Source config 在提交时完整替换；deployment/Extension config PATCH 合并完整候选后由 owner 验证。
关系记录在普通 REST 用 `from_block_id` / `to_block_id`；领域 `RelationModel` 和已有 Peer wire 不随之改名。

`request_input` 只包住本次输入的校验，保留 Pydantic/jsonschema 原始错误并补实际路径。Resolver invocation
把参数验证的异常标为原生 ValidationError 子类，route 只捕获这个输入异常；方法内部和输出故障保持真实 5xx。
不会将所有 ValueError、IntegrityError 或 ValidationError 全局映射为 422。

明确的记录写入通过 `database_write` 将 PostgreSQL 外键与 CHECK 冲突映射为 409，保留数据库给出的原因和
约束名。route 不预查引用或复制 CHECK 条件；连接故障、程序错误和生成主键碰撞仍保持服务器错误。

## 内容交付

普通值是 JSON，纯 bytes 是 `application/octet-stream`，嵌套 bytes 使用 `multipart/related`。第一项 JSON
是 `{value, parts}`；parts 把 value 中的 RFC 6901 JSON Pointer 映射到后续 binary part 的 Content-ID，
只有映射的 null 才代表 bytes。业务原有同形对象、普通 null 和字符串不被解释成引用。

`app/routes/content.py` 使用 aiohttp 的 MIME writer 完成一次响应，CLI 使用标准库 MIME parser 解码。
不调用第二次 Resolver、不增加内容缓存或下载会话。当前 producer 已持有全部 bytes，协议不宣称端到端
有界内存 streaming。raw 是 Block.content，hydrated 是 Block 的 Storage 读取结果；solved 由 Resolver 方法取得。

## 有界结果和实际错误

管理清单按自然 identity 提供可选 limit/cursor 与 `next_cursor`，Job 默认取最近 20 条。
没有自动翻页、总数查询或历史快照。Graph/recall 保留自己的查询边界，不伪装成相同分页模型。

批量实体读取保留输入顺序、重复引用和逐项内容读取错误；共享数据库故障仍是整个请求失败。
普通 HTTP 使用 FastAPI detail；不存在为 404，明确的状态冲突为 409，本次输入不合法为 422。
不额外包装 success/status，不用日志代替逐项结果。
