# Agent 开发追踪

为了在一次真实运行后检查工具发现、参数错误、重复请求和预算截断，可以临时开启 Agent 调试日志：

```text
OBSRV__AGENT_DEBUG=true
OBSRV__LOGGING_BACKEND=postgresql
OBSRV__LOGGING_BACKEND_LEVEL=20
```

设置作用于运行 Agent 的 Peer，应用重启后生效。默认 `agent_debug=false`。本地仅查看标准输出时，backend 可以
保持 `none`；JSON 事件仍通过 `inkcre.agent.debug` logger 输出。启用 PostgreSQL backend 才会写现有 `logs` 表，
记录能够跨 Peer 进程重启保留，并通过现有 PostgREST 查询。不需要新增表、迁移或调试 HTTP endpoint。

PR preview 当前部署脚本显式配置 backend 为 `none`。仅部署带有追踪代码的镜像不会自动启用或保存调试记录；
需要给目标 preview Peer 同时配置上述开关与 backend，并核对实际写入后再开始需要轨迹的验收。

## 记录内容

`agent.thread.created` 保存 Agent ID/name、模型 ID、system prompt、实际绑定的 Tool descriptions/schemas、tool choice
和预算快照。每个 turn 记录输入、模型请求序号、模型返回、工具参数、工具结果、错误与阶段耗时。
结束原因包括 completed、max_model_calls、failed、cancelled。异常工具的调试事件保存异常类型、消息与 traceback；
`agent.tool.completed` 同时保留返回给模型的真实 `ToolResult`，包括批次内容中的子项错误。

每条事件包含 Thread ID 与 turn index；模型请求和工具事件含 call index，工具调用含 ToolCall ID。Job scheduler
已有的 `job.<id>` trace context 会传到这些日志。直接调用 Agent 的运行可能没有 Job trace，仍可按 Thread ID 查询。

事件正文 `body` 是 JSON；`attributes.agent_thread_id` 与 `attributes.event` 可过滤：

```text
GET /logs?trace_id=eq.job.42&order=id.asc
GET /logs?attributes->>agent_thread_id=eq.<thread-uuid>&order=id.asc
```

并发工具的完成顺序可能不同于调用顺序；使用 turn/call/ToolCall ID 对齐，不能只按行号推断依赖关系。
有 started 无 completed/finished 可帮助定位停顿，但也可能是进程中断或日志写入失败，不能自动判断为模型死循环。

## 使用边界

这是开发日志，不是 Thread persistence backend，也不提供重新执行、恢复、exactly-once 或执行状态 authority。
关闭追踪不会删除已有日志。按诊断 Thread/Job 的精确 ID 导出并清理记录，避免清理其它运行。

日志包含调试输入与 Tool payload，适用于明确选择的开发/验收环境。不会读取 provider config 或 HTTP authorization
headers，也不请求 provider 的额外 reasoning 字段。二进制内容只记录省略的字节数。
当前 AI response contract 不返回 token usage，因此此方案记录请求次数与耗时，不能声称得到真实 token 费用。

日志序列化和写入通过线程隔离；失败只报告调试输出不可用，不替换 Agent 的实际结果。开启后的写入会增加耗时，
尤其 PostgreSQL 每条日志独立写入；它适合临时开发诊断。没有额外队列、采样、保留策略或通用观测平台。
