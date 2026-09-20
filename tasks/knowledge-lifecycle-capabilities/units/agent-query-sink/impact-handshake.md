# Impact Handshake

2026-09-20。设计依据更新至 D-631，D-628 的四条产品验收旅程保留，关键 preflight 与设计修正核对已完成。
Sir 已授权本次 task packet 提交；尚未授权源码实施、推送或发布。

D-629/D-630 的领域归属与 controller/service 修正已反映于 P1；D-631 的文档 authority 纠正及 Hub meta
判断准则已反映于 P4，见 documentation-authority.md。未实现的新路径仍须按计划验收。

## 对象与变化

| 对象 | From → To | 影响与约束 |
| --- | --- | --- |
| 读取能力归属 | Organization 内六个读取工具与输入模型 → InfoBase、GraphNavigation、Resolver 各自领域 owner | 禁止 app/agent_tools；exact IDs 不变；Tool controller 调用领域 service，ResolverManager 分派至实例；不将 handler 整体塞进业务类 |
| SinkBase / SinkManager | 强制 hooks、可交错的实例管理 → hooks 默认 no-op、同实例管理操作串行 | 已复现 enable/disable 竞态；配置更新、删除与关闭使用同一管理边界。影响现有 MCP Sink，必须回归；运行 Job 不持锁 |
| Agent Query | 无实现 → AgentQuerySink、类型级 JobHandler、普通 submit_query_result 工具 | sink.config 引用既有 Agent；复用 Thread 与 Job，不建立新 runtime、持久会话或恢复机制 |
| REST / schema | 无 Query endpoint → 启用实例挂载 POST /sinks/{id}/query | 普通 REST JWT 依赖；202 + Job + Location；关闭撤下自己实际注册的 route 对象并刷新 OpenAPI；不是 Peer delegation |
| CLI | 无 Sink 管理与 Agent Query → sink 管理组、query 命令 | 只消费 REST，不 import Core；动态 schema 查具体实例路径，后续控制复用 job get/wait/abort |
| 数据与发行 | 既有 Sink/Job/Agent 表及 Core/CLI 发行机制 → 增加 type/catalog 声明与两个项目的 fragments | 无新表、列、schema migration或依赖；不 seed 实例、Agent；不改版本/发布编排 |
| 文档 | 旧工具 owner、消费者越权声明与缺失使用旅程 → 领域 authority、操作模板、CLI 文档与 Hub meta 判断准则 | Hub source 单独修改/发布后 Spoke bump；不修改挂载 docs/_shared；不改 client-web/ext-reg |

## 保持不变的合同

Query 读取 info-base，不为回答写 graph；结果是 answer + references。最后成功提交以闭合 Thread
历史为依据，Job 收尾尽力保存。正常返回有结果才 finished；取消、超时或异常保留真实 Job 状态。
LLM 不接收 runtime 预算计数或临时收尾消息。禁用 Sink 不取消已运行的 Job。

模型读取以文本/JSON 和已有媒体文字子图为限；不把 metadata 当正文，也不新增原始媒体 ToolResult
通路。输入在真实输入边界验证，不重复验证可信工具输出。结果保存不是实时或崩溃恢复保证。

## 执行与验证

按 [实现计划](implementation-plan.md) 的 P1–P5 推进：先移动共享工具，再实现 Sink/Job，接合动态
REST/CLI，完成文档与机械检查，最后跑 [四条验收旅程](acceptance.md)。共享工具迁移须验证旧
Organization 读取/写入；生命周期修正须验证 MCP 启停，不将隔离实验升级为自动化测试。

[Preflight 实测](preflight-evidence.md) 已覆盖动态 FastAPI 接合、真实 Thread 的六条路径、Sink 竞态、
真实模型工具调用、六工具完整 schema、catalog 收敛路径与静态基线。它不替代新 handler、持久化
收尾、CLI 和实际回答质量的端到端验收。

## 残余与授权边界

production 当前没有 AIModel，正式验收需通过已有管理接口配置模型及检索环境。新功能尚未实现，
所以 preview artifact 与最终 production/PyPI 验收尚不存在；这是实施后的交付阶段，不是已完成证据。
超大内容仍可能超过模型上下文；取消未闭合工具 batch、进程崩溃或数据库收尾失败仍可丢失结果。
不为这些已接受的上限引入隐藏截断、自动重试、恢复框架或额外索引。

等待 Sir 明确授权开始实施；后续 Git 操作与发布另行确认。本次获授权提交的内容仅为 task packet，
不含忽略目录内的隔离实验、开发环境产物或任何生产源码；未推送或写入 production。
