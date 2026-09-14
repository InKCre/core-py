# 实现前预演

状态：2026-09-14，完整 preflight 已完成。D-571–D-603 的产品、接口和验收基线不变；
具体代码落点、真实验收环境与交付顺序已收敛，可以进入 Impact Handshake。
这不是实施完成、产品验收通过或发布授权。

## 结论与证据入口

| 计划 | 已闭合的准备 | 证据 |
| --- | --- | --- |
| P0 | Core feature 基线、ext-reg/client-web origin/main、声明开发环境恢复；不重置 dirty checkout 或共享 DB | [环境](preflight-environment.md) |
| P1 | 逐调用点区分输入、一次原生 Pydantic 类型恢复、typed 传递；不自建递归 decoder | [调用链](preflight-call-sites.md) |
| P2 | 两端 worker 取消、shutdown、条件终态、Agent 传播；Mail 清理替代实验通过 | [调用链](preflight-call-sites.md)、[runtime 实验](preflight-runtime.md) |
| P3 | Manager 事务签名、PATCH omitted、catalog-only 输入、路由顺序和现有 Peer 消费者 | [REST 接合](preflight-rest.md) |
| P4 | 独立 PDM/lock、sdist→wheel→干净环境，Core 不可导入，Click 正常退出/compact JSON | [工具链](preflight-toolchain.md) |
| P5 | 复用 ReleaseProject/Towncrier 的 CLI 独立版本与 Git index 隔离；修正发布构建缺口的路径得到验证 | [工具链](preflight-toolchain.md)、[环境](preflight-environment.md) |
| P6 | 双 Core/同 DB、真实 Dovecot、Mail 安装/启用、浏览器→PostgREST、真实 embedding/tool call、云端冷启动 | [环境](preflight-environment.md) |

原先的 SSH reset、旧 image 快照已经收敛；它们的真实时序保留在环境页，不再列为当前 blocker。
Pydantic 方案已由 D-602/D-603 确认，不以逐调用点调查重新打开同一个决策。

## 预演带来的必要改动

最重要的新发现是正式 Mail 0.2.0 wheel 缺少 installed record，enable 真实返回 409。
Preview 构建已使用现有 Toolkit finalize，production publisher 却没有。
隔离实验复用 finalize 后，Core A 安装、B 启用和真实 IMAP 读取均成功。
[实现计划 P5](implementation-plan.md) 因而补入同一构建步骤的复用；不降低 runtime 合同，不覆盖正式旧 wheel，
不扩大为 release framework 重写。这项 source correction 等待本次 Impact Handshake 后的实施授权。

另两项修正是具体实现落点：Resolver reflection 在 resolver/main.py；显式整理 Job 调用
RuminationBehaviorResolver.ruminate_local。APScheduler shutdown 的 wait=True 不会等待异步清理，P2 必须
先停止接纳并排空本端执行，再关闭资源，而不是依赖这个参数。

## 实施与交付条件分开

目前没有尚未定位、会推翻设计的编码 blocker。仍存在正常的交付前置：

- 候选 PR 创建后才有本 unit 的 Preview；必须对实际候选运行四条 CLI 旅程。
- ext-reg runtime 修改需独立发布并由 Core pin；Core 与 client-web worker 均交付后才算停止协议完整。
- 正式 Mail 新版本必须包含 finalize 和本轮 adapter 修正，并实际从 Registry 安装/启用。
- PyPI Trusted Publisher 仍需 Human 配置/确认。先使 Core 新 REST 可用，再发布 CLI 0.1.0 并干净 pip 复跑。

本次不声称上述交付已完成，不发布包，不重置真实用户数据。
下一步是 [Impact Handshake](impact-handshake.md)；Sir 明确“开始”后才进入源码实施。
