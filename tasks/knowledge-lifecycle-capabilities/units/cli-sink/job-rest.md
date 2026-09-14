# Job REST 与 CLI 有界观察

状态：2026-09-13 按 [D-587](../../decisions/D581-D590.md) 获确认，尚未实现。以 D-575/D-580 的等待、停止和执行端集中检查为基础；
本页收敛 HTTP 接入与 CLI 组合，不重新定义 Job 生命周期，也不授权实现。运行语义统一见 [Job 控制](job-control.md)。

## 创建、观察与请求停止

| 普通 REST | CLI 用途 | 返回 |
| --- | --- | --- |
| GET /job-types | job types，发现 deployment 已知的 exact 类型 | 类型目录 |
| GET /job-types/{type} | job create --type … --schema 所需的动态参数合同 | JobType 的参数 schema 与默认执行期限等字段 |
| POST /jobs | job create | HTTP 201，直接返回持久化后的 Job 记录 |
| GET /jobs | job list | 最近的 Job 记录列表，允许 type/status 过滤 |
| GET /jobs/{id} | job get，以及 wait 的每次观察 | HTTP 200，直接返回 Job 记录 |
| POST /jobs/{id}/abort | job abort | HTTP 200，直接返回处理停止请求后观察到的 Job 记录 |

列表按 D-597 的 [limit/cursor 合同](list-error-contract.md) 返回，不据此宣称返回全部 Job 历史。
单条不存在为 404；创建/查询/停止
没有另一份 success/status receipt。实际 Job 字段保留 type、parameters、state、timeout_seconds、status、
created_at、started_at、closed_at，并加入 D-580 已确认的 abort_requested；不虚构当前没有的执行 Peer 字段。

POST /jobs 的请求复用已有 JobCreateForm：

```json
{"type":"core.source.collect.v1","parameters":{"source":12,"config":{}},"timeout_seconds":300}
```

CLI 中 type 仍由 --type 提供，JSON 输入只包含 parameters 与可选 timeout_seconds；--schema 显示的也是
这一输入位置，不要求填写数据库字段。parameters 的动态合同由 Job owner 提供，Core 沿用 JobManager 的
本地 Handler 模型或持久化 JobType schema 校验。CLI 不再构造一份 Extension 参数校验器。

创建只确认执行机会已持久化，不等待执行、不在 HTTP handler 内运行工作，也不要求接入 Peer 的 can_handle
通过。当前 JobManager 已支持本机没有 Handler 时按持久 schema 创建 Job；其它 capable Peer 可正常 claim。
GET job-types 因此读取 deployment catalog，而不是过滤成接入 Peer 此刻可执行的清单。目录也不承诺现在
有在线执行者，或该参数一定能被某个执行者成功处理。

POST abort 不需要业务 body。重复调用或 Job 已经结束时仍返回真实记录；不开放通用 status/state PATCH，
也不使用 DELETE 来混淆停止执行与删除历史。具体 pending/running/terminal 转移沿用 D-580，并由 JobManager
及数据库条件更新完成，HTTP 层不复制生命周期分支。abort_requested 与 running 同时出现是合法结果。

D-595/D-596 明确：CLI 显式收集、整理均受理为相应 Job。Source 便捷入口沿 D-588；organization ruminate 直接
使用 POST /jobs 和新增的 explicit rumination 类型，详见 [任务入口](organization-write-rest.md)。已有 automatic
类型的 max_seeds 参数不是指定 Block 的替代物。上述命令不增加执行 Peer 选择，不调用 Peer inbound。

## wait 是 CLI 对 GET 的有界组合

job wait 默认最多观察 30 秒，可通过 --for 指定其它时长；进入任何终态时提前返回。每次 wait 先进行
一次 GET，未结束时在预算内以约 2 秒间隔继续查询，不新增 /wait endpoint、服务端等待会话、SSE 或 WebSocket。
CLI 的状态查询与执行端 JobManager 集中读取 abort_requested 是不同职责，不能混成一个轮询机制。

```sh
inkcre-cli job wait 301 --for 30s --json
inkcre-cli job abort 301 --json
inkcre-cli job wait 301 --for 10s --json
```

时长字面值的最终解析语法随 CLI 库选型收敛，示例不要求手写 duration DSL。观察预算按单调时钟计算，覆盖
本次 HTTP 请求和查询间隔，不在每次 GET 后重新计时；剩余预算约束在途读取的等待时间。

预算用完时返回最后成功观察到的记录，不宣称它是此刻数据库的最新状态。若预算内尚未取得任何记录，应
报告观察超时，不能伪造 pending/running。终止原因只是本次观察预算用尽时，可返回已有记录；网络断开、
认证失败或 HTTP 错误不是预算正常耗尽，不以旧记录冒充观察成功。stdout 保留单个 Job 记录，过程在 stderr。

正常读取到任何 Job 状态，包含 failed/timed_out/aborted，或正常等到预算结束，CLI 观察操作均以 exit 0
结束。调用者检查 Job.status 判断后台工作结果。连接、协议或请求失败使用非零退出码；具体退出码已按
D-597 确认。Ctrl+C 或命令结束只结束本次观察，不自动发 abort，不修改 Job 的执行期限。

## 现有实现与预演压力

2026-09-13 只读核验：

- app/schemas/job.py 已有 JobCreateForm 与 JobTypeModel 的 parameters_schema/default_timeout_seconds。
- app/business/job.py 的 create 已与 _prepare/can_handle/_claim 分开；持久类型可在没有本地 Handler 时用于创建。
- 当前 app/routes 中没有 Job 管理 router；app/routes/source.py 的 collect/backfill 直接创建 Job 并同步调用
  JobManager.check。D-588 已确定将这次附带扫描移到受理响应之后，不能让已提交 Job 因后续扫描失败而被
  描述为未创建；这是已确认的实现落点，不再作为未决产品选择。
- Job 返回模型没有 updated_at 或执行 Peer，不为输出一致性添加这些字段。client-web 的实际 Job worker 与
  AbortController 已在 Job 控制文档列为配套落点，不因 CLI 通过 core-py 请求就跳过另一端。

后续预演需要覆盖创建已提交但响应中断时不自动重发、pending/running/terminal 的观察与停止竞争、观察预算
覆盖慢请求，以及观察命令结束后工作继续。执行端的集中检查周期和子任务取消仍在 Job 控制的实现前压力中。
本提案没有为发现目录、路由表或 DTO 新增自动化测试，也没有开展数据库操作。

本轮按 python-backend-code 保持 HTTP 边界薄，按 ponytail 复用 JobCreateForm 与 JobManager，将 wait 留作
已有 GET 的有界调用组合，不建立第二套任务生命周期或等待服务。
