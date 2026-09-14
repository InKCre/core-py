# CLI Sink — Impact Handshake

2026-09-14；完整 preflight 后的实施基线。等待 Sir 明确“开始”，不把预演或本页视为源码授权。
产品/接口 D-571–D-600、验收 D-601、Pydantic 取舍 D-602/D-603 保持已确认状态。

## From → To

当前只有零散 Core 普通 REST，没有独立 CLI，Job 没有外部请求停止的完整执行链；
部分可信持久数据/typed 值反复经过输入 validator。

本轮交付同仓库独立的 inkcre-cli：通过普通 REST 完成已确认的检索、实体/Resolver、配置和运行管理；
原生 JSON/bytes/multipart 交付内容；Job 停止在 Core 与浏览器 worker 闭合。
CLI 不安装 Core、不访问数据库、不加入 Peer delegation。

## 改动与影响范围

| Owner | 具体变化 | 副作用及不变项 |
| --- | --- | --- |
| core-py app/routes、business、schemas | 普通 REST、必要领域管理接口、动态 schema、内容响应、可信读取校验修正 | 普通 REST 允许 breaking 重整；已存在的 Peer/MCP 消费合同保留，不重写 retrieval 算法。 |
| Core Job / migration / run.py | abort_requested 默认 false、本地执行句柄、集中意图观察、shutdown 清理；显式 rumination Job | 新列是 additive；旧 worker 不消费它，需两端发布。不能把 pending/running/terminal 或 abort/timeout 混为一谈。 |
| extensions/mail | to_thread 清理顺序与原生有限网络 timeout | 取消可能等待实际 I/O/清理；不是强杀线程，也不承诺撤销远端副作用。 |
| ext-reg Python runtime | config/state 的重复校验链收敛，typed 返回值保留 | 不改生命周期、注册或 installed-record 合同；独立 feature、发布后再更新 Core dependency pin。 |
| client-web packages/core | Job DTO 与 AbortController 执行/停止闭合 | 不做新增管理 UI，不把 browser 组件探针宣传为完整 Mail client。 |
| cli/ | 独立 PDM project、lock、src、命令与文档 | Click/Pydantic/HTTPX/PyJWT；复用协议而非 Core 代码，REST 返回只转换。 |
| Core release/automation | CLI 接同一 Towncrier Release PR，独立 main-only PyPI publisher；production Extension build 复用 Toolkit finalize | 不把 CLI 放进 Extension matrix，不再造 release controller；不覆盖已发布 wheel。 |
| Hub / 本地文档 | 只提升真正共享的校验/Job 合同；其余在各 owner 落地 | Hub 修改、ref bump、Spoke-local 变更分开；旧 Organization promotion 不搭车。 |

其中 finalize 是本次 preflight 实测暴露的必要交付修正：正式 Mail 0.2.0 无 installed record，enable 409；
同一 wheel 经已有 Toolkit finalize 后，双 Core 安装/启用 200，真实 IMAP BODYSTRUCTURE/bytes 可读取。
修复是接上已有步骤，不新增安装旁路。Mail 本轮已有 adapter fragment，将用下一正式版本完成交付。

## 实施顺序

1. 核对 main 漂移，在 ext-reg/client-web 使用独立 feature 工作位置，保留现有 dirty checkout。
2. P1 校验边界、P2 Job/取消、P3 普通 REST 按各自 owner 落地，汇合验证。
3. P4 独立 CLI 完整命令面；P5 对应文档、检查、发布接合。具体步骤见 implementation-plan.md。
4. 候选 Preview 与隔离双 Core/IMAP 跑四条真实 CLI 旅程；runtime → Core pin，Core/client-web 同步交付。
5. Core production 新 REST 可用后才首次发布 CLI；在 checkout 外干净 pip 安装复跑，再关闭 unit。

以上是依赖顺序，不授权跨 session 通信。提交、push、PR、合并和发布仍遵循各自明确授权。

## 验证与剩余条件

预演已通过：Mail 取消候选、独立 sdist/wheel 安装、Release prepare/index 隔离、双 Core/IMAP、浏览器数据库
通路、真实 embedding 与 tool call、云端冷启动。详见 preflight.md；这些不是 CLI 已完成验收。

代码落地后运行 Core/CLI/client-web 各自静态 gate 和生成合同，按 acceptance.md 执行四条手工/脚本旅程；
不新增自动化 helper/schema 矩阵。发布后再次确认真实 Registry 安装和 PyPI 安装，不只看 CI green。

无尚未定位的设计或编码 blocker。实际 CLI Preview 要在候选 PR 后创建，PyPI Trusted Publisher 尚需
Human 配置/确认；它们是交付条件，不掩盖成已就绪权限。主环境 AI catalog 为空，验收隔离环境需显式准备
已验证的 Provider/模型/Agent 配置。任何新发现若改变本页产品范围或 owner，再返回讨论。
