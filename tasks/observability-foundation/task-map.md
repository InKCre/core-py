# 工作边界与交付顺序

> 当前执行进度：G1 已收敛并授权实施，Hub draft PR #33 已发布，core/client 首批实现与本地 G2 已运行，正在云端合成读回与提交收尾。本文保留全父任务的工作地图；旧“未实施”状态由 [packet](packet.md) 与 [verification](verification.md) 的当前记录替代。


[packet.md](packet.md)是唯一 Human 入口。本文件拥有跨仓依赖和实施顺序；[整体设计](design.md)拥有架构，[共享契约形状](design/shared-contract.md)拥有字段/配置/兼容，[验收表](verification.md)拥有证据。各仓不复制第二个父任务包。

## 阶段和责任

| 阶段 | 状态与退出条件 |
| --- | --- |
| G1：契约与可行性 | 业务契约已收敛；D10 已确认 Grafana Cloud Free、显式 opt-in 与默认 PG；目标 SaaS 准入待验。既有传播、旧消费者/准入、carrier 和本地三信号证据保留；目标 SaaS 尚未验证 |
| G2：真实多 Peer 集成 | 待实现。契约按 Hub→Spoke 发布；Python/浏览器提交与执行、同步委派、Cron、模型/工具形成可查询因果关系；旧查询、出口内容边界和业务故障隔离通过 V1—V6 |
| G3：覆盖与运行交付 | 待实现。活跃 Unit 逐项完成，实际用量/配额/保留/导出/恢复边界、运维入口和回退通过 V7—V9；V10 依确认后的长期证据承诺验收 |

四条工作线持续存在：C 拥有共享契约与兼容；I 拥有托管接入和运行；P 拥有各 Peer 采集/PG 日志兼容；A 拥有 AI 调用与业务结果证据。主 Agent 负责全局集成和 Human 沟通，独立工作只有在明确低耦合收益时委派。G1 两个单元的返回见 [C-G1](cells/contracts-foundation.md)、[I-G1](cells/infra-foundation.md)，随父任务保留，不因子单元完成而清理。

## 可执行的实施顺序

### 1. 发布共享契约和机械协议

变更对象是 Hub 的四文件 patch：无统一观测语义 → 公共身份/传播/Job carrier/内容边界。影响所有参与 Peer，不改变业务 authority。先审查并在 Hub 源交付，经明确指令提交/推送后，各 Spoke 分别更新共享引用；Hub 修改、引用 bump 和本地实现不得混为一个提交。当前 patch 仍只在任务内，尚未应用。

core-py 数据库协议 owner 随后交付两列、容量约束、config schema 注册、数据库初始化步骤与生成协议投影；client-web 同步消费生成类型。实际 migration 在 disposable DB 验证旧记录/旧消费者、约束和 exact-head。新增遥测默认关闭且不读取其共享配置；未配置或关闭不影响 PG 日志和应用启动。新 Job 字段依赖对应 schema admission，不靠写失败重试。正式发布采用共享契约已描述的协调升级，不能把 nullable 推导为无停机滚动兼容。

### 2. 验证并交付 SaaS 接入

先用一个 Grafana Cloud Free 目标账户确认非试用/无付费依赖，再验证三信号、Job 因果查询、AI unknown/zero/partial 的写入/查询/导出、实际诊断入口和预算控制；不上传真实内容。只有必要条件失败才重看其它免费候选，不同时建设多家生产出口；OpenObserve Cloud 暂缓。当前没有云端账户运行证据；不采购、不自动升级、不向第三方发送真实内容。

core-py 的 `docs/40-deployment/observability.md` 拟拥有启用、身份、权限、费用/限额、保留、导出与切换步骤；各 Peer 交付默认 false 的本地开关、标准 SDK 和按信号出口配置；endpoint/凭据不得自动启用。没有默认的 `deploy/observability/` 五组件交付项。部署 owner 管理供应商项目，各运行平台保管本地私密凭据。

验证进程直接 OTLP、短生命周期 flush 上限和计费影响；指标用 push，不用 scrape 唤醒归零实例。浏览器只使用经验证的客户端写入能力，否则通过受控按请求转发；查明 CORS、权限、限流和失效行为。仅在供应商或现有平台不能承担必要机制时引入 Collector，并记录具体缺口与运行成本。

接入失败不阻止应用 ready，不重试业务事务。费用以实际写入、查询、保留和应用出口计量；用量上限对应告警、限流还是丢弃必须实测，不承诺所有供应商都有硬费用上限。完成必要准入即进入真实业务切片，不把无限产品比较当交付。

### 3. 先验证默认行为，再完成显式开启的跨 Peer 切片

Python 的 `libs/obsrv` 保留现有 logging_backend 与 PG 生命周期，新增独立本地 telemetry_enabled；Compose 未配置 fallback 从 none 对齐 PostgreSQL，但保留显式覆盖。先验默认关闭及“已有 endpoint/凭据仍关闭”时没有新增 OTLP/provider/队列而 PG/Job UI 正常，再验开启后的标准 SDK 初始化与有界关闭、Resource、专用结构化日志来源。middleware/Peer 调用负责受控 HTTP context；Job/Cron 的共用创建入口写 carrier、领取后的执行 scope 建 Link。client-web 共用 core 包负责 JobManager、Peer HTTP 和 DBAPIClient，Web 页面负责诊断入口。

明确为参与测试的 Peer 开启新遥测，以“浏览器 Peer A 提交 Job → Python Peer B 执行 Agent → 能力调用 Peer C → 模型和并行工具 → 结果与引用”为首条旅程；反向增加 Python 提交、浏览器实际执行。覆盖开→关、关→开、关→关、开启后再关闭，以及发起方重启、NULL/损坏 carrier、Cron、并发隔离、取消、失败、结果未知及关闭。标准事件至少区分提交、成功 claim/开始、终态、能力未执行/已执行/结果未知；只在业务已确认这些事实的边界发出，不能从日志顺序推断状态。

AI adapters 在 provider 回包位置采集使用量，覆盖流式 usage-only 末块、embedding、无 usage 和真零；Agent/Tool/检索只记录固定事件和受控 ID。先用受控回包比较，再在授权 preview 用实际 provider 验证外部行为。价格估算由版本化价格/币种配置负责，未知价格不记零；不用 tracing 代替账单。

同一业务负载断开 SDK→SaaS，以及实际存在的转发/Collector→SaaS，比较原有 API/数据库终态、内存/队列、关闭时限和丢弃计数；遥测失败不能让 Job 创建重试或业务 ready 失败。内容 canary 从请求、异常、SDK warning、SQL 参数和工具结果进入，检查 Peer 第一次发送的 OTLP，不能只检查后端清洗结果。

### 4. 保留 PostgreSQL 日志，添加可选诊断入口

Job 页当前及历史 `job.<id>` 查询、分页与排序继续使用 PG 路径，不迁移或替换其 trace_id/span_id。新后端链接只作附加入口，未开启、无可用 Trace 或已经过保留期时 PG 日志仍可查询。关闭新增遥测不需要回切 PG，不删除历史，不回填此前未采集的 Trace。

新增 OTLP logger 不自动桥接 PG 历史、任意应用日志或 agent_debug 内容；现有 PG/Logtail 的内容行为与配置保持。撤销旧 writer 退役计划；未来是否停写或删除日志属于另一个明确授权的变更。exact-head 仍使旧二进制不能直接配新 schema，关闭遥测不等于数据库 downgrade。

后端可替换验收只改标准出口及认证配置，把同一采集样本交给另一兼容接收端，核对必要 ID/Links/unknown 与聚合；业务采集和持久字段不改。Grafana 查询、datasource、面板和深链接在部署/消费侧维护，不引入通用插件框架，也不声称消费侧零迁移成本。

### 5. 扩面与运行验收

按下表确认活跃部署，补齐采集和查询；没有活跃运行证据的 Unit 保持“待部署盘点”，不能自动宣布不适用。G3 记录每天摄取/查询量、指标序列数、保留、实际费用、峰值和查询 P95；验证供应商配额、删除、导出与配置重建，明确托管服务能提供的恢复范围。独立管线探活不能唤醒归零业务实例；通知目的地由部署 owner 配置，任务不自动给外部联系人发消息。若以后选择自建，再加入磁盘/冷备恢复与启动资源验收。

| Unit / 入口 | 接入责任和范围 | 当前证据与验收 |
| --- | --- | --- |
| core-py / 进程内 extensions | 共用 Python SDK 出口，HTTP、Peer、Job、Cron；Source/Sink/Organization/Resolver/Storage 在业务边界补语义 | 源码已定位；G2 首批实际运行 |
| client-web 共用 core + Web app | Peer/Job/DBAPIClient、浏览器 context、Job UI | 实际 TS/PostgREST 旧消费者仅在 Node 验证；浏览器仍须验收 |
| 独立 client-webext | [root.ts](../../../client-webext/logic/root.ts)、[block.ts](../../../client-webext/logic/block.ts) 的旧直连 HTTP 路径单独接入 | 没有证据它消费当前共用 core；不能称 Web 接入自动覆盖它，也不借本任务迁移其业务协议 |
| client-ios | [APIClient](../../../client-ios/InKCre/APIClient.swift)、[NetworkService](../../../client-ios/InKCre/NetworkService.swift) 的 URLSession 边界 | 活跃发布和现行协议待盘点；采用环境适配的标准传播/导出，不先强加 Job 执行身份 |
| rokid-studio-client | 相机/OkHttp 上传边界，默认只采元数据 | 旧业务 endpoint/OSS 路径的原生应用；活跃部署待盘点，不采图像或签名地址 |
| PostgreSQL / PostgREST / 主机 | 部署 owner 使用已有免费指标/日志出口；有内容的数据库日志单独启用 | 客户端 span 不算 DB server span；不改变 SVC 数据库生命周期 |
| 官方 ext-reg | Worker 与 D1/R2 的现有边界，由该服务运营 owner 采集 | 单独部署/数据归属；选 Worker 兼容标准出口或平台原生采集，不盲装 Node SDK；现成 OTLP 导出仅 logs/traces，metrics 缺口单独验收，不把各用户部署合并为一个 owner |

本顺序没有删除原始“整个 InKCre”范围。AI 先按诊断与来源关联设计；若 Sir 要求所有历史答案/图谱变更都可复核当时内容，V10 必须加入业务结果 owner 的持久快照实现，不以关闭内容开关宣布该要求完成。

## 关闭条件与授权

当前已完成业务契约与 SaaS 方向修订，目标云端准入尚待验证；源码实现、提交/推送和正式部署未执行。实现授权后，应持续完成 G2/G3 所需代码、测试与文档，不能再以方案代替交付。各仓检查按其本地治理执行；协议/数据库与外部行为分别使用 disposable runtime 和授权 preview。

父任务最终关闭需真实验收、持久文档归位、跨仓引用与回退关系明确，实验资源与历史数据的保留/删除有依据。既有 G1 子项完成与本次方向修订均不关闭父任务，任务包和合成数据卷继续保留。
