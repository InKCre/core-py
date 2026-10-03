# InKCre 可观测性基建

建立适合多 Peer、serverless 与 scale-to-0 的可选观测能力。Sir 已选定 Grafana Cloud Free，要求 vendor-agnostic、默认维持 PostgreSQL 日志，并已授权实施、创建分支、提交、推送与 draft PR。Sir 已进一步授权推进既定验收与 PR 合并顺序，包括正常 Release PR 所触发的交付；没有付费服务或持续生产遥测启用授权。

## 当前交付

首批实现正在完成预览验收与按依赖合并：Python 与 client-web 使用标准 OTel/OTLP，本地开关缺省关闭，PG writer 与 Job 查询保留。Hub #33 已合并；两 Spoke 各自独立更新共享引用至 `7916312`，#124/#125 已退出 draft。core 功能合并后先走既有 Release PR 和 stable 准入，再同步客户端类型与合并。

| 对象 | 当前状态 |
| --- | --- |
| Hub | `main`，`7916312c12cfaf2ee396d7dc1afffee67d4f0721`，[已合并 PR #33](https://github.com/InKCre/docs/pull/33) |
| core-py | [PR #124](https://github.com/InKCre/core-py/pull/124)，源码 `0eba26a`，共享引用提交 `4e4b10e`，基于 `fa23a1c`；默认关闭、三信号、HTTP/Peer/Job/Cron/AI/Agent/来源事件、正式迁移及受控 protobuf relay |
| client-web | [PR #125](https://github.com/InKCre/client-web/pull/125)，源码及预览修复至 `6026b2d`，共享引用提交 `df90755`，基于 `d4c6437`；连接本地开关、三信号、Peer/Job carrier/Link、可选诊断链接与认证 relay |
| Grafana Cloud | Sir 已创建 stack 并配置写入与 Viewer 凭据；API 当前标记为 `free-trial`，不能据此宣称稳定 Free 套餐边界已验。三类合成数据已由 Viewer API 独立读回；Trace/Span/Link、AI unknown/zero、日志和指标均与源输入一致 |

持久行为见 [core-py 部署文档](../../docs/40-deployment/observability.md)和已发布[共享契约](../../docs/_shared/20-product-tdd/observability-contract.md)。任务内旧设计与实验保留其历史语境，不再作为运行事实的第二权威。

## 已验证与收尾

真实隔离 PostgreSQL 已迁移至 `3d9593b0c855`，Python Job 成功/失败/取消与 PG 日志、mixed 开关、三信号及 metrics-only 已验。实际 FastAPI lifespan/readiness/JWT relay 已验。实际 OpenAI SDK 对合成 provider 的流式末块、unknown/zero、并行工具与内容 canary 已验，不等于真实付费模型验收。

真实 Chromium＋PostgREST 验证了直写、执行 Link、异步并发、重定向、JWT 与三信号。真实浏览器→core relay→接收端逐值核对 Trace/Span/Link IDs 已通过；此前 JSON 返回 200 的证据作废，通用 ProtoJSON 会误解 OTLP 十六进制 ID，因此采用官方 protobuf exporter，并明确拒绝 JSON。

- [本轮验收](verification.md)管理具体主张、证据和残余；[客户端报告](experiments/client-implementation.md)给出客户端范围。
- SDK 故障隔离、部分初始化资源回收、原生队列/导出计数已通过独立复验；迁移升级/降级/再升级保留旧 Job/PG 日志并验证容量约束。最终 `pdm run check` 已通过（14 passed、63 skipped，0 类型诊断）。
- core 最终 `pdm run check` 通过（14 passed、63 skipped）。client lint、全量类型检查、build 与 tracked 文件格式通过；完整 `pnpm check` 被用户原有未跟踪 skill 格式阻塞，保持该文件原状。

## 剩余交付门禁

本批实现交付不等于完整 G2/G3 或持续生产遥测启用准入。正式客户端类型需在 core release artifact 准入后，使用既有 sync 流程重新生成并比较；不修改准入规则来容纳候选数据库。Hub 合并后两个 Spoke 的共享 SHA 已独立更新。

云端合成数据读回及 API 样本导出已通过，免费额度、保留边界与长期历史导出仍待验证；真实平台终止宽限与请求后冻结、真实模型 provider、活跃部署覆盖及 webext 独立生命周期仍是部署或后续覆盖门禁。AI 原文/长期快照没有被基础 tracing 自动授权。正常 SDK shutdown 的等待窗口不是端到端硬时限或零丢失承诺。

## 资源与权限

本轮 task-owned `inkcre-o11y-db-g1-b0a97f7c` 的两个容器和隧道已停止；`o11y_impl`、`o11y_migration_roundtrip`、历史 `o11y_lab` 与其余实验卷保留。其它三历史实验项目也保持停止。未操作 SVC 开发数据库；未升级套餐。Hub 已合并，应用交付推进中。真实凭据仅留本地忽略配置，不进入任务证据、提交或浏览器。父任务保持活跃。

## 当前预览验收

PR #124 独立 Heroku/Neon 预览曾临时开启 PG 日志与 OTLP，私密值仅通过 Heroku API 写入服务端，原配置保存于忽略的恢复文件。真实 Chromium 初次读取共享配置被 1.5 秒上限取消，业务 Job 与 PG 错误日志正常；独立 HTTP 读同一合法配置耗时 2.376 秒。客户端 `b64e5eb` 将配置读取上限设为 10 秒，直发/relay exporter 分别为 10/35 秒，处理器多留 5 秒；调用方 flush/shutdown 等待仍 1.5 秒。修复后真实 Job 三信号/Link 经 Cloud 独立读回通过，Pages 预览显示业务终态与 PG 日志。配置 10 秒超时、上游拒连、再次关闭后的业务/PG 保留已验；`6026b2d` 对齐指标标签及秒分桶，Cloud 严格读回通过。真实付费模型未调用。

预览运行配置与共享配置已恢复，新增私密出口变量已移除，见 `experiments/evidence/preview-restored.json`。预览原有显式 logging backend 为 none；临时 PG 日志只用于本次开关/故障验证，不修改生产配置。
