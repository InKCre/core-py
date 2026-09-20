# 实现计划（实施前历史基线）

P1–P4 与 P5 的 Preview 部分已由 [core-py#111](https://github.com/InKCre/core-py/pull/111) 实现并验收。
本文保留计划快照；当前状态与剩余授权边界见 [packet](packet.md)，执行证据见
[implementation-evidence](implementation-evidence.md)，当前实现合同见
[Agent Query Sink TDD](../../../../docs/30-unit-tdd/agent-query-sink.md)。

依据 D-611–D-631 与已确认的 [验收方案](acceptance.md)。领域 owner、controller/service 和文档 authority
修正已纳入下列步骤；注册机制的补充源码核对见 preflight-evidence.md。影响边界见
[Impact Handshake](impact-handshake.md)。
当前 branch 为 feat/agent-query-sink，起点 676886a；实施前重新核对 main 与 working tree，不清除 parent packet。

## 依赖次序

```text
P0 关键预演与设计修正核对（已完成）
 → P1 读取能力回归领域 + Tool controller / schema 接合
 → P2 AgentQuerySink + Job + 结果交付 + catalog
 → P3 实例 route、运行时 schema 与 CLI
 → P4 文档 authority 纠正、Hub 准则、release fragments 与机械检查
 → P5 preview 黑盒验收 → 获授权后发布与 production 消费验证
```

这是工作依赖，不另切 unit；不要求每个文件串行完成，也不授权跨 session 通信。预计只改 core-py 内
Core 与 cli 两个项目，不新增依赖、不改 client-web/ext-reg。D-631 增加 Hub meta 文档 authority 准则，
按 Hub-first 流程分离 owner 和提交，不为了新功能宣传而写入所有 Hub capability 文档。

## P0：已完成关键预演与验收准备

见 [preflight](preflight.md) 与 [实测记录](preflight-evidence.md)。动态 route/schema、读取工具依赖、
取消与结果收尾、catalog 收敛路径已核对；真实 corpus 与目标模型协议握手已准备完成。
新功能 preview 要在实施后生成，不能将现有基线环境 ready 等同于新功能验收通过。
D-630 保留普通函数 Tool controller，因而不需要让注册器支持 classmethod 或改变单输入模型约定。
源码核对已确认现有注册机制适用；移动后的实际冷启动/import 路径必须在 P1 验证，不能在文件尚未
移动时声称已跑过。D-631 的文档 owner 清单与变化传播检查见 documentation-authority.md。

## P1：移动已有能力，不复制一套查询工具

按 D-629 将六个读取能力和对应输入 schema 迁回各自领域：InfoBaseManager 拥有 retrieve/get_entities；
GraphNavigationRetrievalManager 拥有邻域/路径/连通性；Resolver 领域拥有内容方法发现与调用。
禁止创建 app/agent_tools 或等价中央业务集合。保持 exact IDs 与公开结果语义，schema 去掉 Organization
偶然命名。注册声明与必要边界投影随领域放置，不强迫普通领域调用接受 Agent Tool 消息类型。
按 D-630 保留 controller/service 分离：注册普通 Tool handler，由其调用领域方法；不对业务类方法
机械叠加工具装饰器，也不为满足单 input model 注册要求改造 service 签名。
写入工具继续归原 owner，显式 bootstrap 加载同一 AgentManager registry。
具体拆分如下；这是职责安排，不要求每行新建文件或增加一层调用。

| 领域 | Service 工作 | Tool controller 工作 |
| --- | --- | --- |
| InfoBase | retrieve 组合既有 lexical/semantic；get_entities 复用实体 services | 接受既有工具输入并投影结果，不把 JSON-only 限制放入业务方法 |
| Graph navigation | 复用已有邻域、路径、连通性方法；仅补必要的实体邻域选择 | 选择对应入口、参数接合与结果投影，不复制图遍历 |
| Resolver | Manager 拥有方法发现/分派，Resolver 实例执行内容读取 | describe/invoke 工具合同、动态 schema 与输出表示；不复制方法 registry |
| Agent Query | Sink 拥有回答提交合同及结果收尾 | submit_query_result 接合；不直接写 Job 或 graph |

控制器及其输入 schema 随领域组织，不从 service 反向导入 controller。组合根显式加载各领域工具，
避免业务包 __init__ 为导出普通类型而隐式加载所有工具/Organization。更新旧调用者与常量导入，
不保留 Organization 作为通用工具发现入口。可共用的纯序列化机制使用现有 Agent 基建，不能借此
重新建立跨领域工具业务集合。
清除读取路径对 OrganizationError 等写入合同的偶然依赖，不搬整包形成转发层。静态检查全部引用，再
用实际 Tool 发现和一次原 Organization 运行证明注册完整。现有 bytes 限制按 D-625 保留。

## P2：一个 Sink 实例，一种 Job 合同

SinkBase hooks 改为默认 no-op；保留 app 参数和 MCP override。SinkManager 补本地实例访问，并将
同实例 enable/disable/config update/delete 管理操作串行，修复预演已复现的启停交错；关闭复用内部
操作，shutdown 不清除持久 enabled intent。不锁运行 Job，不引入分布式锁或 reconcile/snapshot/rollback。
AgentQuerySink 拥有 config.agent、普通 submit_query_result 和执行结果提取；类型级 JobHandler 在
bootstrap 注册一次，不随每个实例重复注册。Job parameters 引用 sink 和 query，预算复用 Job 字段。

受理路径复用 JobManager.create，claim 前复用本地 Sink 和 AgentManager.can_execute；领取后执行
AgentManager.run 并 await Turn。按 D-622/D-627 收尾，普通返回、预算、无提交、异常/取消的映射由
Query owner 处理，不改 Job 通用状态机。输入只在真实边界验证，工具结果不再经过一遍业务校验。

同步 runtime type 注册与必要 built-in Job profile，检查 db init/ready 对 catalog 的实际要求。复用
已有 sinks/jobs/agents 表，不预设 schema migration；若 catalog-only 更新需要维护部署 manifest，
按现行工具生成而非添加新表或绕过 readiness。Sink instance/Agent 不被 seed 自动创建。

## P3：实例 endpoint 与独立 CLI

AgentQuerySink 启动时挂载自己的 POST /sinks/{id}/query，关闭时只移除自己的 routes，并处理 FastAPI
OpenAPI cache。沿现有普通 Core REST 认证依赖，不改成 MCP PAT，也不引入 Peer delegation。
创建 Job 后返回 202/Job/Location，不 await Agent；generic /jobs 仍独立。

cli/ 新增 sink 管理组与 query 命令，复用现有 Click/Pydantic 输入、HTTP、动态 schema、分页与文件输出
机制。CLI 不 import Core，不复制 prompt 或业务结果校验。核对 Sink 列表与 type/config schema 的真实
REST 形状，需要的分页按已有 REST 规范接合，不能给未分页接口加无效 CLI 参数。
动态 query --schema 消费启用实例的运行时路径，不以 checked-in 静态 OpenAPI 代替运行事实。

## P4：文档、检查与发行意图

文档按 owner 更新：Core 本地 Sink/REST/Agent 工具边界，使用文档内一份推荐 AgentForm，cli/README
提供完整接入步骤并引用模板。删除被迁移的旧 owner 说法，不重复维护工具说明或 prompt。
落实 [controller/service 文档修正计划](../../documentation-promotion/spoke-unit-tdd.md)，在既有架构
authority 中说明分层，并由 Agent subtree AGENTS 引用；不以新增规范文件代替清理含糊的旧说明。
同时落实 [D-631 文档 authority 纠正](documentation-authority.md)：迁走消费者文档中的依赖规范，
清理旧 Rumination/Agent 合同副本；长期判断准则归 Hub meta，具体实现合同留对应 Spoke owner。
文档修正按以下依赖顺序推进，可与对应代码同步而非全部推迟到 P4 末尾：

1. 逐项核实 documentation-authority.md 的 claim/owner，先明确现行合同，再迁移过期或越权声明。
2. 在 Hub source 的既有 ownership 文档中落长期准则，skill 只引用；Core 架构文档落 controller/service
   合同，各领域文档拥有具体行为，消费者文档保留组合事实和引用。
3. 核对 Organization/semantic retrieval 的旧副本、相关 Sink/Resolver 文档与导航；已发现的图查询和
   Rumination authority 错置均在本轮纠正，不仅添加新段落而保留旧规范。
4. 按另行授权先提交/推送 Hub，再单独提交 Core shared-ref bump；Core 本地文档/代码另行提交。
   本次 packet 提交授权不包含这些后续 Git 操作。
5. 检查单条合同是否只剩一个定义 owner、摘要是否忠实、引用是否可达，以及实现调用链是否符合分层。
   不新增 claim registry、文档 gate 或为了准则而建立另一份通用框架。
检查 docs/openapi.json 的生成边界，静态文档不伪装包含尚未启用的动态实例。

按现有 release tooling 为 Core 与 CLI 添加 Towncrier fragments，版本由独立 Release PR 消费，
不在功能 PR 人工改版本或重做发布编排。运行 pdm run check、pdm run -p cli check 和
pdm build -p cli，并按实际改动运行 release/migration checks。构建产物不进入 Git。

## P5：验收与交付

先以 wheel 对接 preview 完成 A1–A4 与共享工具回归；语义问题优先检查真实轨迹和 evidence，不凭
失败就追加 prompt 规则、工具或更大预算。修正与复跑均记录。接着按经确认的交付终点、另行取得的
Git/发布授权推进。部署成功与 PyPI 可安装都以实际结果核验，不以合并或 CI 绿色替代。
