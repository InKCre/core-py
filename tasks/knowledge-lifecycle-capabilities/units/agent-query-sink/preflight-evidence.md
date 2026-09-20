# Preflight 实测记录

本文保留实施前实验的历史证据，不代表当前工作树或交付状态。后续实现与 Preview 验收见
[implementation-evidence](implementation-evidence.md)，当前阶段见 [packet](packet.md)。

2026-09-20，基线 676886a4d2242be2f14465523c3267a126b60fd3；git ls-remote 确认 origin/main 仍为同一
SHA。当前工作树只有本 task packet 改动。隔离脚本在忽略目录 `.runtime/agent-query-preflight.kj5RQX/`，
不作为新增自动化测试或发布源码。PDM 2.28.0；本机 FastAPI 0.139.2、Pydantic 2.13.4、HTTPX 0.28.1。

## 动态路由与 schema

执行 `PYTHONPATH=. pdm run python .runtime/agent-query-preflight.kj5RQX/spike.py`，使用真实 FastAPI
TestClient，但没有数据库、模型或生产服务。先请求 OpenAPI，再添加两个实例 router，分别调用、撤下
其中一个、重新加入并再次调用。两实例独立、schema 刷新、被移除路径 404、另一实例正常、重启无重复
均通过。普通 dependency 在实际请求中执行。

当前 FastAPI include_router 产生 `_IncludedRouter` 对象，而不是旧版假设的扁平 APIRoute 列表。
第一次脚本使用旧结构计数断言失败；改为核对实际注册对象、HTTP 行为和公开 schema 后通过。实施时
保存本实例实际新增的 route 对象，关闭时按 identity 移除；不通过全局 path 猜 owner，也不依赖私有类名。
挂载/撤下后清空 app.openapi_schema 即可重新发现。CLI 用具体 `/sinks/7/query`，不能查不存在的
模板键 `/sinks/{sink_id}/query`。静态 OpenAPI 生成脚本不启动 Sink，此事实无需改变。

## Thread 的六条隔离路径

同一 spike 复用真实 Thread、InMemoryThreadPersistenceBackend 和 Pydantic 工具输入，仅替换模型
响应；不连接数据库或构造产品测试模式。结果如下：

| 路径 | runtime 结果 | 闭合历史中的成功结果数 |
| --- | --- | --- |
| 最后一次模型调用提交 | max_model_calls | 1 |
| 正常文字结束、未提交 | completed | 0 |
| 预算结束、未成功提交 | max_model_calls | 0 |
| 提交后下一次模型调用期间取消 | cancelled | 1 |
| 提交工具结束、同批另一个工具未结束时取消 | cancelled | 0 |
| 提交后 wall-clock timeout | timeout | 1 |

取消/超时均结束实际 Turn Task 与等待中的子任务。此证据证明 asyncio 传播和内存历史边界，不声称
新 Query JobHandler 已实现或数据库收尾已验收。AgentManager.run 在 start_turn 后没有 await，正常
返回 Thread 后直接 await current_turn 即可传播取消，不增加 detached runtime。

## Sink 启停交错

执行 `lifecycle.py`，保留真实 SinkManager.enable/disable，用局部替身替换持久化与 on_start 中的
外部等待。复现 enable 挂起 → disable 完成 → enable 恢复：enabled=false，running=true，on_close
未调用。用同一实例的 asyncio.Lock 包住完整两次管理操作，得到 enabled=false、running=false，且
on_close 已调用。

实施采用 Manager 内同实例生命周期串行化，不引入分布式锁、generation、回滚或 reconcile。运行 Job
不持此锁，disable 不等待 Job；无关 Sink 互不串行。配置更新/删除同实例也应使用同一管理边界，避免
启动中的旧 model 覆盖已保存配置或在删除后挂入；shutdown 沿同一关闭内部操作，不能把 enabled intent
清掉。失败仍保留可观察的 intent，实验不支持增加自动恢复承诺。

## 真实模型与内容体量

`handshake.py` 通过既有 AlibabaModelStudioDialect 调用 qwen3.5-omni-flash，两次真实请求完成
tool call → JSON ToolResult → 最终文字闭合，1.29 秒。只使用现有本地 dotenv 内 Provider 凭据，未
打印值、未写入任何 deployment 或改动 Agent/AI 源码。

`content_and_schema.py` 加载六个现有读取工具及 core Resolvers，将完整 schemas 交给同一真实模型；
服务端接受，模型选择 get_entities，实际 arguments 通过该工具现有输入模型。schema JSON 共
13,676 bytes；SHA-256 为 ba490bf85e162d0585d53005ca55055bac1e0dfc88f24dbcd68ab37afd292102。
该实验仅证明 schema/协议相容，不证明模型已经成功检索新 Query 的 corpus。

真实 HTMLResolver 对 SQLite 快照得到 12,002 字符、JSON 编码 12,262 bytes 的文本。拟用 corpus
不要求引入新文本分片/缓存工具。保持现有完整返回，不静默截断；任意超大材料的上下文管理仍是已知
上限，不能从该测量推导任意规模都可用。实际回答质量与长历史成本在 preview 记录。

## 工具移动、catalog 与运行环境

六 read handlers、_resolver_input_model、_project_json/_contains_bytes 迁出 organization/tools.py；
organization_behavior.py 的对应 read inputs、union 分支、EntityReference 同归共享适配合同。
不要与 MCP/REST 的同名参数类合并，它们有各自 wire 形状。get_connected_components 使用了写入
_exact_result helper，迁移时保留普通 ValueError 投影而去掉 OrganizationError 依赖；_exact_result
继续留给 Organization 写入。调用点由 rg 检查：Organization __init__ 导出及既有黑盒验收 imports
需更新，不能只让新 Sink 导入时才注册。持久 Agent definitions 的 exact Tool IDs 不变。

catalog.py::reconcile_builtins 已 upsert BUILTIN_JOB_TYPES；readiness.py 按相同 profile 检查字段。
增加 Query Job 属于已有 catalog 数据变化，db init 会收敛；无需新表、列或 schema migration。
Sink types 仍由 SinkManager.startup/sync_sink_types 发布，不能把 Sink instances 或 Agent seed 化。

SVC 最初检测到旧 dev image b3ccb00/source_matches=false。执行 `svc dev ensure database --repo .`
后已在同一声明的远程 Docker/volume 上更新为 676886a，migration head d41cc84db0c5，readyz=200，
未 reset/stop 数据库。只读盘点：13 Blocks、1 个 text-embedding-v4 模型、0 个 Agents。
production 的受保护 ai models 读取成功，当前为空；正式验收要先配置专用 Provider/模型及基础检索，
不能假定旧验收配置仍在。此准备在实施后的相应验收环境完成，不是本次对 production 的写操作。

基线 pdm run lint、pdm run typecheck、pdm run -p cli check、check_lock.py 与
check_migration_history.py 均通过。release.py projects 包含 core 与 cli；发行意图分别落根 .changes/
与 cli/.changes/，独立 Release PR 消费，CLI main workflow 用 Trusted Publishing 发布。
没有为本 unit 建 PR，故新功能的 preview 与 production 验收均尚未执行。

## D-629–D-631 后的补充核对

现有 AgentManager.tool 在注册时读取普通函数的唯一 Pydantic input 参数并保留 handler；input_model_factory
在绑定 Thread 时执行。controller/service 分离后仍是这一路径，不要求新增 classmethod 注册支持。
GraphNavigationRetrievalManager 已有三个图查询的业务方法，ResolverManager 已有方法合同与 invoke_method；
迁移只应补真实缺少的领域组合、移动 controller/schema，不复制查询/反射实现。

当前 Organization __init__ 导出六个读取工具常量，run.py 又经 Organization 路由/Jobs 导入触发注册；
所以 P1 必须改组合根和消费方 imports，不能只移动函数。普通业务模块不得反向导入 controller，
冷启动的实际无循环导入与完整工具发现是在改动后验证的事项，不声称本次只读核对已经证明。

文档核对发现 controller/service 的已有规则未被正确应用，且消费者章节在重复定义依赖合同。
这不能靠迁移源码自动修复；D-631 的逐项 owner、旧位置处理及 Hub/Core 分工已纳入实现计划。
