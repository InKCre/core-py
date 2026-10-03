# 现状证据与待解问题

本文件拥有调查结论与未决问题。[design.md](design.md) 消费这些事实，[decisions.md](decisions.md) 保存已经接受的选择；不得把候选方案改写成已观察行为。

## 证据边界

2026-10-03 复核未变化的源码基线：core-py `1385e6066336eee37626e3b4f4bf68155f9bf1b7`，client-web `367ace98bfb7e9880c002e7971eb397a25c9ef84`，Hub 与 core-py 共享引用均为 `42f7bad1c61e57b5e0ebf55e27815ddc2ae913fa`。Hub 与共享挂载未发现未提交修改；client-web 有与本任务无关的未跟踪 `.agents/skills/vue-ts-code/`，须保留。SVC 状态健康。

E1—E12 是定向源码调查；新增实验和官方文档事实见 E13—E28。源码、引用、依赖或部署版本变化后重验受影响结论，合成实验不替代业务验收。首轮 advisor 支持标准传播、独立 Job 关联和可替换后端；此前一次咨询因额度未完成，后续针对实际后端结果的咨询已完成，支持否决 OpenObserve 及限定 Tempo flags 例外。用户明确 serverless/scale-to-0 后，advisor 根据新证据支持 SaaS 优先、OpenObserve Cloud 先验与必要语义门槛，原自建推荐由 D8 替代；随后零费用要求又由 D9 将首验改为 Grafana Cloud Free，并限定 Cloudflare 的补充范围，advisor 支持该收束。选择仍由主 Agent 负责。

| ID | 已观察事实 | 主要证据与影响 |
| --- | --- | --- |
| E1 | 一个 deployment 是一个 owner，Peer 可直接操作数据库或委派同步能力 | [共享 authority](../../docs/_shared/20-product-tdd/system-state-and-authority.md)、[Peer 契约](../../docs/_shared/20-product-tdd/semantic-retrieval-and-peer-capabilities.md)；不能假定固定前后端或自动增加租户模型 |
| E2 | 日志走 stdout，Python backend 缺省 PG、可选 Logtail/none；当前依赖无 OTel | [日志初始化](../../libs/obsrv/main.py)、[依赖](../../pyproject.toml)；保留本地诊断，新增受限的结构化事件出口 |
| E3 | 请求、周期任务和 Job 使用自定义关联 ID | [middleware](../../app/middleware.py)、[scheduler](../../app/scheduler.py)、[JobManager](../../app/business/job.py)；不是标准跨 Peer Trace |
| E4 | PG writer 有界排队、批量独立事务，仍共用业务连接池 | [handler](../../libs/obsrv/log_handler_postgresql.py)、[uow](../../app/persistence/observability/uow.py)；队列 1024、每批最多 100、排空最多 5 秒，不能称无损 |
| E5 | Web Job 日志页按 `job.<id>` 查 logs 表 | [Job 页面](../../../client-web/apps/client-web/src/views/jobs/job/job.vue)、[Log 查询](../../../client-web/packages/core/src/obsrv/log.ts)；不能原位替换旧 trace_id 后直接退役 |
| E6 | 浏览器通过 PostgREST 提交、领取和关闭 Job，也能本地执行 handler | [TS JobManager](../../../client-web/packages/core/src/job/manager.ts)、[Job schema](../../../client-web/packages/core/src/job/job.ts)；跨语言生产者和执行者都属于契约消费者 |
| E7 | Python 手动任务与 Cron 复用 create_in_uow；当前 Job 无提交上下文字段 | [Python JobManager](../../app/business/job.py)、[CronManager](../../app/business/cron.py)、[Job schema](../../app/schemas/job.py)；只在 REST middleware 加上下文会漏路径 |
| E8 | Peer ID 已有 UUID；通用 deployment configs 已存在，但检查的配置/身份表面未提供统一遥测部署标识 | [Peer schema](../../app/schemas/peer/main.py)、[settings](../../app/settings.py)、[configs](../../app/schemas/deployment_config.py)；选择标识来源时不推导数据库 URL、凭据或后端项目 ID |
| E9 | Agent debug 默认关闭，已有 thread/turn/model/tool 事件 | [debug](../../app/business/agent/debug.py)、[thread](../../app/business/agent/thread.py)、[说明](../../docs/40-deployment/agent-debug.md)；适合复用采集位置，不是执行恢复记录 |
| E10 | 两类 chat adapter 都未保留 usage；阿里流式路径跳过无 choices 的块 | [OpenAI-compatible](../../app/business/ai/dialects/openai_compatible.py)、[Alibaba](../../app/business/ai/dialects/alibaba_model_studio.py)；usage/流结束的准确性需在 provider 边界验证 |
| E11 | Thread 存于内存，Agent Query 结果已有 answer/references | [Thread persistence](../../app/business/agent/persistence.py)、[Agent Query](../../docs/30-unit-tdd/agent-query-sink.md)；不能把 Trace 当结果或恢复权威 |
| E12 | 现有 Compose 声明 PostgreSQL、core、PostgREST；开发数据库由 SVC 管理 | [Compose](../../docker-compose.yml)、根 `AGENTS.local.md`；观测实验需独立资源，不借清理实验删除现有数据库 |
| E13 | 标准 Python/JS propagator 互操作通过；Python malformed tracestate WARNING 含原始 canary | [实验报告](experiments/README.md)；浏览器尚未运行，基础远端来源限制必须覆盖 SDK 诊断 |
| E14 | 旧 Python/TS Job 模型容忍新增列，旧 REST form 拒绝额外字段 | [旧消费者实验](experiments/README.md)；该轮仅模型边界，后续实际 SQL 更新见 E18 |
| E15 | core-py ready 要求 migration heads 精确相等 | [readiness](../../app/database_contract/readiness.py)、[bootstrap](../../run.py)；不得由 nullable 列推导旧 runtime 在新 schema 获准运行 |
| E16 | OpenObserve 合成三信号可查询，但丢失 AI absent/zero 区别；中断时 Collector 有界丢失 | [原始实验](experiments/README.md)；后端候选重开，不宣称业务故障隔离已通过 |
| E17 | Tempo 重启前后保留四条样本的当前 AI/因果语义，历史 Link flags 丢失 | [Tempo 证据](experiments/README.md)；当前语义通过，完整 OTLP 保真未通过，全栈后续见 E20 |
| E18 | disposable PG 上实际旧 Python repository 和 TS JobManager/DBAPIClient 经 PostgREST 创建默认 NULL，claim/close 保留 carrier；模拟新 head 时实际旧 readiness 拒绝 | [数据库证据](experiments/convergence-20261003.md)；支持两列与协调升级，不等于正式 migration/完整启动已验 |
| E19 | SDK traceparent 注入 55 bytes，合法 tracestate 可达 1109 bytes；数据库拒绝 513-byte 字段 | [容量证据](experiments/convergence-20261003.md)；512 是应用存储政策，capture 超限 optional state 整体省略 |
| E20 | 五组件独立 API、Grafana proxy 和 UI 跑通 Job 日志→execute/model→submit Link；Loki 保持 absent/zero，Prom counter/histogram 正确 | [闭环证据](experiments/convergence-20261003.md)；Editor 完整导航，Viewer 只有固定面板 |
| E21 | 2 CPU/4 GiB 限制下查询后的 Docker 快照约 608 MiB；Grafana 首次启动约 8 分 18 秒 | [资源证据](experiments/convergence-20261003.md)；非稳态/峰值容量，生产健康宽限与预算须 G3 验 |
| E22 | 现有自托管 Compose 在 core-py；未发现独立 infra 仓库。client-webext 是独立旧 direct-fetch repo，iOS/rokid 有各自原生入口，ext-reg 为 Worker | [覆盖与归属](task-map.md)；原自建配方归属依据；不代表应当自建，也不能宣称共用 Web 接入自动覆盖所有客户端 |
| E23 | OO1.0.4 原始 -1 保留，但 total 被补为0/部分和，省略 cost 仍补零；source=unavailable 保留，直接负值求和错误 | [本轮实验](experiments/sentinel-saas-20261003.md)；允许最少来源元数据与受控查询，不再以补值全盘否决平台 |
| E24 | OO Cloud 按量收费；Grafana Cloud 有免费三信号和标准直发；PostHog 原生 OTLP 三信号齐备但 metrics Alpha、tracing Beta、AI/Trace 查询和 UI 分离 | [官方资料判别](experiments/sentinel-saas-20261003.md)；无需自建常驻栈，目标账户仍待准入 |
| E25 | Sir 明确 serverless、scale-to-0 和 SaaS 优先，偏好 OpenObserve | 当前会话；否定原单机/常驻 Collector 的默认预算假设，D8 与 V8 已修订 |
| E26 | Sir 暂时不能使用收费服务；Cloudflare 原生观测/AI Gateway/Analytics Engine 有免费能力，但通用多 Peer 后端仍有范围缺口 | [Cloudflare 与免费方案](experiments/sentinel-saas-20261003.md#cloudflare-与当前零费用方案)；D9 改为 Grafana Cloud Free 首验，按日期区分 Cloudflare 新旧限额 |
| E27 | Python ObsrvSetting 默认 postgresql，.env.example 同样为 PG；Compose 未配置 fallback 为 none | [setting](../../libs/obsrv/setting.py)、[初始化](../../libs/obsrv/main.py)、[Compose](../../docker-compose.yml)；D10 保留默认 PG，实施时对齐 Compose fallback 并保留显式覆盖 |
| E28 | Sir 同意 Grafana Cloud Free，强调 vendor-agnostic、新遥测按需开启且默认保留 PG 日志 | 当前会话及 [D10](decisions.md)；撤销 PG writer 退役与端点存在即启用，新增 V0、修订 V3/V7 |

## 问题处置

| ID | 状态与处置 | 对后续的影响 |
| --- | --- | --- |
| Q1 | 尚缺 Sir 的原文/长期复核/评测承诺；新增 OTLP 按运行诊断+结果来源关联、原文默认关闭定稿；原 PG 内容行为保留 | 不阻挡元数据实现；开启长期快照前确定保存/删除与结果 owner schema，不能把 V10 擅自排除 |
| Q2 | SaaS/serverless/scale-to-0 与当前零新增观测费已明确；实际事件/查询量、区域和保留需求仍未给出 | 先验实际 Free 的必要能力和额度；不能用低单价/试用绕过零费用约束 |
| Q3 | 当前按一个 deployment 一个 owner；未出现跨 owner 集中运营需求 | 如出现则重开数据/查询边界，不从部署属性推导隔离 |
| Q4 | 已收敛：[共享形状](design/shared-contract.md)确定两列、容量、config key/schema 和初始化责任 | 进入 Hub/数据库协议实现；保持 exact-head 与协调升级 |
| Q5 | D10：Sir 已同意 Grafana Cloud Free 按需启用；Cloudflare 用于实际覆盖部分，目标 SaaS 准入未运行 | 仅验必要查询/字段/入口，失败才转备选；账户/预算边界仍归 Q2 |
| Q6 | 已修订：各 Peer 本地 opt-in 后直发 SaaS，默认 PG 不变；部署 owner 管理项目与数据生命周期，转发/Collector 按缺口引入 | 无需新平台仓库或默认常驻主机；core-py 分发相关接入文档 |
| Q7 | 源码覆盖清单已完成，活跃发布/运行实例仍需部署盘点 | 所有已发现 Unit 留在 G3 清单，未知运行状态不算不适用 |

此前 Q1/Q2 未收到具体参数而采用单机假设；Sir 本次已明确修正 Q2 的首要标准，现按 SaaS 与 scale-to-0 推进。本次零新增观测费已由 Sir 明确，长期内容承诺仍不能从未答复推导，生产启用在对应交付门槛收束，不重复索取总体架构许可。

## 新增共享 truth 的拟归位

身份、传播、Job 上下文和观测/业务 authority 的区别需要 Python 与 TS 共同理解，拟由 Hub `20-product-tdd/` 的独立观测契约承载，现有 cross-unit 导航与 Job 契约仅引用或补充必要连接。SDK 初始化、logger wiring、UI 组件、Collector 配置和资源值留在各 Unit/部署 owner。

当前 Hub 可用且与 Spoke 引用一致；没有理由从 `docs/_shared/` 修改。需遵循 [共享文档工作流](../../docs/_shared/00-meta/skills/edit-svc-shared-docs/SKILL.md) 的 Hub 源先发布、Spoke 引用后推进顺序。已准备[未应用 Hub patch](design/hub-contract.patch)及[评审说明](design/hub-review.md)。当前源仓与挂载未修改；正式发布仍需明确提交/推送指令。
