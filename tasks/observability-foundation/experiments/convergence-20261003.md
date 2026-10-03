# 2026-10-03：数据库与三信号查询闭环

> 后续修订：Sir 明确 serverless/scale-to-0 后，默认自建选择已由 [D8](../decisions.md) 替代；当前方向与缺失值判别见 [SaaS 修订报告](sentinel-saas-20261003.md)。本文件保留当时的实验事实和决策背景。

本轮补齐 G1 的两个判别：持久 Job carrier 是否能兼容实际旧消费者，以及分立后端能否形成一个可操作的诊断入口。结果支持进入实现；没有启动真实多 Peer 应用，没有使用生产数据，也没有证明生产容量。早期 OpenObserve 否决及 Tempo 重启/flags 限制仍以[前轮报告](README.md)为准。

## 数据库与传播容量

独立 PostgreSQL 使用仓库现有 `scripts/database.py init --profile development` 初始化，基线 readiness 通过。实验只在 disposable database 添加两个 nullable text 列，各用 `octet_length <= 512` 限制；未创建应用 migration。实际旧 Python JobRepository 创建记录时两列为 NULL，读取已有 carrier 后 claim/close 更新终态与 state，carrier 保持不变。实际旧 TypeScript JobManager、Job schema、DBAPIClient 经 PostgREST 完成同样操作；只替换配置/认证来源以指向实验库，没有替换 HTTP transport。这是 Node 运行证据，不是浏览器上下文证据。

语义损坏但有界的 `broken` 可以存入；513 bytes 被数据库约束拒绝。临时将 `public.alembic_version` 改成实验 head 后，实际旧 readiness 明确拒绝 migration mismatch，最后恢复原 head。因此新旧模型的数据兼容成立，任意旧新 runtime 混跑不成立。选择协调升级，不为本任务新增兼容版本框架。

Python SDK 注入的 traceparent 为 55 bytes；合法的 32 项 tracestate 可以达到 1109 bytes。512 是应用持久化容量政策，不是 W3C 最大值。生产 capture 应先让 SDK 标准化，再在存入 Job 前省略超限的整个 optional tracestate，保留 traceparent 的 ID 与 flags，记录有界省略原因；不自制 W3C parser，不截断半个成员，也不让观测状态导致业务事务失败。[W3C 的容量与截断规则](https://www.w3.org/TR/trace-context/)

证据：[Python/数据库](evidence/convergence-20261003/database-probe.json)、[TypeScript/PostgREST](evidence/convergence-20261003/database-client-result.json)、[SDK 容量](evidence/convergence-20261003/carrier-capacity.json)。实验曾先误用 schema 限定的 alembic_version 路径；从真实 catalog 确认后修正任务脚本，仅重置独立实验数据再运行，没有变更业务仓库。

## 采集到查询

标准 Python SDK 发出 submit、execute 和 model spans、关联日志、counter=3、histogram count=2/sum=0.4；再发出 AI usage 缺失与真实零两条日志。Collector 用原生 OTLP/HTTP 出口分别写 Tempo、Loki、Prometheus。独立 API 和 Grafana datasource proxy 均读回预期结果。

| 判别 | 观察与适用边界 |
| --- | --- |
| 日志字段 | Job/trace/span 可关联；缺失 usage 不存在、零为字符串 `"0"`。Loki 把点换成下划线、非字符串属性字符串化；可消费但不承诺原始类型保真 |
| 指标 | cumulative counter=3；直方图 count=2、sum=0.4，各 bucket 正确。没有 Job ID 标签，不开启实验性 delta 转换 |
| Trace | Job 42 搜索到提交与执行两条 Trace；执行有模型子 span，Link 指向提交 span |
| Grafana 页面 | Job 42 显示三条日志，统计面板为 3 和 2；展开日志可打开执行 Trace，再点 `View linked span` 在分屏显示 job.submit |
| 角色 | anonymous Viewer 看得到固定面板但没有 Explore/内部 Trace 链接；仅此 loopback 合成实验改成 Editor 后链路通过。正式部署使用有身份的诊断用户，不能复制匿名配置 |

内部日志链接从真实页面读取后在同一 tab 打开，因为实验浏览器的新窗口点击未创建 tab；后续 Span Link 实际点击成功。没有通过构造一个独立 API 查询冒充 UI 跳转。Grafana datasource provisioning 的 `${__value.raw}` 需要在 Grafana 与 Compose 两层分别转义；运行中 inline config 变更需重建对应容器才生效。

原始证据：[输入标识](evidence/convergence-20261003/expected.json)、[独立查询](evidence/convergence-20261003/stack-direct.json)、[Grafana proxy](evidence/convergence-20261003/stack-grafana.json)、[额外日志输入](evidence/convergence-20261003/stack-log-input.json)、[UI 观察](evidence/convergence-20261003/ui-observation.json)。主要依据：[Loki OTLP 映射](https://grafana.com/docs/loki/latest/send-data/otel/)、[Prometheus OTLP](https://prometheus.io/docs/guides/opentelemetry/)、[Loki derived fields](https://grafana.com/docs/grafana/latest/datasources/loki/configure/)、[Grafana Explore 角色配置](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/)。

## 版本与资源观察

本轮继续使用前轮 Collector 0.162.0、Tempo 3.1.0 和 Python OTel 1.45.0，新增镜像如下，完整可执行配置在 [stack-lab.py](stack-lab.py) 和 [database-lab.py](database-lab.py)。固定版本是实现起点，升级仍需重验字段映射。

| 组件 | 固定镜像 |
| --- | --- |
| Loki 3.7.8 | `grafana/loki@sha256:1107dd5274e0ada47e42472b7a7e71f3b2a2fe878878108f3e2f9e51528f0193` |
| Prometheus 3.15.0 | `prom/prometheus@sha256:efd719c99d83b060d9daefdcf00360461adf279f45ef5391f8d111892118753e` |
| Grafana 13.2.3 | `grafana/grafana@sha256:b28bae15e219c998fb0e0424ed724930cc61b1f61fb404d47c862f9a23f9e572` |
| pgvector pg17 | `pgvector/pgvector:pg17@sha256:d2ef61f42ef767baa5a1475393303cc235bcd92febd9d7014eddb48b41f3bad0` |
| PostgREST 14.15 | `postgrest/postgrest:v14.15@sha256:2f8e7b656f09db697a8875177694b417b35cb76c21370de07fc54e711e902326` |

五组件限制合计 2 CPU/4 GiB：Tempo 和 Loki 各 0.5 CPU/1 GiB，Prometheus 0.35 CPU/768 MiB，Grafana 0.4 CPU/768 MiB，Collector 0.25 CPU/512 MiB。数据库实验另限 PostgreSQL 1 CPU/768 MiB、PostgREST 0.25 CPU/256 MiB，不计入观测栈预算。

UI 查询后的 [Docker 快照](evidence/convergence-20261003/stack-stats.jsonl)合计约 608 MiB，五个[容器状态](evidence/convergence-20261003/stack-state.jsonl)均未标记 OOM。十次极小日志查询的客户端 RTT 中位数约 9.71 ms，Grafana proxy 约 9.17 ms。它们包含本机经 SSH 到远端的路径，不能外推为生产 P95、CPU/RSS 峰值或每天磁盘增长。

Grafana 首次启动日志从 06:04:33 到 06:12:51 UTC 才开始 HTTP listen，约 8 分 18 秒，期间有一次后台资源注册超时；保留 SQLite 卷后的重建明显更快。Tempo idle scheduler 仍有 `no jobs found` 噪声。G3 必须复核冷启动预算、健康检查宽限和运维噪声。2 CPU/4 GiB 是可行性实验上限，不能写成最低配置或已满足 Sir 的实际预算。

## 复现与结束状态

从 core-py 根运行，先确认对应实验项目不存在冲突。`database-probe.py probe` 的候选 DDL 只供新初始化的实验库执行一次；重跑应新建 disposable 实验库，不指向任何共享库。

```bash
python3 tasks/observability-foundation/experiments/database-lab.py up
pdm run python tasks/observability-foundation/experiments/database-probe.py init
pdm run python tasks/observability-foundation/experiments/database-probe.py probe
python3 tasks/observability-foundation/experiments/database-lab.py postgrest
node tasks/observability-foundation/experiments/database-client.mjs
pdm run tasks/observability-foundation/experiments/carrier-capacity.py
python3 tasks/observability-foundation/experiments/stack-lab.py up
pdm run tasks/observability-foundation/experiments/signals.py
python3 tasks/observability-foundation/experiments/stack-probe.py send-log-cases
python3 tasks/observability-foundation/experiments/stack-probe.py direct
python3 tasks/observability-foundation/experiments/stack-probe.py grafana
python3 tasks/observability-foundation/experiments/database-lab.py stop
python3 tasks/observability-foundation/experiments/stack-lab.py stop
```

各服务 ready 与异步摄取可见后才运行依赖步骤；Grafana 首次初始化不能用一条短超时判为失败。连接方式与命令级 WSL interop 说明沿用前轮报告。新的 runtime 凭据与短时 JWT 均为 0600、处于忽略目录，不归档。

本轮结束停止两个项目的七个容器并关闭两个 SSH 隧道，保留独立合成数据卷：`inkcre-o11y-db-g1-b0a97f7c_data` 和 `inkcre-o11y-stack-g1-b0a97f7c_{tempo,loki,prometheus,grafana}`。加上前轮四个容器共十一项，最终状态见 [resource-final.json](evidence/convergence-20261003/resource-final.json)。不删除父任务数据，不操作 SVC 开发数据库。

G1 的设计判别已结束；正式入口认证、真实浏览器 context、应用故障隔离、内容出口 canary、实际 provider、容量/备份恢复继续作为 G2/G3 实现验收，不能借这份报告提前标通过。
