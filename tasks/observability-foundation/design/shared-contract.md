# 跨 Peer 观测契约与持久形状

状态：2026-10-03 契约候选已按显式 opt-in、PG 保留与 SaaS 方向修订，尚未发布。本文细化[整体设计](../design.md)的跨语言实现输入；[Hub patch](hub-contract.patch)承载公共语义，数据库 schema、语言投影和迁移由 core-py 数据库协议 owner 交付。实验结果见[数据库与三信号报告](../experiments/convergence-20261003.md)。

## 显式启用与现有日志

新增遥测通过每个 Peer 本地的 `telemetry_enabled` 开关控制，缺省 false。Python 拟映射为 `obsrv.telemetry_enabled` / `OBSRV__TELEMETRY_ENABLED`；浏览器在现有部署连接配置中提供同义布尔值，原生 Peer 使用其运行配置。该开关不是既有 `logging_backend` 或 `ENABLE_LOG_BACKEND`，不进入共享部署配置，不添加第二个部署级总开关。仅存在 endpoint、token、diagnostics_url 或安装 SDK 不能启用。

| 有效状态 | 新增遥测 | 已有日志与业务 |
| --- | --- | --- |
| 未配置或 false | 不初始化新增 SDK/provider/instrumentation/exporter，不发 OTLP，不新增传播与 carrier 捕获 | 保持 stdout 与原 logging_backend，默认 PostgreSQL；现有 Job 查询可用 |
| true，出口有效 | 按已配置的信号初始化标准 SDK/OTLP；没有配置的信号不导出 | PG writer 不替换、不停写；业务不依赖后端可用 |
| true，配置不足或出口初始化失败 | 报告明确且不含凭据的本地配置问题，不启用受影响信号 | 业务正常启动，PG 路径保持；不靠记录业务重试来恢复遥测 |
| 由 true 改为 false | 下一次进程启动/浏览器连接重新初始化后停止新采集；前一运行期正常关闭仍可有界排空 | 不删除 PG 历史或 Job carrier，不需要恢复/重建 PG writer |

第一版不承诺热切换。关闭态不为新增遥测额外查询共享配置或要求创建部署标识，也不增加队列、轮询和 SDK 关闭等待。显式设置已有 logging_backend 为 none/logtail 等仍按原配置执行；代码和 .env 模板已默认 PG，Compose 未配置 fallback 为 none 的不一致列入实现对齐。

## 身份和配置

部署、Peer、运行实例和业务操作各有身份。部署标识使用一次分配的 UUID；Peer 复用已注册 UUID；`service.instance.id` 每次进程或浏览器运行期生成。Job/Thread/ToolCall/实体 ID 保留原类型和意义，Trace/Span ID 由 SDK 生成。启动期身份不全可省略，不生成假 Peer，也不阻挡业务就绪。

复用现有 `configs`，选择 key `inkcre.observability`、schema `inkcre.observability.v1`，value 包含必需的 `deployment_id` UUID，以及可选的 `otlp_http_endpoints` 和 `diagnostics_url`。前者是对象，按需包含 traces、logs、metrics 三个完整 OTLP/HTTP 出口 URL，本地开关开启后，缺省的信号仍不启用远端导出；不自动拼接固定后缀。后者为诊断入口基础地址，不保存供应商查询模板。所有 URL 均无凭据，不允许 userinfo 或带 token 的 query。进程端映射标准 per-signal exporter 配置；显式本地运行配置优先于共享默认值，浏览器读取同一投影与其连接设置。配置 schema 在现有 DeploymentConfigManager 注册，由各语言读取对应投影，不增加配置服务。

部署安装/启用步骤在已有配置缺失时一次创建身份；并发初始化以数据库唯一 key 和 insert-on-conflict 保留已存在值，不能用 replace 重置 ID。开启的 Peer 只读取；本机启动期间配置不可用则保留本地诊断、暂不远端导出，配置恢复后在本地开关仍开启的前提下重新初始化接入。Exporter 必须先满足本地 telemetry_enabled=true，再检查有效 endpoint 与出口配置；任何共享配置都不能覆盖本地 false，不影响 readyz。服务端私密 OTLP ingest token 属于运行配置，不进入客户端；供应商专为公开客户端提供的受限写入能力需单独准入，否则使用受控按请求转发。凭据不进入该非秘密 value 或诊断跳转 URL。

部署 owner 保证各出口使用同一 deployment ID；若存在 Collector/转发入口，其受控配置使用相同归属，不信任客户端自报属性作为权限。重启/原地恢复保留 ID；克隆、preview 和新 owner 的部署在启用出口前显式换 ID。首版不声称能自动识别数据库克隆。

## 同步传播

开启的 Peer 采用标准 OTel W3C propagator 注入/提取 `traceparent`、`tracestate`，不复制 parser。同步 Peer 请求在实际调用边界注入当前 SDK context；auto/manual 只保留一个注入 owner。调用端的选择和远端执行分别记录，继续遵守原有 not-executed 与结果未知不能泛化重放的规则。

缺失、语义无效、未采样的 carrier 不改变认证与业务响应。传播 allowlist 来自已经配置的部署 Peer endpoint；外部 provider/source 默认只有本地 client span，不外传内部 context 或 baggage。浏览器的 CORS 允许项不能代替认证，PostgREST client span 不能冒充 server/SQL span。

## Job 的公共形状

| 字段 | 类型和边界 | 写入与读取责任 |
| --- | --- | --- |
| `submission_traceparent` | nullable text，缺省 NULL，UTF-8 最多 512 bytes | 创建方保存 SDK 注入的值；当前采用 SDK 注入 55 bytes 的 version 00 |
| `submission_tracestate` | nullable text，缺省 NULL，UTF-8 最多 512 bytes | 可选 vendor state；capture 时超限省略整个字段，保留有效 traceparent |

512 bytes 是应用持久化政策，不是 W3C tracestate 的全局最大值。SDK 实测可产生 1109 bytes；省略 optional state 的决定必须发生在业务写事务之前，记录固定原因的丢弃计数，不输出原始值，也不为遥测增加写失败重放。SQL 只验证普通类型/容量，不校验 W3C 语法。直接数据库调用传入超限字段仍按普通协议错误拒绝，不能借容错接受无限输入。

开启的创建方在创建 Job 的同一事务内保存 carrier；Python REST 从当前 SDK context 捕获，不在旧 JobCreateForm 中添加字段。Python 的共用 create_in_uow、Cron materialize/run_now、TS JobManager 的 PostgREST 创建都落在此语义。Cron 每次真正创建 Job 时捕获该次发生的 context，不能永久继承最初创建 Cron 的请求。

开启的执行器成功 claim 后建立独立 trace，以标准 Span Link 连接有效提交 span，记录 Job ID；新执行 context 不能覆盖 submission 列。旧 Job 的 NULL 和有界语义损坏只失去 Link，不阻止执行。读取语义用 SDK；SDK malformed tracestate WARNING 只留在本地诊断，不桥接到基础远端 logger。查找路径始终允许 Job ID，不要求提交 Trace 尚在保留期内。

关闭的创建方不捕获新增 carrier，两个字段按缺省 NULL 写入；关闭的执行方不创建 span，但 claim/close 必须保留行中已有 carrier。开→关、关→开与关→关组合都保持现有 Job 结果语义；开→关可能只有提交 Trace，关→开可能只有独立执行 Trace，不能伪造完整链路。这里描述同一获准 schema 上的配置混用，不授予旧二进制跨 migration head 混跑能力。

## 兼容、准入与升级

| 组合 | 已观察行为 | 交付约束 |
| --- | --- | --- |
| 旧生产者 → 新 nullable 列 | 实际 Python repository 与 TS/PostgREST 创建默认 NULL | 仅在 runtime 已获协议准入时可运行 |
| 新 carrier 行 → 旧模型/执行方法 | 旧 Python/TS 模型忽略新列；实际 claim/close 保留两列 | 不由该证据推导旧进程在新 migration head 获准运行 |
| 有界语义损坏 / 容量超限 | 前者可存，后者被实际数据库约束拒绝；SDK 解析实验已完成 | 新执行器的真实业务回归在 G2 验收 |
| 新 migration head → 旧 readiness | 实际检查对模拟新 head 拒绝 | 不改变 exact-head，不承诺滚动混跑 |
| 新生产者 → 旧 schema | 无受支持写入路径 | 遵循 admission；不捕获失败后删字段重试 Job |

首版按协调升级交付：先发布 Hub 契约与 Spoke 引用，再发布 schema/生成协议/Python/TS 匹配版本；部署时暂停新提交、停用领取并排空或按既有机制取消执行，备份后迁移、刷新 PostgREST schema cache、更新所有参与的运行版本、检查 readiness 再恢复。旧浏览器页/离线客户端重连需刷新到匹配版本。任务不增设零停机框架；若有此要求，重新决策发布模型。

将本地遥测开关改为 false 并重启进程或重新初始化客户端连接，是观测故障的首选回退，不涉及 schema 回退。旧二进制因 exact-head 不可直接替换新版本；数据库 downgrade 只允许在维护窗口排空、备份并验证的独立操作，不能为回退可选遥测删除业务 Job。正式 migration、完整启动和协调升级演练仍是 G2 验收，不把实验 DDL 当发布物。

## PostgreSQL 日志保留与 AI 关联

`job.<id>` 及现有 PG `trace_id`/`span_id` 保持原语义，不改作标准 OTel ID。Job 页的当前与历史日志始终从既有路径读取；已配置的新诊断入口是附加能力，新遥测事件带独立 Job/trace/span 属性。不以新查询验收通过作为停用 PG writer、删除表或搬迁历史数据的条件，本任务不再安排旧 writer 退役。

新增 OTLP 只接专门的结构化事件 logger，不桥接 PG 历史、任意应用日志或 agent_debug 原文。现有 PG/Logtail 内容行为继续由原配置控制，不要求为了保持当前行为开启新的内容模式；“原文默认关闭”只描述新增 OTLP 出口，不能泛指整个部署。

AI 的 metadata、usage unknown、结果 authority 和内容边界遵循整体设计。`AgentQueryResult.answer/references` 及现有结果保存仍由业务 owner 负责；基础阶段从 Job/实体 ID 关联诊断，不能将 Trace 留存冒充答案或图谱的历史快照。未来有长期快照承诺时，先扩展相应结果/引用契约，再启用内容存储。

## 变更和验证边界

本提案从“无标准提交上下文/统一部署关联”变为上述两个 nullable 字段与一个共享配置。影响数据库协议、生成 TS 类型、各语言采集初始化和 Job 查询入口；不改变 Job claim、取消、终态、重试、业务 authority 或认证模型。确切规范键必须随 Hub 合同一并评审，SQL、SDK wiring、后端版本和运行参数分别归实现/部署文档。

标准 SDK、实际旧数据库消费者、容量边界与合成三信号已提供 G1 支撑。V0—V6 的默认行为、真实跨 Peer、浏览器、错误路径和出口验证仍需执行；Tempo 后端历史 Link flags 损失不能放宽实时传播/持久 carrier，也不能从历史默认值推断原始采样状态。
