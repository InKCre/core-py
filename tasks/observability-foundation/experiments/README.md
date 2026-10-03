# G1 前轮传播与后端判别

> 后续修订：Sir 明确 serverless/scale-to-0 后，默认自建选择已由 [D8](../decisions.md) 替代；当前方向与缺失值判别见 [SaaS 修订报告](sentinel-saas-20261003.md)。本文件保留当时的实验事实和决策背景。

2026-10-01—03 使用合成数据检查标准传播、旧模型读取及后端语义。结论是保留 OTel/OTLP 与部署自有 Collector，结束 OpenObserve 1.0.4 的统一后端候选验证，继续 Tempo 3.1.0 的 Trace 路线。本轮尚未包含数据库与五组件闭环，后续结果见[2026-10-03 收敛报告](convergence-20261003.md)。本文保留当时的实验事实；选择与重开条件由[任务决定](../decisions.md)拥有。没有运行 InKCre 业务旅程，不能把这些结果算成 G2 通过。

## 判别结果

| 检查 | 实际观察 | 对下一步的影响 |
| --- | --- | --- |
| Python ↔ JavaScript 标准传播 | sampled/unsampled、未来版本、缺失/损坏/零 ID、tracestate 及独立 Job trace/Link 均按 SDK 结果核对；Python asyncio 和 JS 显式 context 并发隔离通过 | 复用官方 propagator；JS 在 Node 运行，浏览器异步 context 尚未验证 |
| SDK 诊断日志 | Python `opentelemetry.trace.span` 的 malformed tracestate WARNING 含合成原文 canary | 实现必须在出口前限制该诊断；不因不记录 HTTP body 就宣称没有内容副本，也不重写 W3C parser |
| 旧 Job 模型 | 实际 Python SQLModel 与 TS Zod 接受缺失、NULL、额外 carrier 字段，忽略未知列；旧 REST create form 拒绝额外字段 | REST 从 HTTP 上下文捕获，不向旧 body 塞字段。模型可读不证明数据库更新或 runtime admission 兼容 |
| OpenObserve 三信号 | 独立 API 查到提交/执行/AI 三个 spans、关联日志、counter=3、histogram count=2/sum=0.4 和各桶；重启后仍可查 | 基本摄取成立；累积指标不能跨导出快照求和 |
| OpenObserve 属性/Links | Trace 的整数 Job ID 变字符串；Link 属性被展开、整数变字符串，Link ID/tracestate 可读 | 表示变换需要消费端声明，不等于原始 OTLP 无损导出 |
| OpenObserve AI 缺失值 | 未提供 usage/cost 的 AI span 被写入 usage=0、cost=-0.0；缺失 agent.version 被 service.version 填充。显式零和显式非零也可读 | unknown 与真零在摄取时已不可区分，查询层无法还原；当前版本不符合本任务 AI 语义 |
| Collector 后端中断 | 4096 spans、16 次请求全部 HTTP 200；最终 enqueue_failed=3712、send_failed=384，队列回零 | 接收成功不是持久化成功；丢失可观察。没有执行业务，V6 仍待验证 |
| Tempo 查询与重启 | 按整数 Job ID 找到四条 trace；重启前后属性的存在性、类型和值，以及 Link ID、tracestate、属性均与输入一致 | 当前 AI/因果语义的窄门槛通过；可以继续检验日志、指标与 UI 集成 |
| Tempo Link flags | 输入 flags=1，查询中缺失；固定版本存储 schema 也无该字段 | 完整 OTLP 保真不通过。不得把查询默认零解释成原始未采样，更不能用历史记录恢复传播或推断完整性 |

旧模型检查不访问数据库。源码另证实 core-py 的 readiness 要求 migration heads 精确一致，因此“加 nullable 列”不能保证旧 core 在新 schema 上启动；旧模型检查也没有验证已经运行的旧 Peer 能否持续工作。发布必须独立处理协议准入。

OpenObserve 的三个 AI 判别样本分别是 absent、真实 zero、显式 usage 8/3 与 cost 0.125。固定标签源码表明 LLM enrichment 会填充缺失值；`ZO_MODEL_PRICING_ENABLED=false` 只关闭数据库价格查询，仍有内置价格回退，不构成禁用 enrichment 的证据。主 Agent 与 advisor 据此收束该候选，不增加影子字段或修复层。依据：[摄取入口](https://github.com/openobserve/openobserve/blob/v1.0.4/src/core/src/traces/mod.rs)、[usage/cost 处理](https://github.com/openobserve/openobserve/blob/v1.0.4/src/core/src/traces/otel/processor.rs)、[版本候选字段](https://github.com/openobserve/openobserve/blob/v1.0.4/src/config/src/meta/gen_ai.rs)。

Tempo flags 限制由[固定版本存储定义](https://github.com/grafana/tempo/blob/v3.1.0/tempodb/encoding/vparquet5/schema.go)与实际查询相互核对。当前执行采样发生在 SDK，Job carrier 是传播依据，后端查询只消费业务 ID 和因果关联，因此该历史存储损失暂不阻挡窄范围候选准入；SDK、Collector 和 Job carrier 的标准传播要求不放宽。未来消费者需要历史 flags 时重开。

## 版本、拓扑与资源

| 组件 | 实测版本与固定来源 |
| --- | --- |
| Python SDK / OTLP exporter | 1.45.0，脚本 PEP 723 隔离依赖 |
| JavaScript | Node 24.15.0；OTel API 1.9.1、core/sdk-trace-base 2.11.0；[package-lock.json](package-lock.json) |
| Collector | 0.162.0；`otel/opentelemetry-collector@sha256:310a800ad69ee430e7c541796852a242c9c7db97aaad4daa5ccf843c525fbdb2` |
| OpenObserve | 1.0.4；`openobserve/openobserve@sha256:d4a878fac1f6c56003764f7f2a1625668917388f167e222c8c810de3f54c56ba` |
| Tempo | 3.1.0；`grafana/tempo@sha256:3076b8dcdfb32fd6bc5ccef85e7b7313e6199b9cb84366257fc17ecb696db5fd` |

实验经已有 SSH 主机 `wsl.win-ws.localhost` 使用 Windows Docker CLI 访问 Docker Desktop Linux x86_64 daemon；宿主报告 12 CPU、约 16.745 GB 内存。原生 Linux Docker CLI 指向另一 daemon，不能替换调用。两个实验依次占用同一个 OTLP 转发端口，不同时启动。

每套实验限制合计 2 CPU/4 GiB：后端 1.5 CPU/3.5 GiB、Collector 0.5 CPU/512 MiB。各信号出口队列按字节限制为 1 MiB，有限重试。后端使用独立本地数据卷，平台遥测关闭；Tempo 单体 `target=all`，不引入 Kafka。普通 bridge 网络与 loopback 端口发布不等于出站隔离。

OpenObserve 重启后小样本查询 20 次，客户端 RTT 中位 56.51 ms，按排序第 19 项计算 P95 为 63.01 ms。后端中断实验的 Collector 队列采样峰值 912,150 bytes，过程 RSS 采样约 95 MB；4096 spans 最终全部丢弃。Tempo 重启后四条 trace 下 Docker 快照为后端 40.66 MiB、Collector 25.82 MiB。它们是小样本和时间点观察，不能用于全栈容量承诺、每日增长或应用开销比较；实验没有生产负载模型。

Tempo 本地部署仅用于此实验。本轮未验证正式入口鉴权、Grafana/Loki/Prometheus 集成、保留、删除、备份恢复与容量；Tempo idle scheduler 出现重复 `no jobs found` 错误日志，运维噪声待复核。重启保留样本不等于备份恢复通过。[官方单体本地部署说明](https://grafana.com/docs/tempo/latest/set-up-for-tracing/setup-tempo/deploy/locally/linux/)

## 证据入口

- [标准传播结果](evidence/openobserve-20261001/propagation.json)、[三信号输入标识](evidence/openobserve-20261001/expected.json)、[独立查询和延迟](evidence/openobserve-20261001/readback.json)。
- [AI 判别输入、后端输出与 Link](evidence/openobserve-20261001/ai-projection.json)、[中断原始计数和资源采样](evidence/openobserve-20261001/failure.json)。
- [Tempo 输入](evidence/tempo-20261003/tempo-input.json)、[重启前](evidence/tempo-20261003/tempo-before.json)、[重启后](evidence/tempo-20261003/tempo-after.json)、[Job 查询前](evidence/tempo-20261003/tempo-search-before.json)、[Job 查询后](evidence/tempo-20261003/tempo-search-after.json)。
- [Tempo 落盘指标](evidence/tempo-20261003/tempo-metrics.txt)、[重启后资源快照](evidence/tempo-20261003/tempo-stats.jsonl)。重启前 `blocks_completed_total=1`、`local_blocks_flushed_total=1`，用于区别纯内存读回。

第一次 Tempo 发送被中断，没有接收成功证据；10 月 3 日先核对空查询与 ready，再发送并完成读回/重启验证。不得把中断的首次尝试记成已接收数据丢失。归档不包含凭据，随机实验凭据仅在忽略的 `runtime/credential.json`，权限 0600。

## 复现与资源归属

以下命令从 core-py 根运行。脚本是本任务的判别实验，不是可移植生产工具。先在实验目录执行 `npm ci --ignore-scripts --no-audit --no-fund`；旧 TS 模型检查还依赖相邻 client-web 的现有 esbuild 0.28.1 路径。`propagation.py` 需已有 `runtime/` 目录，可用 `mkdir -p tasks/observability-foundation/experiments/runtime` 创建。

```bash
pdm run tasks/observability-foundation/experiments/propagation.py
pdm run python tasks/observability-foundation/experiments/legacy-consumers.py
node tasks/observability-foundation/experiments/legacy-consumers.mjs
python3 tasks/observability-foundation/experiments/lab.py up
pdm run tasks/observability-foundation/experiments/signals.py
python3 tasks/observability-foundation/experiments/readback.py
python3 tasks/observability-foundation/experiments/ai-projection.py
python3 tasks/observability-foundation/experiments/failure.py
python3 tasks/observability-foundation/experiments/lab.py stop
python3 tasks/observability-foundation/experiments/tempo-lab.py up
python3 tasks/observability-foundation/experiments/tempo-probe.py send
python3 tasks/observability-foundation/experiments/tempo-probe.py before
python3 tasks/observability-foundation/experiments/tempo-lab.py restart
python3 tasks/observability-foundation/experiments/tempo-probe.py after
python3 tasks/observability-foundation/experiments/tempo-lab.py stop
```

启动后先检查服务 ready；异步入库需要等待可查询，不能连续执行上面所有命令后将短暂不可见当成不保留。Tempo 重启实验应先从 `/metrics` 确认样本完成落盘，再重启并等 `/ready` 返回 200。查询脚本按近一小时搜索，历史复核使用归档时间范围。`ai-projection.py` 会报告明确的语义失败布尔值，退出码零不表示候选通过。`failure.py` 在 finally 中重启后端。

WSL interop 曾超时；当时经只读核对使用命令级 `LAB_WSL_INTEROP=/run/WSL/1905_interop` 恢复 Windows CLI。socket 会变化，不把该值当成永久配置，不修改宿主环境来迁就脚本。`internal:true` 网络首次未发布端口，现用普通 bridge；失败启动不作为摄取成功证据。

2026-10-03 已独立检查下列两个项目的四个容器均为 `exited`，两个 SSH control socket 均不存在。卷保留合成数据，随活跃父任务保留：

| Compose project | 保留卷 |
| --- | --- |
| `inkcre-o11y-g1-b0a97f7c` | `inkcre-o11y-g1-b0a97f7c_data` |
| `inkcre-o11y-tempo-g1-b0a97f7c` | `inkcre-o11y-tempo-g1-b0a97f7c_data` |

各配方 `stop` 停止并关闭隧道，`remove` 仅删除对应实验项目及卷。结束父任务时决定保留或删除；不要调用 `svc dev stop database` 清理本实验。未修改 SVC 数据库资源、应用源码、Hub 源、共享引用或仓库依赖。
