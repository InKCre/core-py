# Hub 契约差异评审

[hub-contract.patch](hub-contract.patch) 保留基于旧 Hub `42f7bad1c61e57b5e0ebf55e27815ddc2ae913fa` 的设计证据。授权实施后已重新基于 `03d0c54` 检查并应用到 Hub 源，提交 `a603b036fd41dae5a471dea24cd7609bb4927bd5`，发布 [draft PR #33](https://github.com/InKCre/docs/pull/33)；两 Spoke 各自独立更新引用。下文的未应用/未授权描述属于此前设计阶段，不再表示当前状态；当前控制见 [packet](../packet.md)。

| 变更对象 | From → To | 影响与边界 |
| --- | --- | --- |
| `20-product-tdd/observability-contract.md` | 无独立观测契约 → 默认关闭/现有日志保留、身份、传播、Job 因果、AI unknown、内容和后端可替换性要求 | Python、TS 及其它 Peer 的共同可观察行为；不承诺当前实现完成 |
| `docs/index.md` | 既有共享导航 → 增加新契约链接 | 只改人工维护区域，生成 SVC 区域保持原样 |
| `20-product-tdd/cross-unit-contracts.md` | 既有合同索引 → 明确观测语义 owner | 引用新文档，不复制整份契约 |
| `20-product-tdd/knowledge-capability-contract.md` | Job 生命周期约束 → 增加观测关联的连接 | 不修改领取、终态、取消、重试或 Cron 语义 |

归位独立判断如下：Hub 拥有跨 Unit 行为；数据库协议 owner 交付持久字段和准入；各 Peer 实现本地 opt-in、SDK/context 与 provider 边界；部署 owner 配置托管采集、存储和查询，按实际缺口使用可选转发组件。W3C 与 OTel 的协议机制由标准依赖拥有，InKCre 只补业务关联和边界。按 D8 改为 SaaS 优先，core-py 拥有相关部署接入文档；具体供应商、配方和位置不进入 Hub 契约。 D10 已获用户同意选用 Grafana Cloud Free，但公共契约仍不绑定它；关闭态保持原日志，开启也不自动停用 PG。

新增 `-1`/来源标记实验与 SaaS 文档判别见[本轮报告](../experiments/sentinel-saas-20261003.md)，目标 Cloud 尚未验收。既有支持证据是标准 Python/JS 互操作、实际旧 Python/TS 数据库消费者与 readiness、carrier 容量、OpenObserve 的 AI 缺失值反例、Tempo 重启前后的因果/属性保留，以及五组件 Grafana 诊断闭环。它们见[实验记录](../experiments/README.md)。patch 要求的真实业务故障隔离、浏览器传播、内容出口、正式 migration/完整启动和历史导出仍需实现验收；不能用文档发布替代这些证据。

D10 增加本地显式 opt-in，关闭时不捕获新 carrier，更新已有 Job 仍保留字段；撤销 PG writer 退役和保留旧日志需再次授权内容模式的约束。carrier 公共字段/容量保持；未发布配置由单一 base URL 改为按信号完整 URL，允许客户端专用受限写入与受控转发，均已进入 patch，避免跨语言各自发明。SQL DDL、配置初始化命令、生成类型、SDK 生命周期和协调升级步骤由[实现输入](shared-contract.md)细化，不进入公共行为文档。当前后端的版本、资源和 Link flags 损失只在部署实验中记录，不把某版本存储缺口固化成共享标准。内容长期保存和生产预算仍等待实际需求，不从本差异推导永久证据或生产部署授权。

2026-10-03 已对原 Hub 工作树运行 `git apply --check`，并在临时目录应用后核对新增链接、四个文件范围及生成 SVC 区域，均通过；未把 patch 应用到源仓。正式落地前重查基线与本地差异。交付依次是 Hub 源、经明确指令提交/推送、Spoke 引用、各 Spoke 实现，分别保持独立变更边界。

仓库 AGENTS 明确要求源码修改批准，并要求提交仅依明确 Human 指令。当前已授权的任务包与隔离实验足以生成和验证此差异；本文件不自行扩大为修改应用、提交、推送或生产发布的授权。
