# Grafana Cloud 合成接入验收

2026-10-03 使用真实 Python facade/标准 SDK 向用户配置的 stack 发送一次纯合成运行，再用独立 Viewer service account 经 Grafana datasource proxy API 查询 Tempo、Loki 与 Prometheus。没有启用真实业务采集、付费套餐或 Assistant/MCP 功能；账号实际 Free 限额和保留边界仍需部署 owner 核对。

运行 `3e4b0adf-a931-4d29-8bda-778a4ce6c345` 的发送证据见 [cloud-probe.json](evidence/cloud-probe.json)，独立读回与导出见 [cloud-query.json](evidence/cloud-query.json)。读回三个 span，提交与执行独立 trace 的 Link 指向原提交 span，AI chat 保持执行父 span。输入 token 0 的来源为 provider，输出字段缺省且来源 unavailable；Cloud 没有把未知补成零。日志有 job.submitted/job.closed；同一运行实例的三个 operation counter 和 histogram count 均为1，input token总量0，output缺失计数1且不存在output token样本。

配置中 Basic 后必须是 instance ID 与 token 组合的base64，而不是原始 glc_ token。Viewer读取权限与OTLP写入权限分离。凭据仅通过dotenv作为数据读取，stdout与证据不记录headers或token。当前本机Python没有默认CA文件；probe通过标准进程环境变量使用已有certifi可信CA，TLS校验保持开启。

实际首次TLS往返超过一秒，原固定一秒超时导致错误丢弃；改用标准可配置timeout后成功。Trace/Metrics返回200，Logs返回204；仅凭这些响应不声明存储通过，后续API读回才形成结论。服务端relay兼容200/204并仍只处理标准protobuf，实际浏览器relay的逐值ID验证见 [client-real-relay-result.json](client-real-relay-result.json)。浏览器该轮使用合成上游，不能把组合证据写成浏览器直连本stack的实测。

重跑用 `pdm run python tasks/observability-foundation/experiments/cloud-probe.py` 发送新合成运行，再运行同目录 `cloud-query.py` 查询对应运行。发送脚本只显式启用自己的子进程，保持本地 `.env` 的应用开关false。样本API导出不等于全历史、跨保留窗口迁移或厂商备份/恢复已验。

## PR 预览中的真实 Job 链路（2026-10-03）

本轮使用 PR #124 的 Heroku Core 与隔离 Neon/PostgREST，临时启用 PostgreSQL 日志和
私密 OTLP 出口，部署身份为 `19c771e2-e728-4299-b81a-9d7c387b207b`。Chromium 加载
client-web 的真实业务模块，通过 PostgREST 提交最多处理一条记录的 lexical maintenance
Job，由远端 Core 领取执行；这不是付费模型调用，也不是在 Pages UI 中提交 Job。
Pages 的实际预览随后独立显示成功 Job 和失败 Job 的 PostgreSQL 日志。

第一次和第二次运行暴露了实际问题：浏览器 1.5 秒的共享配置读取上限取消了合法请求。
独立 HTTP 读取耗时 2.376 秒；业务成功和错误日志不受影响，但遥测未初始化，因此这两轮
不算链路通过。客户端提交 `b64e5eb` 将读取上限调到 10 秒，直发 exporter 为 10 秒，relay
exporter 为 35 秒，以容纳服务端最多 32 秒的转发预算和网络余量。处理器多留 5 秒；调用方
flush/shutdown 等待仍为 1.5 秒，不承诺页面退出排空。

修复后的 Job #6 成功，#7 按预期因无效参数失败并留下 1 条 PG 日志。
`preview-query.json` 通过独立 Viewer API 读回两个服务的三信号：提交 Trace
`bddd7663505c46d94e35c215f4b7fff2`，执行 Trace `61e1f23b243c2eaf36856cd4be07da1a`，
执行 Span Link 精确指向提交 Span；`job.submitted`、`job.started`、`job.closed` 齐全，
浏览器提交与 Core 执行的时延指标均存在。初次读回发现浏览器的 `inkcre_operation` 和 Core 的 `operation` 标签不同；
JS 默认秒分桶也不能细分短请求。最终客户端 `6026b2d` 将时延指标标签与显式秒分桶
对齐 Core，日志属性不变。历史 `preview-query.json` 保留当时两种标签的真实读回，
最终指标另由 `preview-metric-query.py` 严格核对统一标签、全部桶边界及 count/sum。

`preview-ui.json` 记录实际 Pages 预览中的成功状态与错误日志展示。浏览器 SDK 的部分
fetch 出口在收到 200 后出现 `net::ERR_ABORTED` 事件；已查 SDK 的成功分支不消费
响应体，但未据此断言这些事件的唯一原因。三信号是否成功以
Cloud 独立读回为依据，不把网络事件数量当作精确导出或丢失账本。

账号 frontend settings 当前返回 `plan=free-trial`，见 `grafana-plan.json`。官方 Free
页面列出 10,000 活跃指标序列、每月各 50 GB 日志/Trace 及 14 天保留，但这不证明本账号
已经结束试用，也不等于实际限额行为已验。本轮没有升级套餐或开启额外托管功能，持续
生产 opt-in 仍需确认稳定 Free 状态及平台生命周期约束。

证据文件均位于本目录的 `evidence/`。真实凭据只经本地 Keychain/dotenv 和 Heroku API
传输；恢复快照在被忽略的 `runtime/`，不进入归档。

故障与恢复矩阵也已执行：共享配置请求始终不返回时，初始化在 10015.6ms 后停用遥测，Job #8 完成，#9 失败并保留 PG 日志；将预览 OTLP 出口切到本机拒连端口后，三信号 relay 返回 502，Job #10 仍完成，#11 的 PG 日志保留。仅关闭遥测后，#12 完成且 carrier 为 NULL，#13 的 PG 日志保留，浏览器无 OTLP 请求。最终指标严格读回 count=1、sum=0.0263s，全部显式桶边界与 Core 一致。
