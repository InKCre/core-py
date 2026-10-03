# 按需启用可观测性

新增遥测缺省关闭。现有 stdout、PostgreSQL 日志、`job.<id>` 关联和 Job 日志查询继续工作；显式配置的 `none` 或 Logtail 也继续生效。开启遥测会增加标准 OTLP 元数据出口，不替换 PG writer，不转发历史日志或任意 Python logger。共享行为由[跨 Peer 可观测性契约](../_shared/20-product-tdd/observability-contract.md)拥有。

## 配置与启停

每个 Python Peer 在运行环境或本地 `.env` 设置 `OBSRV__TELEMETRY_ENABLED=true` 才启用。配置 endpoint、认证头或安装 SDK 都不能自动打开它。修改后重启进程；没有后台配置探测或热重载。关闭态不初始化新增 provider、导出线程或队列，也不查询新增共享配置。

部署 owner 在数据库已完成初始化后运行 `pdm run python scripts/observability.py`。该命令只在 `configs` 缺少 `inkcre.observability` 时插入一次 UUID；重复运行保留已存在的身份和配置，不能用于重置克隆后的身份。它不会启用任何 Peer。独立 preview、数据库克隆或新 owner 的部署，在启用前显式更换 deployment ID。

共享配置 schema 是 `inkcre.observability.v1`，包含 `deployment_id`，以及可选的 `otlp_http_endpoints`（`traces`、`logs`、`metrics` 完整 URL）和 `diagnostics_url`。共享 URL 禁止 userinfo、query 和 fragment。私密认证始终留在服务端运行配置，不写入共享 value、浏览器 bundle 或诊断链接。

```dotenv
OBSRV__TELEMETRY_ENABLED=true
OBSRV__LOGGING_BACKEND=postgresql
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://your-otlp-host/otlp/v1/traces
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://your-otlp-host/otlp/v1/logs
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=https://your-otlp-host/otlp/v1/metrics
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic%20YOUR_ENCODED_VALUE"
```

当前出口为标准 OTLP/HTTP protobuf。三个 endpoint 使用完整地址，不自动添加路径；未配置的信号不导出。运行环境和 `.env` 的 per-signal endpoint 优先于共享默认值。认证支持公共 `OTEL_EXPORTER_OTLP_HEADERS` 和优先级更高的 `OTEL_EXPORTER_OTLP_{TRACES,LOGS,METRICS}_HEADERS`。服务名称、版本、运行实例由本实现提供，不读取任意 `OTEL_RESOURCE_ATTRIBUTES`，避免将配置原文引入 Resource。

Python 在数据库准入、Peer 注册之后读取一次共享配置，读取限时两秒；配置缺失、无效或读取失败时暂停新增遥测，不影响业务 readiness。单信号初始化失败只报告不含原始配置的本地诊断，不改变业务 readiness 或 PG 生命周期。配置恢复后需要重启，不自动轮询重试。

Grafana Cloud Free 是当前首个部署目标。`Authorization` 的 Basic 值必须是 `base64(instance ID:token)`，不能在 `Basic%20` 后直接拼原始 `glc_` token。Cloud Portal 的 stack 页面中，使用 OpenTelemetry 的 Configure 获取基础 endpoint 和认证变量；per-signal 地址应追加各自的 `/v1/traces`、`/v1/logs`、`/v1/metrics`，Python 的 Basic 空格使用 `%20`。[Grafana 官方说明](https://grafana.com/docs/grafana-cloud/send-data/otlp/send-data-otlp/)。账号准入、实际免费额度和查询读回必须在目标 stack 单独验收；配置示例不证明云端已通过。不要为本接入启用付费计划或依赖试用专属功能。

## 浏览器转发

浏览器不能使用上述私密 Grafana 写入凭据。client-web 的本地连接配置单独控制启用；需要服务端转发时，显式配置 relay 基础 URL，例如 `https://core.example/telemetry`，由客户端复用该连接的现有短效 Peer JWT。没有 relay 时，只能使用已准入、适合公开客户端的出口。relay URL 本身不启用遥测，也不改变业务的数据库直写或 Peer 路由。

core-py 的 `POST /telemetry/v1/{traces,logs,metrics}` 复用普通 Peer JWT 认证，仅向自身已成功启用的对应信号出口发送。调用方不能指定目标或转发认证头；服务端使用本地私密认证。它仅接受标准 OTLP/HTTP protobuf，直接使用标准 protobuf 请求与响应；JSON 返回 415。上游的 200 或 204 视为接收成功，204 的空响应映射为空 protobuf 成功响应；仍须独立查询验证持久化。client-web 使用官方 protobuf exporter，避免应用自行实现 OTLP JSON 的十六进制 Trace/Span ID 规则。不增加持久队列、后台重试或任意 URL 代理。

每个请求最多 256 KiB；每个进程最多四个转发请求同时进行，上游 HTTP 使用对应信号的 timeout；请求读取和发送的总预算为该 timeout 加两秒（最多三十二秒），不跟随重定向。不支持压缩请求。关闭或目的地不可用返回 503，满额返回 429，超大返回 413，格式错误返回 400，转发失败返回固定的 502，不回显上游错误体。转发会唤醒其宿主并消耗按请求资源，因此必须由部署显式选择；它不承诺遥测零额外运行费用。

## 首批采集与查询

| 边界 | 可观察内容 |
| --- | --- |
| `http.server` / `peer.http` | 路由模板、状态、耗时；Peer 目标及未执行、结果未知或已响应，不导出 URL query、headers 或 body |
| `job.submit` / `job.execute` | Job ID、受限提交 carrier、独立执行 Trace 与 Span Link；提交写入 span 只证明事务内 flush，`job.submitted` / `job.closed` 事件在本地拥有的事务提交后发出 |
| `cron.materialize` | 每次检查的 Cron ID 和当次实际创建的 Job，不复用最初创建 Cron 的请求上下文 |
| `ai.chat` / `ai.embed` | 共用 AI 执行边界；配置的模型标识、provider/dialect、耗时、真实 usage 和受控结束原因 |
| `agent.turn` / `agent.step` / `agent.tool` | Thread、turn、步骤、并发父子关系与工具结果；动态业务 ID 不进入指标维度 |
| Agent 检索、读取与结果 | 分开记录候选实体、实际读到的实体、Resolver 成功读取及最后选中的引用；只导出受控 ID 和计数 |

`inkcre.operation.count` 和 `inkcre.operation.duration` 记录操作范围的 `success`、`error`、`cancelled`，结果独立于是否开启 Trace。它们不是全库 Job 终态统计；过期收敛等未进入执行 scope 的路径不能从这个 counter 推算。请求 5xx、已捕获的 Job 失败/取消、工具错误结果在业务边界显式分类。耗时直方图按秒显式分桶，从 5ms 到 300s，覆盖 HTTP 短调用与较长 AI/Job 操作。指标只使用固定操作和结果等有界标签，不包含 Job、Trace、Thread、Peer 实例或动态模型 ID。

资源使用 `service.name`、`service.version`、`service.instance.id`、已知的 `inkcre.deployment.id` 与 `inkcre.peer.id`。查询单个任务用 `inkcre.job.id`，从执行 Trace 的 Link 查提交 Trace；同步 Peer 调用使用标准 W3C context。只有配置的 Peer 传输注入上下文，外部模型请求不注入内部 Trace Context。关闭的提交方写 NULL，关闭的执行方不创建 Trace，但领取和关闭保留已有 carrier。缺失、采样和过期导致的空缺不是业务未执行的证据。

生成的 Job carrier 各最多 512 UTF-8 bytes；SDK 注入的可选 tracestate 超限时整体省略并记录固定原因事件。SQL 容量约束拒绝直接超限输入。正式 migration `3d9593b0c855` 增加两列；nullable 不解除 exact-head 准入，部署需协调更新 schema、Python 与客户端，刷新 PostgREST schema cache。关闭遥测无需 downgrade 或删除任何 Job、PG 日志或 carrier。

## AI 数据边界

GenAI 映射固定到 `semantic-conventions-genai` 修订 `e07f4ebacb08f56db8c4c882d117720333fbca04`，由 AI owner 的 `telemetry.py` 维护。OpenAI-compatible 和 Alibaba adapter 在真实 SDK 回包处采集；Alibaba 的空 choices 尾块仍读取 usage，重复累计总量只记最后一次。input/output 缺失分别标记 `unavailable`，真实非负 int64（包括零）标记 `provider`。缓存和推理 token 不重复加到 input/output 总量。

`inkcre.ai.token.usage` 只累计已知值；缺失、负值、布尔与越界值不添加零或负样本，缺失另记 `inkcre.ai.usage.missing`。当前没有价格配置或成本估算，未返回的成本保持未知；Token 总和及采样 Trace 都不能冒充 provider 账单。

基础模式不导出 prompt、答案、工具输入输出、query、provider 配置、任意异常消息或 stack。配置中的模型标识受字符集与长度限制，provider 任意回显 ID/model 不复制；ToolCall ID 使用 SHA-256 摘要关联。最终引用最多导出前 128 项中的有效 ID，同时记录总数和未导出数量；不截断原业务结果。

首批来源事件分别是 `inkcre.retrieval.candidates`、`inkcre.entity.read` 和 `inkcre.agent.query.result`。最后一个事件描述选入 Job 内存 state 的结果，不提前声称最终数据库 close 已成功。当前点位覆盖 Agent 的 retrieve/get_entities/Resolver Tool 与 Agent Query Sink；直接非 Agent 检索、图遍历和 Resolver 内部传递读取尚无完整来源事件覆盖。关联不能证明模型确实依据该实体或答案正确，也不提供长期内容快照。原有 `agent_debug` 与 PG/Logtail 内容行为保持，不能将新出口的元数据策略泛称为整个部署没有原文副本。

## 故障、关闭与迁移后端

需要队列丢弃及导出观测值时，在进程环境设置 `OTEL_PYTHON_SDK_INTERNAL_METRICS_ENABLED=true`；Compose 默认值为 true，允许显式覆盖。原生启动用 `export` 或 dotenv 启动器注入，单由应用 Pydantic 读取 `.env` 不会改变 SDK 读取的进程环境。此变量不自动启用遥测。配置 metrics 出口后，原生 SDK 内部指标只保留组件类型、错误类型与 HTTP 状态；不导出 endpoint、组件随机名称。未配置 metrics 或显式关闭内部指标时只有本地固定 warning，没有 SDK 丢弃计数。SDK 队列并发检查可使计数与真正损失存在误差，指标本身也可能丢失；它们用于诊断，不是精确损失账本，缺少样本不能推断零丢弃。

Span 和 log 各使用 SDK 的 256 条有界队列、最多 256 条一批、五秒周期；metric 为三十秒 push，不增加 scrape 或唤醒归零实例的采集轮询。HTTP 导出 timeout 采用标准 `OTEL_EXPORTER_OTLP_TIMEOUT`，缺省十秒；按信号的 `OTEL_EXPORTER_OTLP_{TRACES,LOGS,METRICS}_TIMEOUT` 优先，允许有限正数且不超过三十秒。真实 Cloud 首次 TLS 往返超过一秒，固定一秒会误丢弃可用出口的数据；故障实验使用显式一秒配置。源端 SDK warning/导出失败只输出固定本地诊断，不转发 SDK 错误体或凭据。

正常关闭先完成业务资源和 PG writer，再停止接受新记录，并发关闭 trace/log SDK，最后关闭 metrics 以采集前两者的最终导出与丢弃计数。SDK 1.45 的 trace/log worker 等待窗口为三十秒，metrics shutdown 等待参数为对应信号 timeout 加两秒（缺省十二秒）；这些不是网络总时限或交付保证。不先执行一次会忽略 timeout 的 force_flush。平台提前杀进程、请求后冻结或断网时允许丢失尾部记录；使用该平台前需要验证实际终止宽限期，不能延长每个业务请求来掩盖此限制。

更换后端只调整标准出口和服务端认证，重新验证 ID、Links、AI unknown/zero 与聚合；Grafana 的查询、datasource、面板及诊断链接留在部署/消费侧。历史数据、查询和面板不承诺无成本迁移。故障回退是关闭本地遥测开关后重启，PG 无需恢复或迁移，业务 schema 与历史记录保持。

查询验收使用独立 Viewer service account，经 Grafana 的 datasource query/proxy API 读取 Tempo、Loki、Prometheus；`GRAFANA_URL` 与 `GRAFANA_SERVICE_ACCOUNT_TOKEN` 仅供部署工具使用，不进入应用采集。写入成功必须再核对存储后的 ID、Links、AI 来源/未知值与指标。若本机 Python 没有默认 CA 路径，在进程环境用标准 `OTEL_EXPORTER_OTLP_CERTIFICATE` 指向可信 CA 文件，不能关闭 TLS 校验。
