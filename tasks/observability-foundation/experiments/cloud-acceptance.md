# Grafana Cloud 合成接入验收

2026-10-03 使用真实 Python facade/标准 SDK 向用户配置的 stack 发送一次纯合成运行，再用独立 Viewer service account 经 Grafana datasource proxy API 查询 Tempo、Loki 与 Prometheus。没有启用真实业务采集、付费套餐或 Assistant/MCP 功能；账号实际 Free 限额和保留边界仍需部署 owner 核对。

运行 `3e4b0adf-a931-4d29-8bda-778a4ce6c345` 的发送证据见 [cloud-probe.json](evidence/cloud-probe.json)，独立读回与导出见 [cloud-query.json](evidence/cloud-query.json)。读回三个 span，提交与执行独立 trace 的 Link 指向原提交 span，AI chat 保持执行父 span。输入 token 0 的来源为 provider，输出字段缺省且来源 unavailable；Cloud 没有把未知补成零。日志有 job.submitted/job.closed；同一运行实例的三个 operation counter 和 histogram count 均为1，input token总量0，output缺失计数1且不存在output token样本。

配置中 Basic 后必须是 instance ID 与 token 组合的base64，而不是原始 glc_ token。Viewer读取权限与OTLP写入权限分离。凭据仅通过dotenv作为数据读取，stdout与证据不记录headers或token。当前本机Python没有默认CA文件；probe通过标准进程环境变量使用已有certifi可信CA，TLS校验保持开启。

实际首次TLS往返超过一秒，原固定一秒超时导致错误丢弃；改用标准可配置timeout后成功。Trace/Metrics返回200，Logs返回204；仅凭这些响应不声明存储通过，后续API读回才形成结论。服务端relay兼容200/204并仍只处理标准protobuf，实际浏览器relay的逐值ID验证见 [client-real-relay-result.json](client-real-relay-result.json)。浏览器该轮使用合成上游，不能把组合证据写成浏览器直连本stack的实测。

重跑用 `pdm run python tasks/observability-foundation/experiments/cloud-probe.py` 发送新合成运行，再运行同目录 `cloud-query.py` 查询对应运行。发送脚本只显式启用自己的子进程，保持本地 `.env` 的应用开关false。样本API导出不等于全历史、跨保留窗口迁移或厂商备份/恢复已验。
