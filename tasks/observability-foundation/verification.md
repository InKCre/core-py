# 跨工作线验收

本文件汇总整个任务的交付主张、判别性证据和残余；预期行为来自已接受方向与已发布到 Hub draft PR #33 的共享契约。它不替代各仓检查，也不凭测试通过授予发布或范围缩减权限。

## 主张与证据要求

| ID | 需要证明的结果 | 判别方法与观察来源 | 当前状态 |
| --- | --- | --- | --- |
| V0 | 默认行为与显式 opt-in 正确 | 默认配置、已有 endpoint/凭据但开关关闭、显式开启、故障、改回关闭后重启/连接初始化五种状态，核对 PG 写入/Job UI；关闭态无新增 provider/后台队列/OTLP 请求或传播捕获。Compose 无值默认 PG，显式 none/logtail 保持 | 已验：关闭时即使配置出口也无新增线程/发送，默认 PG；实际应用两种模式 ready/关闭通过；Compose 默认已对齐 |
| V1 | 同步 Peer 调用因果关系正确，直接数据库访问的盲区被准确呈现 | 用真实浏览器/HTTP 传输发起受控操作，独立后端读回 trace/span/Peer/能力关联；PostgREST 客户端 span 不算服务端 SQL 证据 | 真实 Chromium/Peer 与真实 core relay protobuf 已验；Trace/Span/Link ID逐值一致。Cloud 合成提交/执行/AI 三个 span 与 Link 已独立读回 |
| V2 | 提交与另一 Peer 的 Job 执行可关联，重启不依赖内存上下文 | 提交后重启发起 Peer；另一执行 Peer 领取；核对持久提交上下文、执行 Span Link 和 Job 终态。覆盖 Python/TS 生产者与执行者、Cron、旧 Job 及开→关/关→开/关→关；关闭端创建 NULL，领取/关闭保留已有 carrier | 正式 migration、实际 Python/TS Job和mixed开关已验，关闭端保留carrier。独立迁移升级/降级/再升级及容量约束已验；生产协调升级未执行 |
| V3 | 新增观测开关不改变现有 PG 日志能力 | 开关关闭/开启/后端中断/再次关闭时，从真实 Job 页核对当前与历史 PG 日志、job.<id>、排序分页；新诊断链接为可选，旧 writer 不自动停写，原日志 trace_id 不替换为 OTel ID | Python真实Job/PG日志在开启与关闭路径保持；客户端Job页入口保持并有UI烟测。生产历史数据分页仍待部署验收 |
| V4 | AI 耗时、结束原因、usage 与步骤关系可信 | 对受控非流式、流式末块、usage 缺失和并行工具案例比较 provider 原始回包与导出数据；再用授权 preview 验证一个真实 provider。未知不记零，估算成本不冒充账单 | 实际 OpenAI SDK＋合成provider经生产adapter/Agent已验：31span/13HTTP请求，usage-only末块、重复累计、unknown/zero、并发错误取消。真实外部provider尚未调用 |
| V5 | 新增 OTLP 基础模式没有意外内容副本，采集权限不等于读取/管理权限 | 合成敏感 canary 经过请求、异常、工具结果与 SQL 参数路径后，检查实际导出数据；验证采集入口及读者边界。PG 按原配置保留，不能以此宣称整个部署无原文。新增内容模式另验保留、截断、删除与 blob 访问 | 实际OTLP出口canary与受控字段已验；relayJWT、私密头、256KiB/并发4/按信号有界超时已验；SDK内部指标View/exemplar去敏已验。旧PG原文行为保持 |
| V6 | 遥测不可用不改变业务成功、失败、取消和资源关闭语义 | 同一受控负载对比正常与断开 SDK→SaaS 和实际存在的中间转发；检查数据库业务终态、响应、队列/内存上限、丢弃计数和恢复；不可用时不能阻止应用 ready | 正常/慢接收/拒连、真实Job成功失败取消、metrics-only已验；8项SDK故障注入通过；1024条积压产生原生 queue_full 计数；已记录SDK并发误差，不能用作精确损失账本，最后metrics回收export失败 |
| V7 | 可更换后端并保留必要的诊断能力 | 仅改标准 endpoint/认证配置，将同一采集样本改投第二个兼容后端，业务采集/Job schema 不改；按 Job/Trace/AI 字段查询，核对 links；另做历史数据导出读回与配置迁移清单。只收到 OTLP 不能算通过 | 历史第二后端实验保留，新增实际浏览器/core三信号标准PBF已验；目标Cloud必要 Trace/Link/AI 字段、日志/metric查询及样本导出已通过；长期历史导出仍未验 |
| V8 | 托管接入符合 scale-to-0 与当前零新增观测费，可维护和迁移 | 验 SDK 直发与短生命周期 flush/冻结、无 scrape 唤醒、应用附加计费时间；确认实际 Free、无收费依赖，量化摄取/查询/保留额度与限额失效，验删除/导出/配置重建和供应商恢复范围。自建时另验冷备与资源 | 实际stack已创建；Viewer查询API三类均200，写入认证已修正，实际三信号存储读回通过。默认无常驻Collector/scrape；真实免费套餐额度及平台freeze/终止宽限未验 |
| V9 | 整个实际运行集合有明确覆盖结论 | 按 Unit/部署列出业务入口、传播、采集和查询证据；Source/Organization/Storage、各客户端及官方运营边界逐项验收或由 Sir 明确范围 | 首批点位已实现，覆盖表见部署文档；webext独立生命周期、非Agent直接来源事件与活跃部署逐项仍未通过 |
| V10 | AI 长期证据符合确认后的产品承诺 | 若纳入：删除/改变当前源数据后仍能按保存契约复核当时输入与引用；核对业务结果 owner、版本与删除语义。Trace 全采样不算持久证据保证 | 维持诊断/来源关联与原文默认关闭；没有承诺或新增长期快照，具体产品需求另行确认 |

## 当前实现证据（2026-10-03）

`experiments/evidence/foundation-probe.json`、`runtime-probe.json`、`runtime-probe-metrics-only.json` 与 `application-probe.json` 覆盖真实SDK传输、Job/PG与应用生命周期。`experiments/client-browser-result.json` 与 `client-real-relay-result.json` 覆盖真实浏览器/数据库与最终protobuf relay；旧JSON 200不再构成ID保真证据。AI细节见 `ai-instrumentation-notes.md`。机械检查和Cloud结果在收尾时更新，不将请求200混同于存储读回。

## 执行与可信范围

首个受控业务旅程是“Peer A 提交 Job → Peer B 执行 Agent → 能力调用 Peer C → 模型/工具 → 结果与引用”，并增加浏览器本地执行这一对等方向。不要通过强制所有操作经过 core-py 构造一条看似完整的链路。

业务结果以原有 API/数据库状态及界面为观察来源；导出是否成功以接收端查询读回为依据；Token 以已知 provider 回包为对照。构造回包的脚本和消费代码不能互相抄字段后自证完整，至少覆盖流式 usage-only 末块及 unknown 的真实边界。

每次有效运行保留精确源码/镜像/规范版本、拓扑、合成输入标识、查询或 UI 读回、负载参数、结果和残余；原始大日志放在该次实验的任务内目录，入口只保留判断所需摘要。不保存真实凭据和未经授权的生产内容。

先运行最窄、能否定主张的检查。共享数据库迁移、并发领取、跨进程传播和故障隔离可需要真实 disposable PostgreSQL 与传输；不增加映射/私有 helper 的镜像测试。仅整理任务包时检查链接、状态归属及 whitespace，不运行全仓 `pdm run check`。

## G1 历史收敛与 SaaS 修订验证

2026-10-03 较早的数据库/三信号补充实验在原自建假设下曾满足 G1 退出条件：公共形状和 owner 已明确，真实旧消费者/准入已判别，三信号可在独立 API、Grafana proxy 与实际 UI 查询。独立 advisor 复核未发现阻挡进入实现的设计缺口，建议结束选型实验。V0—V10 的任务级实现验收没有因此整体通过。Sir 随后明确 serverless/scale-to-0，D8 重开部署后端准入；本轮 -1/来源标记实验和官方 SaaS 文档只支持修订方向，不替代目标 Cloud 验收。

脚本语法、归档 JSON/JSONL、本地 Markdown 链接/围栏、patch 和工作树隔离由最终检查记录于 `experiments/evidence/convergence-20261003/packet-check.json`。Hub patch 对源仓只读 `apply --check`，并在临时副本应用核对四文件范围、链接和生成 SVC 区域。没有为任务包运行全仓 `pdm run check`。

前轮独立归档核对确认 AI absent/zero/explicit、4096 spans 丢弃总数、Tempo 重启前后属性/Links；flags 丢失保留为失败项。本轮数据库/独立 API/proxy 由脚本断言，UI 由浏览器可见状态单独核对，资源结束状态另查 Docker 与 SSH sockets，不以脚本退出零替代语义判断。

## 重验与结束条件

更换 SDK/GenAI semconv、后端版本、字段映射、部署网络、采样/内容策略、Job carrier 或结果保存规则后，重验受影响的 V 项。源码静态结论不能升级为部署证据，开发机结果不能自动升级为生产容量结论。

当前证据覆盖真实候选应用＋隔离数据库/浏览器，以及目标 Grafana Cloud 的合成样本读回，详见 [Cloud 验收](experiments/cloud-acceptance.md)。这不代表生产业务、真实外部模型或全活跃部署覆盖。G1 已收敛，G2 首批集成已运行；G3 仍需补齐免费额度/保留/平台生命周期和覆盖，V10 依具体产品承诺确定。任何不适用项必须说明条件与决定 owner，不能用未执行或失败代替不适用。

任务关闭还要求持久文档归位、各仓交付/回滚关系明确、历史数据与实验资源的去留有依据。仍有依赖用户事实或授权的动作时，报告具体残余，完成独立可推进工作，不把父任务标为完成。

本次 SaaS 修订的语法、链接、证据、Hub patch 与资源检查记录在 `experiments/evidence/sentinel-saas-20261003/packet-check.json`；原报告保持历史时间边界，不覆盖前轮证据。

历史 D10 阶段只做显式 opt-in、PG 保留和 vendor-agnostic 候选差异的任务包/Hub patch 静态检查；当时未运行新应用实验。当前 V0/V3 结论以本轮实现证据为准。检查见 `experiments/evidence/sentinel-saas-20261003/opt-in-packet-check.json`。

## 预览交付补验

真实 Chromium 业务模块→PR #124 PostgREST→Heroku Core Job 执行→Grafana 三信号已闭环，提交/执行 IDs 与 Link 经 Viewer API 独立核对，实际 Pages 预览已显示业务终态与 PG 日志。第一次 1.5 秒配置读取超时被保留为失败证据，客户端修复后通过。精确运行范围与 Free 试用状态见 [Cloud 验收](experiments/cloud-acceptance.md)。此项不冒充 Pages UI 发起 Job、真实模型、长期保留或生产平台完全验收。
