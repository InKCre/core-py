# 任务决定与重开条件

现行 Grafana Cloud Free 选型、vendor-agnostic 与默认关闭/PG 保留由 D10 拥有；零费用及 Cloudflare 范围由 D9 保留。D8 的 SaaS/SDK 直发方向保留，OpenObserve Cloud 优先顺序被 D9 替代。D1/D4/D6/D7 中的默认常驻 Collector、自建配方及最终后端收敛结论已被 D8 替代，保留它们作为历史决策。这里记录任务级选择及其重开条件；尚未成为 Hub 契约或运行行为的提案，不能因写入本文件而视为已经交付。

## D1：统一采集协议，保留后端替换能力

- **状态与权威**：Sir 于 2026-10-01 认可架构草案、方向与技术选择，允许继续推进。
- **选择**：以 OpenTelemetry/OTLP 为采集与传输基础，部署自有 Collector 汇聚；OpenObserve 单机作为首个验证后端，业务采集点不依赖其专有 SDK。
- **原因**：同时覆盖多 Peer 的日志、指标和 Trace，并把更换存储/查询产品的成本限制在消费侧。
- **后果**：必须验证数据导出、字段保留、Span Links 和必要查询；不能把“支持 OTLP”当作完整可迁移性证明。已有合成摄取、查询和中断证据；生产适用性仍未确认。2026-10-01 的 AI 缺失值实验触发后端重开，见 D4。
- **重开条件**：实际资源超预算、关键查询或导出能力缺失，或者发现已有更合适的运行平台。先调整后端，不轻易改变采集协议。

## D2：长期正确通过边界与证据体现

- **状态与权威**：Sir 于 2026-10-01 明确要求长期正确；以下是主 Agent 对已认可架构的工程落实。
- **选择**：保留 Peer 平等、数据库业务 authority 和现有 Job 语义；诊断遥测与业务结果证据各有保存责任。迁移必须覆盖旧消费者，并以独立查询、故障注入和实际业务结果验收。
- **原因**：短期 Trace 的采样、过期及丢失不能决定业务状态或长期证据是否存在；只替换日志后端也无法证明跨 Peer 关联正确。
- **后果**：先做贯穿 Python、浏览器、异步 Job 与 AI 的集成切片，再扩面；不通过跳过兼容、数据边界或恢复验证来缩小任务。
- **重开条件**：产品明确改变 Peer/owner 模型，或要求无损审计、不可篡改证据、执行恢复等新的承诺。该变化需单独决策，不能借“长期正确”自行推导。

## D3：当前可推进的范围与未授予的含义

- **状态与权威**：Sir 已要求扩展任务包并继续推进；主 Agent 据此继续契约设计、只读调查与隔离合成实验。
- **选择**：同一部署内汇聚作为现行产品模型下的工作基线，基础元数据与原始内容分开控制。没有明确内容范围前，实验使用合成数据。
- **原因**：当前一个部署只有一个 owner，尚无产品租户模型；原文保存会改变数据副本、读者和删除责任。
- **后果**：预算和内容问题只阻挡依赖它们的生产选型或内容启用，不阻挡任务包、协议设计和合成实验。2 vCPU/4 GiB、保留天数、永久证据强度都未成为正式要求。
- **重开条件**：Sir 指定跨部署集中运营、原文/长期证据范围、部署环境或资源上限。

架构认可不等于 Git 提交、推送、生产发布或现有私人内容导出的授权。实际授权在执行对应动作前按会话与仓库规则判断。

## D4：否决当前 OpenObserve，选定分立后端

- **状态与权威**：2026-10-03，主 Agent 根据可重复实验及 advisor 复核作出的候选判断，属于 D1 已约定的条件验证；并非 Sir 已批准新的生产后端。
- **选择**：OpenObserve 1.0.4 不作为当前统一后端；沿 Grafana/Tempo、Loki、Prometheus 方向验证。随后五组件合成三信号与 Grafana UI 闭环通过，选择该组合进入实现；尚未认可生产容量或正式部署。
- **原因**：OpenObserve 在摄取时把缺失 usage/cost 补零，使 unknown 与真实零不可区分；不能靠查询还原。Tempo 重启后保留了样本的字段存在性、类型和值及 Link ID/tracestate/属性。
- **后果**：不增加影子字段、供应商修复层或自研存储；不同时扩大产品比较。Tempo 历史 Link flags 丢失是保留的已知限制，完整 OTLP 保真未通过。SDK、Collector 和 Job carrier 继续使用完整标准传播；查询缺失的 flags 不代表原始未采样，不能用于恢复传播、重采样或推断完整性。
- **重开条件**：后续消费者需要历史 flags，日志/指标的字段映射破坏当前语义，全栈资源或操作成本不合预算，或者新版本改变以上行为。需要时只重验受影响能力。

[实验记录](experiments/README.md)拥有版本、输入、查询、资源和原始证据。当前协议出口与三信号/查询 UI 闭环已有证据；历史数据迁移、真实业务与生产运行仍未完成。


## D5：固定公共形状，采用协调升级

- **状态与权威**：2026-10-03，主 Agent 根据真实 disposable PG/PostgREST 与 SDK 容量实验定稿，advisor 复核未发现阻挡实现的设计问题。
- **选择**：两列 nullable carrier、各 512 bytes；SDK 超限 optional state 在写入前整体省略。部署标识复用一个现有 configs 记录，由部署启用步骤一次初始化；具体字段与 config key/schema 在[共享契约](design/shared-contract.md)。
- **原因**：旧 Python/TS 实际创建与 claim/close 保持兼容，但旧 exact-head readiness 确实拒绝新 head；SDK 也不会自动把 tracestate 限为 512 bytes。
- **后果**：协调升级、匹配 runtime/schema、旧客户端刷新，不增加静默删字段重试或滚动兼容框架。不得把实验 DDL 当正式 migration。
- **重开条件**：必须零停机混跑、增加新的持久传播成员或既有 config authority 发生改变。

## D6：独立配方和有限采集来源

- **状态与权威**：主 Agent 在既有交付物盘点、五组件闭环及内容边界复核后的工程选择；用户未要求创建新的平台仓库。
- **选择**：core-py 分发可独立运行的 Compose 配方，部署 owner 运行。基础远端采集只接明确来源和字段，专用结构化事件 logger、受控 span；自动 instrumentation 按最终记录准入，不默认桥接任意日志。
- **原因**：已有仓库负责自托管 Compose；新仓/控制服务没有现成收益。任意异常/SQL/SDK 日志包含原文的可能性不能靠只删 headers 或通用正则证明消除。
- **后果**：可信 owner 用 Grafana Editor/Explore；Viewer 不承诺交互诊断。原始 PG writer 属于内容模式。首版依旧使用标准 SDK/认证/队列能力，不自建 OTel 数据重写框架。
- **重开条件**：独立 infra 产品出现、必须给只读角色完整 Explore 能力、跨 owner 运营、或准入自动 instrumentation 无法满足最终记录边界。

## D7：关闭设计阶段，保留实施验收

- **状态与权威**：Sir 要求“直到方案完全收敛”；2026-10-03 G1 判别完成，独立 advisor 建议结束选型实验。
- **选择**：方案按单 deployment、2 CPU/4 GiB 合成试点、AI 诊断/来源关联与原文默认关闭进入实现准备。以上是设计假设；实际预算和历史快照承诺未由 Sir 确认。
- **后果**：不再无限扩展候选比较。G2 验真实 Peer/浏览器/AI/故障/出口，G3 验活跃覆盖/容量/运维，V10 根据内容承诺验收；整个基建父任务仍活跃。
- **重开条件**：实际范围或预算否定假设，或者实现判别否定关键机制。不能把未执行验收改称已完成。

## D8：按 serverless 与 scale-to-0 修订为 SaaS 优先

- **状态与权威**：2026-10-03，Sir 明确否定自建五组件的常驻成本，偏好轻量 OpenObserve，并建议利用 PostHog 等 SaaS。该输入重开 D7 的预算假设，替代 D1/D4/D6 的默认自建结论。独立 advisor 已就新约束、最低必要语义和短生命周期进行复核。
- **选择**：默认标准 SDK 直发 SaaS，不要求常驻 Collector。首先验证 OpenObserve Cloud，Grafana Cloud Free 为明确备选；PostHog 有原生三信号与 AI 分析，但 tracing Beta、metrics Alpha 和关联限制使其暂不成为唯一基建首选。候选顺序是工程推荐，不代表用户已经开通或批准采购。
- **原因**：运维、闲置固定费和应用生命周期比单次内存快照更能衡量轻量。OTLP 与业务身份提供替换能力，不要求自建数据平面。当前必要字段可消费即可，不要求后端逐位保真。
- **缺失值决定**：`-1` 可以是消费端受控的 unknown 编码，不能当实际 token/cost 聚合。源端标准字段缺失省略；对于会补值的后端，允许最少的逐字段来源元数据并配套查询，撤销“任何额外标记都是影子真相”的过度约束。不为此自研存储或通用修复框架。部分未知的完整 total 仍未知，费用仅统计已知部分并展示缺失数。
- **配置影响**：尚未发布的 v1 配置从单一 `otlp_http_endpoint` 改为可选 `otlp_http_endpoints`，按 traces/logs/metrics 保存无凭据的完整 URL，映射标准 per-signal exporter 配置。供应商不同路由不构成必须上 Collector 的理由；凭据仍在运行/连接配置中。
- **验收与停止比较**：用一个目标账户验证三信号、Job 因果、AI unknown/zero/partial、浏览器入口、导出和用量边界。通过必要诊断能力即进入 G2，失败才转备选；不因为当前不用的字段或缺少专用 AI UI 无限扩大选型。
- **保留与重开**：D2/D3/D5 的业务 authority、内容范围、Job carrier 和协调升级保持；原自建实验仍是历史证据。只有不可接受的真实费用、必要语义/查询缺口、入口边界或生命周期开销才重开。目标 Cloud 行为、实际负载/预算与长期证据承诺没有被假定为已验证。

## D9：新增观测服务费用为零，先验 Grafana Cloud Free

- **状态与权威**：2026-10-03，Sir 询问 Cloudflare 服务，并明确暂时无法使用收费服务。该约束立即替代 D8 的 OpenObserve Cloud 首验顺序；不把14天试用或低单价当免费。
- **选择**：首先验证 Grafana Cloud 的实际 Free 计划，用标准 OTLP 接受多 Peer 三信号；无需自建底层 Tempo/Loki/Prometheus，也无需默认 Collector。Cloudflare 原生观测覆盖在其平台运行的 Unit，按内容/关联准入后可导出到同一后端；AI Gateway 只在模型代理需求成立时单独评估。OpenObserve Cloud 暂缓，PostHog Free 保留能力资料，当前不并行建设第二套系统。
- **原因**：免费完整 SaaS 比拼接 Workers、D1/R2、Analytics Engine 成为自研观测平台更符合低维护目标。Cloudflare 公开文档尚不足以证明通用外部 OTLP 三信号存储入口；Analytics Engine 的采样也不能保证单条诊断记录可找回。
- **费用与生命周期**：不采购、不升级 Pro、不启用付费附加项、不以试用能力作为验收基线；预算耗尽时遥测可拒收/丢失，业务照常。应用发送、转发与平台采集均受额度约束，不为观测新增常驻实例。已有业务/模型推理成本不因观测免费消失。
- **最小准入**：目标账号确认 Free 及三信号限额，合成样本读回 Job/Trace/Link 与 AI unknown/zero/partial，确认消费 UI、样本导出、浏览器凭据边界和有界 flush。指标按类型/基数验，Cloudflare 自带导出不支持 metrics 的缺口逐 Unit 如实列出。
- **时间与残余**：Cloudflare 12月1日新定价尚未生效；AI Gateway 新旧客户以9月24日区分，见[官方研究](experiments/sentinel-saas-20261003.md)。当前只做只读研究和任务包修订，目标账号实验仍未执行。
- **重开条件**：实际必要语义/接入不能满足，免费额度不足以支持有用诊断，或 Sir 改变费用/保留要求。先降低可选遥测量并准确呈现缺口，不能擅自付费或放宽业务/证据契约。

## D10：用户选定 Grafana Cloud Free，显式 opt-in，默认保留 PG 日志

- **状态与权威**：2026-10-03，Sir 明确同意 Grafana Cloud Free，强调 vendor-agnostic、新可观测性按需开启，默认维持现有 PostgreSQL 日志。后端从工程推荐转为用户已选，实际 Cloud 验收仍待执行。独立 advisor 支持单一本地开关、关闭态不参与新增遥测与 mixed Peer 契约。
- **默认行为**：新遥测关闭，现有 stdout、logging_backend、PG writer 的级别/上下文门控/队列/关闭顺序和 Job 日志页面保持。启用 OTLP 也不自动停 PG；撤销先前“新查询通过后退役旧 writer”和“保留 PG 需另启 legacy 内容模式”的计划。现有显式 logging_backend 覆盖继续有效。
- **配置选择**：每个 Peer 使用本地 telemetry_enabled，缺省 false；Python 拟用 OBSRV__TELEMETRY_ENABLED，浏览器用连接本地布尔配置。共享 configs 只给身份/目的地，不提供总开关，endpoint/token 不等于开启。重启/连接重新初始化生效，首版不做热切换。
- **关闭语义**：不初始化新增 SDK/provider/队列/instrumentation，不新增传播或 carrier 捕获；新建 Job carrier 默认 NULL，已有 carrier 经 claim/close 保留。开启端可以执行 NULL carrier Job，关闭端可以执行有 carrier Job；链路缺口允许，业务与准入规则不变。关闭不清理历史，不回填或补发此前未采集记录。
- **vendor-agnostic**：标准 SDK/OTLP、标准 ID 与公共语义进入业务采集；供应商 endpoint/认证/查询/面板在部署或消费侧。更换后端不改业务采集代码、Job carrier 或 schema。查询和历史迁移仍有成本，不为消除全部差异增加通用插件/转换框架。
- **已观察差异**：libs/obsrv/setting.py 和 .env.example 默认 PG；docker-compose.yml 未配置时使用 none。实现时将 Compose fallback 对齐用户要求，保留显式 none/logtail 等配置；当前尚未修改它，不能宣称所有启动方式都已默认 PG。
- **必要验收**：默认关闭、端点/凭据存在但未开启、显式开启、出口故障、再次关闭的 PG/UI/OTLP 行为；开关组合的跨 Peer Job 与字段保留；仅改出口配置即可替换后端。新出口的内容策略不倒推覆盖旧 PG 日志内容，不能声称整个部署默认无原文。
- **边界**：本轮修订任务包及未应用 Hub patch，应用实现、目标账户与正式发布仍未执行；继续零新增观测服务费，不启动收费功能。


## D11：授权实施与首批交付

2026-10-03，Sir 明确授权实施，并允许创建分支、提交、推送和 draft PR（包括 client-web）；随后创建 Grafana stack 并提供本地写入与 Viewer 配置。Hub 源已先提交推送，两 Spoke 的引用各自单独提交，应用实现按该共享契约进行。授权不扩展为合并、生产发布或付费服务。

首批采用标准 OTLP/HTTP protobuf。真实 browser relay 读回发现通用 ProtoJSON 会把 OTLP hex Trace/Span ID 按 base64 解码；HTTP 200 不能证明正确。改为客户端官方 protobuf exporter 与服务端 protobuf-only，避免应用自研协议解码器。JSON 返回 415，最终验收比较 ID、Link 与事件上下文原值。

SDK 原生内部指标通过 `OTEL_PYTHON_SDK_INTERNAL_METRICS_ENABLED=true` 的进程环境启用；Compose 默认 true 且允许覆盖，原生启动显式注入。它不绕过遥测总开关，View 限定内部指标维度，并禁止过滤后 exemplar 携带被移除的属性。缺少 metrics 出口或关闭此开关时没有原生丢弃计数；计数自身丢失也不能推断零丢弃。避免自定义队列或私有 SDK 工厂。

独立 advisor 认为这些选择不阻挡首批 draft；候选数据库类型、真实平台关闭行为及部署覆盖仍需各自准入。原任务包状态随实际实现更新，不以 draft 或本地测试替代生产通过。

真实 Cloud 验收进一步否定固定一秒网络超时：原生 TLS 首次往返超过一秒。使用标准公共/per-signal timeout（默认十秒、最多三十秒），relay 总预算为该信号 timeout 加两秒。Grafana Logs 返回204，转发识别200/204并以标准空protobuf返回；实际API读回确认已存储。SDK原生队列计数有并发误差，只作诊断，不当精确损失或费用账本。
