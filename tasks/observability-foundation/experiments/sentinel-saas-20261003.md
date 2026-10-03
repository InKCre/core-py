# 2026-10-03：缺失值与 SaaS 方向修订

Sir 明确把 serverless、scale-to-0 和无需维护常驻服务作为选型标准。本轮重新判断 `-1`，并查阅三家 SaaS 的官方文档；没有开通账户、采购服务或上传任何业务数据。自建五组件的既有实验仍有效，但不再拥有默认部署结论，SaaS 方向见 D8；Sir 随后明确暂时不能付费，D9 明确零费用；随后 Sir 通过 D10 选定 Grafana Cloud Free、默认关闭新增遥测并保留 PG。现行决定见[任务决定](../decisions.md)，下文候选顺序保留为当时的判断。

## `-1` 的实际效果

复用前轮固定 digest 的 OpenObserve 1.0.4 和 Collector 0.162.0，仅发送六条合成 span。输入与独立 API 查询见 [sentinel.json](evidence/sentinel-saas-20261003/sentinel.json)，可复现脚本为 [sentinel-probe.py](sentinel-probe.py)。本轮不验证 OpenObserve Cloud 的运行版本或 AI UI。

| 输入情况 | 后端原始字段 | 后端自动生成字段 |
| --- | --- | --- |
| input/output/cost 都为 `-1` | 三个 `-1` 保留 | total 为 0 |
| input=8、output/cost=`-1` | 原始值保留 | total 为 8，不能解释成完整总量 |
| 明确零 | input/output/cost 为 0 | total 为 0 |
| input=8、output=3、cost=0.125 | 原始值保留 | total 为 11 |
| 只有 input/output=`-1`，省略 cost | 两个 `-1` 保留 | total 为 0，cost 为 -0.0 |
| 省略数值，同时声明各字段 source=`unavailable` | source 字符串保留 | 数值仍补零，但来源元数据可以识别 unknown |

把第一、第三、第四条直接求和，input=7、cost=-0.875；先过滤负值后是 8 与 0.125。查询使用 DISTINCT span_id 排除传输重试重复，以单独判别 sentinel 算术。过滤后的值也只是已知部分，必须同时显示 unknown 数量；全部缺失时不能展示为完整的零。input/output 部分缺失时，完整 total 仍 unknown。

结论是 `-1` 可作特定存储/展示的缺失编码，但不适合直接进入标准 usage 指标、成本总额或默认 AI 面板。源端标准字段仍按实际 provider 值写入，缺失省略；如果所选后端会补值，允许最少的逐字段来源元数据，例如 input/output 的 provider/unavailable、cost 的 estimate/unavailable。查询先解释来源，再计算；这类元数据没有复制数值，也不另建业务状态权威。后端生成的估算、total 和 agent.version 都不能未经判别就当作采集事实。无需因为该缺口而承担五组件常驻运维。

## SaaS 的当前能力与费用

以下是 2026-10-03 读取的官方公开资料，美元价格不含税，不是账户报价或实测账单。预算要计入采集端计算/出口、写入、查询、保留和超额；业务 scale-to-0 不保证所有留存、历史查询或平台项目都零费。

| 候选 | 官方能力与费用 | 对本任务的判断 |
| --- | --- | --- |
| OpenObserve Cloud | 统一 logs/traces/metrics；当前 $0.50/GB 写入、$0.01/GB 查询，14 天试用；非 metrics 默认 30 天、metrics 15 个月。2025 定价政策说明无最低消费、取消永久免费档 | 第一验证候选；符合用户偏好、统一查询和按量费用，需在 Cloud 验来源字段、必要因果查询及预算边界 |
| Grafana Cloud Free | 托管三信号并接受 SDK 直发 OTLP；免费档 10k 活跃指标序列、每月 logs/traces 各 50GB、14 天保留、3 名活跃用户。Pro 有 $19/月平台费另加用量 | 零美元试点的明确备选；组件运维由供应商负责，不能与自建五组件混同 |
| PostHog Cloud | AI O11y、logs、通用 tracing 与原生 OTLP metrics；tracing 为 Beta、metrics 为开放 Alpha。每月免费 10GB logs、100k AI events；logs 默认 14 天 | 有吸引力的整合候选，但不作为当前唯一基建首选；metrics/通用 tracing 费用、必要 Link 查询和账户行为尚未确认 |

价格来源：[OpenObserve 当前价格](https://openobserve.ai/pricing/)、[无最低消费与免费档调整](https://openobserve.ai/blog/june-25-pricing-policy-updates/)、[Grafana Cloud 价格](https://grafana.com/pricing/)、[PostHog 价格](https://posthog.com/pricing/)。Grafana 官方允许不能运行 Collector 的应用 [直接用 SDK 发送 OTLP](https://grafana.com/docs/grafana-cloud/send-data/otlp/send-data-otlp/)。免费额度不是容量测量，达到预算上限可能丢弃新数据；PostHog 价格页明确说明了此行为。

PostHog 的 [普通 tracing](https://posthog.com/docs/distributed-tracing) 与 [AI OTLP](https://posthog.com/docs/ai-observability/installation/opentelemetry) 是不同出口：`/i/v1/traces` 接通用 span，`/i/v0/ai/otel` 只接符合 AI 名称/属性的 span。不能用 AI 出口代替整个 Job trace。其 [metrics 文档](https://posthog.com/docs/metrics) 提供标准 `/i/v1/metrics`，不是只能从日志派生指标；Alpha 明确提示接入细节可能变更。

[官方 AI/Trace 关联说明](https://posthog.com/docs/distributed-tracing/link-ai-observability)说明两类记录的 ID 编码不同，分属不同查询集群，需两次查询，当前 UI 没有互相跳转。提供同一 trace ID 可以关联，并不等于已有一体化诊断体验。未知值、部分 usage、重试重复、cost 来源与 Span Links 都要在目标服务实际读回，不能由品牌或“支持 OTLP”推断。

## 准入边界与结束状态

默认方案改为应用 SDK 直发 SaaS；浏览器能否直发取决于供应商是否提供适合客户端的受限写入能力。否则复用受控的按请求转发入口，禁止把服务端秘密打入公开客户端。Collector 仅在已证明的协议、认证、缓存或路由缺口需要它时引入。短生命周期在平台保证的运行窗口内有界 flush，失败允许丢失，不能依赖响应完成后继续运行。

一次候选验收覆盖三信号、Job→执行→提交关联、AI unknown/zero/partial、浏览器入口、导出样本、限额和应用停止；达到必要诊断能力即停止比选。不要求所有 OTLP 字段原样存储，不以历史 Link flags 或当前不用的派生字段单独否决产品。因果 ID、来源事实和正确聚合不可丢。

复现顺序是 `lab.py up`、等待 ready、`sentinel-probe.py`、`lab.py stop`，从 core-py 根用 python3 运行；远端与命令级 WSL interop 沿用[前轮说明](README.md)。已停止本轮两个容器和隧道，合成卷随父任务保留。完整资源与任务包验证结果另归档于本轮 evidence 目录。没有修改应用、Hub、共享引用或 SVC 开发数据库。

## Cloudflare 与当前零费用方案

Sir 随后明确暂时不能使用收费服务。因此当前新增观测服务费用按 **$0** 处理，付费服务的试用期不能充当长期免费方案。OpenObserve Cloud 从第一候选移出，先验 Grafana Cloud Free；Cloudflare 原生能力用于已在该平台运行的 Unit 或明确需要的模型网关，不强制业务迁移平台。

| Cloudflare 能力 | 2026-10-03 核对的官方范围 | 本任务适用性 |
| --- | --- | --- |
| Workers Logs、Workers Traces、Cloudflare Traces | 采集 Worker 与 Cloudflare 网络/服务路径。Workers Logs 当前 Free 为每天20万条、保留3天；最新 Workers Traces 页面写7天保留 | 可覆盖 ext-reg 等实际运行于 Cloudflare 的 Unit；没有找到接收任意外部 Peer 三信号的通用 OTLP 存储入口，不能由“支持 OTel 导出”推导有此入口 |
| AI Gateway | 核心功能免费，观测经过网关的模型调用，并可向外导出 GenAI spans；模型推理本身仍按 provider 规则收费 | 可用于确有模型代理需求的路径，不提供完整 Job/检索/工具/跨 Peer 因果图；不为免费观测强制改变模型请求路径 |
| Workers Analytics Engine | 公布 Free 每天10万写点、1万查询；页面说明当前尚未计费。数据保留3个月，通过 Worker writeDataPoint 写入，读写均可自适应采样 | 适合聚合趋势；不保证找回单条记录或还原事件序列，不选作唯一 Trace/长期证据库 |
| Worker 请求转发 | Free 每天10万请求，每次10ms CPU；无需常驻主机 | 浏览器私密出口的可选转发宿主，需先证明现有入口不能满足；不附带 D1/R2、自研索引或重试队列 |

来源：[Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)、[Workers Traces](https://developers.cloudflare.com/workers/observability/traces/)、[Cloudflare 数据集](https://developers.cloudflare.com/observability/logs/datasets/)、[Trace 配置](https://developers.cloudflare.com/observability/traces/configuration/)、[AI Gateway 价格](https://developers.cloudflare.com/ai-gateway/reference/pricing/)、[Analytics Engine 价格](https://developers.cloudflare.com/analytics/analytics-engine/pricing/)、[保留](https://developers.cloudflare.com/analytics/analytics-engine/limits/)、[采样限制](https://developers.cloudflare.com/analytics/analytics-engine/sampling/)、[Workers 价格](https://developers.cloudflare.com/workers/platform/pricing/)。这些是官方能力与限额，不是目标账户实测。

Cloudflare 的日期边界必须保留：[统一 Observability 定价](https://developers.cloudflare.com/observability/pricing/)从 **2026-12-01** 才生效，Free 对列出的日志/Trace 共享每天0.5GB、保留7天，超限停止新摄取直到 UTC 零点，已存数据继续可查。不能把它写成10月3日已生效，也不能假定所有安全日志数据集均免费。Workers Logs 当前页仍列3天，而新数据集总表列7天；当前日志使用专门页面的明确旧定价，启用时核对账户实际设置，不混用即将切换的政策或 previews 文档。

AI Gateway 同样存在新旧客户差异：[9月24日之后首次建网关](https://developers.cloudflare.com/ai-gateway/reference/limits/)的日志跟随 Workers Logs；之前的客户才有 legacy 免费共10万条存储。不能把旧价格表当作新账户承诺。[日志配置](https://developers.cloudflare.com/ai-gateway/observability/logging/)支持 `cf-aig-collect-log-payload: false` 保留 metadata 而不保存原始请求响应。但 [OTel exporter](https://developers.cloudflare.com/ai-gateway/observability/otel-integration/)单独列出了 prompt/completion 属性；前述日志开关是否同时约束导出内容尚未验证，不能直接打开 exporter 并声称原文不会外流。Gateway 处理请求本身也引入模型内容经过 Cloudflare 的业务路径，不是纯旁路诊断。

当前工程推荐是 **标准 SDK → Grafana Cloud Free**，适用的 Cloudflare Unit 另以现成 OTLP 导出汇入同一诊断入口。Cloudflare 有[官方 Grafana 导出步骤](https://developers.cloudflare.com/observability/export/opentelemetry/grafana-cloud/)，但 Workers 的[平台 OTLP 出口](https://developers.cloudflare.com/workers/observability/opentelemetry-export/)不支持平台/自定义 metrics 导出，不能把 logs/traces 导出视为三信号全覆盖。内容准入、外部传播与指标补充按 Unit 实测，不为完整面板强制新增常驻采集器。

Grafana 官方明确 [Free 不需要信用卡且非限时试用](https://grafana.com/docs/grafana-cloud/learn-and-build/get-started/learn/)，当前[免费额度](https://grafana.com/pricing/)为10k活跃指标序列、logs/traces各50GB/月、14天保留。只用实际 Free，不开 Pro、超额付费或依赖 trial 附加能力。验收记录目标账号的序列/摄取/速率限制、超限拒收与采集端丢弃；免费额度不是完整诊断或生产 SLA 保证。必要时减少日志量、采样和指标基数，业务结果与长期证据继续由已有 owner 保存。

用 Cloudflare Workers 加 D1/R2 自建观测平台虽然能利用基础设施额度，但会把 OTLP 转换、索引、查询、Trace 展示和数据生命周期交给 InKCre；与当前少维护、可替换的目标不符。本轮不采用，也没有开通任何云端功能、修改服务配置或发送遥测。
