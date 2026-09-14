# CLI 命令结构

状态：分组及职责边界按 [D-575](../../decisions/D571-D580.md) 获批，[输入与发现](input-discovery.md) 已获 D-577
确认；不是已实现的命令目录。输出原则、Job 控制与本机接入已获 D-578–D-582 确认，精确 REST DTO 仍在设计。
示例暂以 distribution 同名的 `inkcre-cli` 为可执行名。

## 按意图与操作对象组织

高频的信息取用动作直接放在根级；需要围绕一个对象持续管理的操作放在领域组内。区分这些入口的依据是
调用者要取得什么结果、修改哪个对象，而不是 REST 路径、数据库表或追求所有命令具有相同深度。

| 命令入口 | 职责与拟议子命令 |
| --- | --- |
| `recall` | 显式选择词法、语义模式找候选；可以组合模式，不在 CLI 隐藏选择策略 |
| `get` | 按引用批量取得 Block / Relation 记录，允许混合实体；可选不含 content、原始 content 或 hydrated content |
| `update` / `delete` | 原地编辑或删除一个明确的 Block / Relation；沿用 get 的实体引用形式，准确表单已按 D-596 确认 |
| `graph` | `neighborhood`、`path`、`components` 提供图查询；`submit` 提交 GraphForm |
| `resolver` | `list`、`methods`、`invoke` 发现与调用普通 Resolver 读取能力，包括 `get_solved_content`；不为每种 Resolver 增加 CLI 子命令 |
| `source` | `types`、`list`、`get`、`create`、`update`、`delete`、`collect`、`backfill` |
| `organization` | `ruminate` 为指定 Block 创建相应 Job；Block 是输入，行为与 handler 仍属于 Organization；行为配置通过 `config` 管理 |
| `agent` | `list`、`get`、`create`、`update`、`delete` 管理 Agent definition；`tools` 发现 Agent Tools；不增加对话、Thread 或本机 Agent runtime |
| `ai` | `models` 发现与读取 AIModel；模型被 Agent 引用，不改变其 AI 领域归属；本轮不扩展 Provider / Model 写入 |
| `job` | `types`、`create`、`list`、`get`、`wait`，并纳入主动停止（拟名 `abort`）；限时等待与停止的准确合同见下文 |
| `cron` | `list`、`get`、`create`、`update`、`delete`、`enable`、`disable`、`run`；配置服务端定期执行，或从现有模板立即派发一次 Job |
| `peer` | `list`、`get`、`wake`；报告已知状态与等待 HTTP 服务就绪 |
| `extension` | `list`、`get`、`install`、`uninstall`、`enable`、`disable` 及其配置读取/更新 |
| `connection` | 本机连接配置；`list/get/set/delete/use/check` 已按 D-582 确认，见 [连接与接入](connection-access.md) |
| `config` | 远端 deployment 配置；list/get/replace/update/delete/schemas 已按 D-590 确认，包含 Organization behavior config |

`get block:42 relation:8` 中的字符串是 shell 下明确实体种类的输入表示，不创建新的领域 ID，也不要求 Core
REST 或 MCP 改成同样的 JSON 形状。`get` 不解释内容：raw 是 `BlockModel.content`，可能是 Storage pointer；
hydrated 通过 `BlockModel.get_hydrated_content()` 取得实际内容。Relation 没有 Storage，不能为统一模式虚构
它的 hydration 过程；混合批次下其原始 content 是否省略随选项合同明确。图的邻接结构由 `graph` 查询。
内容字段与基础读取见 [实体与 Resolver REST](entity-resolver-rest.md)；[内容 HTTP 表示](content-transport.md)
与 [文件输出](file-output.md) 已按 D-584–D-586 确认，不能从读取方法名称推断内容总是文本。

取消独立 `read` 命令。`get_solved_content`、`get_text` 等均是 Resolver 的普通方法，归入 `resolver invoke`，
CLI 不再增加一份与它们并列的内容解释合同。已知方法可直接调用，不必每次先发现。

根级 `get`、`update`、`delete` 的 help 必须明确它们操作的是 info-base 实体；Source 等管理对象通过自己的命令组管理。暂不增加
与这些命令功能相同的另一套别名。`connection` 与 `config` 分别修改本机连接与远端 deployment 配置；
D-582 已确认轻量命名连接，不引入 profile 继承或凭据服务。

## 命令不是另一套业务实现

`source collect` / `backfill` 向 Core 请求创建已有类型的 Job；回执与 `job get` / `wait` 操作同一个 Job。
`organization ruminate` 同样创建 Job，参数为指定 Block；当前缺少对应的显式 Job type，按 D-595 在 Organization
内补齐。CLI 不变成 worker，也不直接调用 Peer inbound 或执行门面。这里统一的是收集/整理的任务受理与控制，
不是让检索、配置保存或原地实体编辑也通过 Job 执行。

自动 Organization 从 `job types` 发现准确类型和参数，交给 `job create` 执行一次，或将同一 Job 模板交给
`cron create` 周期运行。已有自动行为自行选择候选，不能在 CLI 为其强加每次固定的 Block，也不维护另一份
Organization 名称到 Job type 的映射。`cron run` 沿用 `CronManager.run_now`，创建一次 Job 而不推进定期进度。

Agent definition 保存 system prompt、model、tools、tool_choice 与每 turn 的调用预算；Organization behavior
config 选择它要使用的 Agent，不复制这些字段。前者由 `agent` 管理，后者由 `config` 管理；修改 definition
不隐式改绑行为，也不改变已经开始的 Thread 快照。模型和 Tool 引用需要配套发现，技术设计核对实际接口，
不因此自动纳入 AI Provider 写入或完整 Agent 会话管理。

Extension 安装记录、Peer 启用意图与实际运行状态仍分别表达；CLI 不拥有 Extension 的发布或运行生命周期。
Source type、Resolver method、Job type 的动态合同来自 Core 的既有 owner。CLI 包不为每个 Extension 附带
适配代码，也不要求 Extension 额外注册 CLI commands。

`connection` 选中的 HTTP 服务与业务执行目标 Peer 不是同一个参数语义：前者是 CLI 接入点；后者只在该业务
支持指定 Peer 时成立。不能从连接配置推导所有 Job 都由该 Peer 执行。准确参数随 Technical 核对，不发明一项
对所有命令生效的全局执行 Peer 设置。

## 限时观察与执行控制

`job wait` 允许调用者指定本次最多等待多久；推荐终态提前返回，否则在等待预算用尽时返回最近实际观察到的
Job 状态。比如拟议 `job wait 301 --for 30s`，不代表把 Job 执行期限改为 30 秒。准确选项和默认时长待复核。
等待额度用尽不是 Job 的 `timed_out`，也不自动取消执行；调用者可使用同一 Job ID 继续等待、查询或主动停止。
观察失败仍需报告真实故障，不能冒充拿到了最新状态。进度只呈现 handler 实际提供的 state，不伪造通用百分比。

Core 当前的 `JobStatus.ABORTED` 只是已有状态枚举；`JobManager.run` / `check` 没有主动取消链路。D-580 已确认
以 JobManager 集中检查停止请求的 best-effort 方案补齐，见 [Job 控制](job-control.md)。主动停止
因此是本轮需要补齐的实际执行能力（D-576 已明确确认），而不是修改一列即可完成的 REST 包装。技术设计需覆盖 Job 可能在其它
Peer 执行的事实、停止请求与执行结束的区别，不在这里承诺杀死进程、远端服务请求或回滚已完成的效果。

## 以实际过程检查可组合性

以下是拟议语法，不是必须遵循的操作 SOP；给定准确 ID 时可以直接读取，不必先搜索或发现。

```sh
inkcre-cli recall 'Agent 工具' --mode lexical
inkcre-cli get block:42 relation:8
inkcre-cli resolver invoke block:42 --method get_solved_content
inkcre-cli graph neighborhood block:42
```

调用者按信息缺口选择步骤。读取内容不自动展开所有相邻实体；邻域查询也不自动读取整幅子图的 solved content。

```sh
inkcre-cli source types
inkcre-cli source create --type <source-type> --input source.json
inkcre-cli source collect 12
inkcre-cli job get 301
inkcre-cli job wait 301 --for 30s
```

这里的 ID 是示意。`source.json` 的结构必须能通过 CLI 从当前 Core 取得；不能要求调用者翻源代码。Collect
创建回执提供真实 Job 引用，`wait` 有界地观察那次执行，而不是重发 collection。JSON 文件/stdin 是嵌套输入的建议
承载形式；`--input` / `--input-json` 已按 D-577 确认。

```sh
inkcre-cli job types
inkcre-cli cron create --job-type <job-type> --input cron.json
inkcre-cli cron run 9
```

最终持久的 Cron 模板保存 Job type、其参数、schedule 和超时；拟议 argv/JSON 分工见 [输入草案](input-discovery.md)。
既可配置收集，也可配置自动整理。手动立即执行与启用未来 schedule 是不同动作，不互相隐含。Source 无需知道自己是否被 Cron 调用。

## 后续复核面

结构按 D-575 收敛；[动态输入](input-discovery.md)、[结果呈现](output-presentation.md)、[内容交付](content-delivery.md)、
[Job 控制](job-control.md) 和 [连接接入](connection-access.md) 已获 D-577–D-582 确认。
基础读取、内容交付及 [Job REST](job-rest.md) 已按 D-583–D-587 确认，[Source / Cron REST](source-cron-rest.md)
已按 D-588 确认，[Agent definition 管理与引用发现](agent-management-rest.md) 已按 D-589 确认，[deployment config](deployment-config-rest.md)
已按 D-590 确认；继续 Peer / Extension 等领域 REST 和分发。类似 `gh api` 的长尾 HTTP
入口暂未列入本方案；没有具体缺口时不让它代替领域命令，
也不因此将未来增加这个普通工具变成禁止事项。

[Peer REST 与 HTTP 唤醒](peer-rest.md) 已按 D-592 确认：记录读取、数据库时间 lease_active，以及以已配置
connection 为目标的直接 /readyz 唤醒。self 为内置别名；不自动支持按任意 Peer ID 发现 REST 地址。

[Extension REST](extension-rest.md) 已按 D-593 确认：保留安装、卸载和配置管理的现有 Host 入口，补齐配置
PATCH，只为 enable/disable 增加目标 Peer 参数；不代表命令及协议已经实现。

[检索与 Graph REST](retrieval-graph-rest.md) 已按 D-594 确认多模式 Recall 的独立结果、图查询路径与追加 Graph 的
POST method correction。语义 profile 选择配套只读 embedding-profile list/get，不引入新的配置写入范围。

[收集/整理 Job 与实体修改](organization-write-rest.md) 已按 D-595/D-596 确认；收集、整理均提交相应 Job，
新增显式 rumination Job type，Block/Relation 的原地编辑与删除使用 update/delete。共同的
[管理列表与错误输出](list-error-contract.md) 已按 D-597 确认；长输出分页和独立批次的部分失败为通用模式，
不改变上述已确认的任务受理语义。

现状依据：`app/business/graph_navigation_retrieval/main.py`、`info_base/resolver/main.py`、`info_base/main.py`，
`app/routes/source.py`、`organization.py`、`extension.py`，以及 `app/business/job.py`、`cron.py`。
这些依据证明已有行为和责任，不证明本表全部 REST 路由已经存在；缺失的普通 REST 仍按 D-572 在 Technical 中设计。
