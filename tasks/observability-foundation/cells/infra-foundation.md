# I-G1：基建可行性

状态：2026-10-03 Sir 已同意 Grafana Cloud Free；按 D10 默认关闭、PG 保留与 vendor-agnostic 进行实现准备，云端准入仍未运行。主 Agent 拥有任务内提案及独立合成实验；运行接入和数据生命周期由部署 owner 负责。

既有 OpenObserve 三信号、Tempo 重启/Link 和五组件 API/Grafana UI 闭环见[前轮](../experiments/README.md)与[数据库/三信号报告](../experiments/convergence-20261003.md)。这些实验有效，但默认自建结论被 Sir 明确的 serverless、scale-to-0 与 SaaS 偏好替代，不再从608MiB快照推断实际运维成本合适。

本轮证实 OO 原始 -1 与来源标记可保留，自动派生 total/cost 仍需按来源解释。官方 SaaS 能力和费用见[修订报告](../experiments/sentinel-saas-20261003.md)。已选 Grafana Cloud Free 为按需开启的后端，OpenObserve Cloud 因零费用约束暂缓；Cloudflare 原生能力按实际 Unit 补充。不恢复默认常驻 Collector，不启动更多产品大全式比较。PostHog 原生三信号已有，但当前成熟度及 AI/普通 Trace 关联限制使其不成为唯一基建首选。

返回消费方是[整体设计](../design.md)与[工作地图](../task-map.md)。剩余准入是目标账户的必要因果/AI查询、导出、三信号、浏览器入口、有界 flush 与费用约束；本地实验不能证明这些云端行为。源端来源/值边界、真实业务故障隔离和覆盖仍由 G2/G3 验收。

所有实验容器和隧道已停止，合成卷随父任务保留，不动 SVC 数据库。标准传播、Job carrier、协调升级及业务 authority 保持，不因后端修订重做已有效的数据库判别。

默认关闭与 PG 保留须由 V0/V3 证明；仅配置 endpoint/token 不能开启，新开关不切换 logging_backend。供应商相关配置/查询留在部署与消费侧，关闭/开启混用不改变 Job 结果。Compose 现有 none fallback 的对齐属于待实现项，不能以任务包完成冒充已修复。
