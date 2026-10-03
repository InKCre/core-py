# InKCre 可观测性基建

建立适合多 Peer、serverless 与 scale-to-0 的可选观测能力。Sir 已选定 Grafana Cloud Free，要求 vendor-agnostic、默认维持 PostgreSQL 日志，并已授权实施、创建分支、提交、推送与 draft PR。没有合并、生产发布或付费服务授权。

## 当前交付

首批实现已进入集成收尾：Python 与 client-web 使用标准 OTel/OTLP，本地开关缺省关闭，PG writer 与 Job 查询保留。Hub 契约已发布到分支；两 Spoke 的共享引用各自独立提交。两个 Spoke 的源码均已提交、推送并发布 draft PR；任务包与实验归档作为独立提交收尾。

| 对象 | 当前状态 |
| --- | --- |
| Hub | `codex/observability-contract`，`a603b036fd41dae5a471dea24cd7609bb4927bd5`，[draft PR #33](https://github.com/InKCre/docs/pull/33) |
| core-py | [draft PR #124](https://github.com/InKCre/core-py/pull/124)，源码 `0eba26a`，共享引用提交 `f0397e7`，基于 `fa23a1c`；默认关闭、三信号、HTTP/Peer/Job/Cron/AI/Agent/来源事件、正式迁移及受控 protobuf relay |
| client-web | [draft PR #125](https://github.com/InKCre/client-web/pull/125)，源码 `b81554d`，共享引用提交 `b1072a9`，基于 `d4c6437`；连接本地开关、三信号、Peer/Job carrier/Link、可选诊断链接与认证 relay |
| Grafana Cloud | Sir 已创建 stack 并配置写入与 Viewer 凭据。三类合成数据已由 Viewer API 独立读回；Trace/Span/Link、AI unknown/zero、日志和指标均与源输入一致 |

持久行为见 [core-py 部署文档](../../docs/40-deployment/observability.md)和已发布[共享契约](../../docs/_shared/20-product-tdd/observability-contract.md)。任务内旧设计与实验保留其历史语境，不再作为运行事实的第二权威。

## 已验证与收尾

真实隔离 PostgreSQL 已迁移至 `3d9593b0c855`，Python Job 成功/失败/取消与 PG 日志、mixed 开关、三信号及 metrics-only 已验。实际 FastAPI lifespan/readiness/JWT relay 已验。实际 OpenAI SDK 对合成 provider 的流式末块、unknown/zero、并行工具与内容 canary 已验，不等于真实付费模型验收。

真实 Chromium＋PostgREST 验证了直写、执行 Link、异步并发、重定向、JWT 与三信号。真实浏览器→core relay→接收端逐值核对 Trace/Span/Link IDs 已通过；此前 JSON 返回 200 的证据作废，通用 ProtoJSON 会误解 OTLP 十六进制 ID，因此采用官方 protobuf exporter，并明确拒绝 JSON。

- [本轮验收](verification.md)管理具体主张、证据和残余；[客户端报告](experiments/client-implementation.md)给出客户端范围。
- SDK 故障隔离、部分初始化资源回收、原生队列/导出计数已通过独立复验；迁移升级/降级/再升级保留旧 Job/PG 日志并验证容量约束。最终 `pdm run check` 已通过（14 passed、63 skipped，0 类型诊断）。
- core 最终 `pdm run check` 通过（14 passed、63 skipped）。client lint、全量类型检查、build 与 tracked 文件格式通过；完整 `pnpm check` 被用户原有未跟踪 skill 格式阻塞，保持该文件原状。

## 剩余交付门禁

本批 draft 不等于完整 G2/G3 或生产准入。正式客户端类型需在 core release artifact 准入后，使用既有 sync 流程重新生成并比较；不修改准入规则来容纳候选数据库。Hub 合并后依赖 Spoke 必须更新至合并后的共享 SHA。

云端合成数据读回及 API 样本导出已通过，免费额度、保留边界与长期历史导出仍待验证；真实平台终止宽限与请求后冻结、真实模型 provider、活跃部署覆盖及 webext 独立生命周期仍是部署或后续覆盖门禁。AI 原文/长期快照没有被基础 tracing 自动授权。正常 SDK shutdown 的等待窗口不是端到端硬时限或零丢失承诺。

## 资源与权限

本轮 task-owned `inkcre-o11y-db-g1-b0a97f7c` 的两个容器和隧道已停止；`o11y_impl`、`o11y_migration_roundtrip`、历史 `o11y_lab` 与其余实验卷保留。其它三历史实验项目也保持停止。未操作 SVC 开发数据库；未升级套餐、合并或生产部署。真实凭据仅留本地忽略配置，不进入任务证据、提交或浏览器。父任务保持活跃。
