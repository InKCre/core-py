# CLI 产品设计

操作范围已获 [D-573/D-575](../../decisions/D571-D580.md) 确认；本页将范围映射到可观察行为，尚未冻结全部命令参数与
全部行为细节。当前阶段和下一复核面只由 [packet](packet.md) 维护。

已确认的命令分组与待复核的参数示例见 [命令结构](command-surface.md)。

## 已确认操作范围

| 调用者要完成什么 | 本轮提供的能力 |
| --- | --- |
| 从线索找到并取用信息 | 词法、语义、图导航检索；批量实体记录及可选 raw/hydrated content；solved content 等解释通过动态 Resolver 方法读取 |
| 把明确的信息改动交给 Core | GraphForm 新增 graph，以及已有 Block/Relation 的原地编辑、删除；沿用 info-base 的持久化能力 |
| 运行收集或整理并保持执行控制 | 显式 collection/backfill 和 organization 均提交相应 Job；提供状态查看、限时等待及主动停止 |
| 查看参与运行的节点并使可唤醒节点恢复服务 | Peer 列表/详情、状态、唤醒；支持边界见下文 |
| 管理 Extension | 列表/详情、安装/卸载、启用/禁用；必要的配置与合同发现服务实际安装使用 |
| 配置收集来源 | Source 列表/详情、创建/编辑/删除；发现 Source type 与其配置/collect/backfill schema |
| 安排定期收集或整理 | Cron 列表/详情、创建/编辑/删除、启用/禁用；选择 Job type、参数、超时和 schedule |
| 管理整理所用 Agent 与行为配置 | Agent definition 发现/创建/读取/编辑/删除；通过 deployment config 管理 Organization behavior config，包括 Agent 选择 |

列表、详情、类型与配置合同不是额外产品主线；它们让调用者能完成已获批的管理操作。也不据此把所有数据库
表变成 CLI CRUD，或增加用户、租户和权限管理。Agent-friendly 的研究方向见 [research](research.md)。

D-591 将已有的同类校验边界问题纳入本 unit 配套修正，范围与证据见
[校验边界修正](validation-boundary-correction.md)。这不是额外 CLI 功能，不改变本页的产品操作范围。

D-595 明确上述任务提交与实体修改边界。Block 是整理的输入，不使整理变成 Block 领域操作；既有同步执行
方法或 Peer inbound 也不决定 CLI 的受理方式。准确方案见 [Job 入口与实体修改](organization-write-rest.md)。

## 从已有模型自然得到的边界

CLI 配置的是连接哪个 Core REST 服务。这个服务属于一个 Peer，但 Source、Cron 等持久配置是 deployment
共享的。相反，Extension 启用/禁用影响选定 Peer 的 runtime；返回信息应让调用者看清作用对象，不能把一次
disable 描述为全 deployment 停止运行。安装记录、启用意图与实际运行也不能合成一个状态。

Source 负责收集配置与游标，Cron 保存 schedule 和 Job 模板，Job 表示一次执行。CLI 分别操作这三个对象，
不把 Cron 配置放回 Source，不把编辑 Source 自动变成启动 collection，也不把定时配置写成本机 crontab。
删除 Source 的配置不意味着删除已经收集的信息；关联引用和延迟读取的影响需在删除合同设计中核对。

Cron 沿用 Core 的时区、错过不补跑和并发 occurrence 语义，不由 CLI 另建 scheduler。Job 的创建回执只确认
执行机会已持久化；实际 pending/running/terminal 状态从 Core 查询。组织 Job finished 不证明 Agent 的语义
判断正确，也可能没有 graph 写入。输出必须保留这些既有含义。

等待者拥有本次观察预算，Job 拥有独立的执行期限。等待结束可正常返回 pending/running 等实际状态，不代表
Job 失败或取消；调用者使用同一引用继续观察或主动停止。Agent definition 管理不隐含新增 Agent 会话产品；
Organization config 也不复制 definition 中的 prompt/model/tools。配置的保存位置与具体字段保持现有 owner。

管理配置和读取动态合同依赖当前 Core 的 capability owner。CLI 不内置每种 Extension、Source 或 Organization
的配置清单；如何按需发现并构造输入在 Technical 阶段明确。

## Peer 唤醒，D-574 已确认

现有 Peer 状态是能力 advertisement 与 lease，尚无 wake 操作。Lease 过期只表示未在该时间范围内续期；
无法区分 scale-to-zero、关闭、失联等原因。状态查看应报告实际已知事实，不猜测休眠原因，也不主动续写
其它 Peer 的 lease。

本轮覆盖由外部 HTTP 请求触发冷启动的 Core 服务，例如现有 Render Free 部署。使用现有 `GET /readyz`，
宿主平台因请求到达而启动服务，Core 返回自身就绪状态；不存在专门的 `/wake` handler。CLI 复用普通 HTTP
调用并等待实际就绪，无需平台 SDK 或独立 wake protocol。唤醒只使服务可用，不附带执行 collection/organization
或补发错过的 Cron。已可访问时可正常完成，不必制造“已经醒着”的错误。

初始配置的 Core 自己也可能休眠。因此访问/等待这个已知地址不能先依赖一次 Peer 列表查询；醒来后才能
读取 deployment 中的其它 Peer。CLI 仍只使用普通 Core REST，不通过过期 lease 的 Peer delegation 唤醒目标。
目标按 D-592 使用已配置的 CLI connection；保留直接请求 /readyz 的轻量操作，不按任意 Peer ID 自动发现地址，
不建立独立唤醒服务或调度机制。通用 Peer 唤醒尚未规范化，不由本单元补齐。

本轮不承诺启动已关闭的桌面应用、Android 应用或机器，也不接管 Render/Heroku/Docker 的部署控制。
没有 HTTP 唤醒路径的 Peer 可以被查看，但不能仅凭一条 Peer row 使其启动。产品能力边界已确认，超时和
等待过程的呈现随命令合同落实。

## 验收应增加的场景

在原有信息取用与显式操作旅程之外，加入从 CLI 安装/启用 Extension、按真实 schema 创建 Source、配置
collection Cron、观察产生的 Job，以及配置现有 Organization Cron 的真实链路。另覆盖休眠 Core 的访问/
唤醒与后续 Peer 状态查看。D-575 还要求覆盖限时返回后继续观察/停止 Job，以及管理 Agent definition 并在行为
配置中选择它。D-595 增加针对指定 Block 创建整理 Job 的链路，以及原地修改/删除 Block、Relation 后重新读取
实际效果；不能以 HTTP 受理冒充整理完成。准确数据、环境、清理方式和验收终点在 Acceptance 阶段冻结，不从本建议推导
新增自动化测试或扩大为全部 hosting platform 验收。
