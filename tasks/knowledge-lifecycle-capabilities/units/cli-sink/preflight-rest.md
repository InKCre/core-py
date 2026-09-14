# 普通 REST 的接合预演

2026-09-14，P3。这里是代码/事务落点，不是另一份业务规则定义；公开形状仍以已确认的各 REST 设计页为准。

## Manager、事务和路由

| 接合面 | 已核验的接口与实施注意点 |
| --- | --- |
| GraphForm | `InfoBaseManager.submit_graph(graph, db_session=None)` 无外部 session 时自己 commit，否则 flush。普通 REST 改为 POST，复用该事务，不在 router 重做 graph 写入。 |
| Block PATCH | `BlockManager.edit_block` 的 storage 使用未提供 sentinel；必须用 exclude_unset 保留 omitted，与显式 null 区分。不得用完整 BlockModel 默认值拼 PATCH。 |
| Relation PATCH | `RelationManager.update` 的 from_/to_/content 也有 omitted 语义；沿现有 owner 写入和 commit。单实体 delete 的 false 映射为未找到，不假装已删除。 |
| Source CRUD | 补现有 owner 的查询、update/delete，不创建通用 CRUD service。只写可编辑字段，不覆盖 cursor/state；已有 Source anchor 才同步 projection，改名不额外创建 anchor。 |
| Job / Cron | 复用 Job 参数的输入规范化，不因接入 Peer 无 handler 而拒绝保存。Cron 验证参数但不创建 Job；run-now 显式创建 Job，不改 last_scheduled_for/last_job。 |
| Agent / AI / profile | Agent definition 管理在 Agent owner；模型发现属于 AI。工具目录可发现已注册 schema，不要求提前 bind 一次完整 Agent 才能列表。 |
| Deployment config | `/config-schemas` 独立于 `/configs/{key}`；raw GET 不依赖加载 schema。PUT 的新建/更新状态在写事务中确定，不用先 GET 再猜。 |
| Peer | `/peers/self` 在 `/{id}` 之前注册；它是别名。wake 只对已知 HTTP 地址做有界请求，不引入新的发现/唤醒协议。 |
| Resolver | reflection 位于 `app/business/info_base/resolver/main.py`，不是 inspection.py（后者是媒体内容检查 helper）。REST 直接用其发现和 invoke_method；输入模型在那里构造，不反向调用 MCP tool 或再验证一次。 |
| 内容响应 | JSON / bytes / multipart 只在 HTTP 边界投影；既有 aiohttp writer 与 stdlib email parser 实验已验证 bytes 保真。不改 Resolver 返回模型，不新增下载会话。 |

保持同步 SQLModel CRUD 用同步 route、异步 resolver/运行操作用 async route 的本轮取舍，不借机迁移整个
数据库驱动。列表续读见 query-continuation.md；静态目录、动态目录和持久列表分别核对，而不是只给 Job 分页。

## catalog-only 的输入不是 typed defaults

持久目录实际表名是 `sources_types`（不是 source_types）。接入 Peer 可以仅从该目录得到 config/job schema，
使用已有 JSON Schema validator 校验新提交；不要求 instantiate Source，更不运行 can_handle。
JSON Schema 的 default 是 annotation，不会像 Pydantic 自动填默认值。保留未提交字段，在真正执行端由
Source 自己的模型恢复默认值；不能为模拟默认值自建 schema decoder。

Source-specific collect config 仍由 Source 边界拥有。Job/Cron 受理时复用源类型目录的参数校验，
不能因为外层 `parameters.config` 是 dict 就漏掉首次输入校验，也不能反过来把 Source 规则写死在 JobManager。
自定义 Python validator 没有完整反映到 JSON Schema 的限制按当前目录能力接受，不虚构远程代码校验。

## 确认不动的现有消费者

client-web origin/main 的以下代码使用 Peer delegation，而非将要提供的普通 REST：

- `packages/core/src/semantic-retrieval/main.ts`、`lexical-retrieval/main.ts`、`organization/main.ts`。
- `apps/client-web/src/extension-peer-control.ts`。
- `extensions/twitter/src/setup-api.ts` 与 `extensions/mail/src/resolver.ts` 的 Extension-owned capability。

保留精确的 `/semantic-retrieval`、`/lexical-retrieval`、`/organization/ruminate`、`/extension-management`
inbound 和 non-delegating local seam。新增普通 `/retrieval/*` 可以接领域 facade；Graph 查询可直接使用
本 Peer 的数据库。共用 HTTP 并不使 CLI 成为 Peer，也不授权修改上述 capability 协议。

Core output DTO 只表达输出，CLI 只做 JSON/MIME 解码和呈现。FastAPI 的 response serialization 不应再次
调用输入侧业务 validator；配置 raw value 和 runtime-owned 内容不套一套新校验模型。最终 OpenAPI 生成
与 router 顺序检查在代码落地后执行，动态 Extension 目录不从静态 OpenAPI 反推。
