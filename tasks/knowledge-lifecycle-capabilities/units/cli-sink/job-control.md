# Job 观察与停止

状态：范围已获 D-576 确认，等待/停止语义与集中检查机制已获 [D-580](../../decisions/D571-D580.md) 确认，定位为 best-effort。
检查周期、精确接口与取消传播仍需技术设计及预演；尚未授权实现。[Job REST 与有界观察](job-rest.md)
已按 D-587 确认具体 HTTP 与 CLI wait 方案，不改变本页已确认的运行语义。
CLI 仍只调用 Core REST。Job 在哪个 Peer 执行，不改变 CLI 的命令，也不需要调用者寻找 worker。

## 一个 Job，分别观察与控制

```sh
inkcre-cli job get 301
inkcre-cli job wait 301 --for 30s
inkcre-cli job abort 301
inkcre-cli job wait 301 --for 10s --json
```

`get` 取得当前持久记录。`wait` 在调用者指定的时间窗口中观察同一 Job，进入终态可以提前返回；预算用尽则
返回最新已观察记录，即使仍是 pending/running。它不重新创建 Job、不改变执行 timeout，也不在命令结束或
被中断时自动 abort。没有新状态时可以继续下一次 wait。轮询过程走 stderr，stdout 只返回观察结果。

Job `state` 仍由 Handler 提供；有何进度、checkpoint 或错误信息取决于它实际持久化了什么。CLI 不把运行
时间伪装成完成百分比，也不因没有进度字段引入统一 progress 协议。等待过程与 Job 本身的结果是两件事：
正常观察到 failed/timed_out，或者等待预算用完，不等于 CLI 观察操作失败。网络/协议错误仍报告实际失败。
等待默认预算与 CLI 基于 GET 的组合已按 D-587 确认；准确时长解析语法与完整 exit code 表仍待统一收敛。

## 请求停止与执行已经结束分开

| 调用时的 Job | `abort` 的行为 |
| --- | --- |
| pending | 原子关闭为 aborted，使其不能再被 claim；不需要等待执行端 |
| running | 持久化停止请求，由实际执行端取消工作；返回当前记录，不把受理冒充已停止 |
| 任一终态 | 返回已有终态，不重写结果，不产生重试或另一个 Job |

运行中的 Job 在执行端结束前仍是 running。增加一个 Job-owned `abort_requested: bool` 表达请求，不把
控制信息混入 Handler-owned `state`，也不增加整套中间状态。执行端处理请求并结束执行后再关闭为 aborted。
示意字段子集为紧凑 JSON：`{"id":301,"status":"running","abort_requested":true}`；完整响应仍是 Job 记录，
不额外包装 receipt。字段与 runtime 集中检查策略已按 D-580 确认。

重复请求不会重复创建控制工作。停止与完成竞争时保留已经写入的终态，不把 finished 回写成 aborted。
停止请求本身不清空执行记录、不释放 Cron 的非终态占位；因此不会仅因请求受理就允许下一次 Cron Job 重叠。
若执行端已消失，不能声称它确认了停止；保留请求事实并沿用已有 timeout 收敛，不增加重领或 retry。

停止不回滚已写入的 graph/state，也不承诺撤回已经发出的远端请求。合作式取消不是杀进程或跨系统事务。
具体 Handler 的阻塞 SDK、后台子任务、Agent tool 执行如何结束，须在预演中核验；不能只取消一个等待它的
协程就宣布全部工作已停止。若 Handler 尚未结束，abort_requested 与 running 可以并存。

## 多 Peer 仍通过数据库协同

```text
CLI → Core REST → JobManager 写入停止请求 → jobs
                                            ↑
                实际执行端 JobManager 读取请求
                  → 取消本机执行 → 结束后关闭 Job
```

REST 所在 Peer 不一定是执行端。执行端可以是另一 core-py，也可以是 client-web；因此不能只维护收到 HTTP
请求那台机器的 task map，也不为停止另建 Peer delegation capability、broker、控制 Job 或执行端路由表。
复用各端现有 Job worker 检查机制，对本机 active Job 读取停止请求，使用各自已有异步运行模型取消。
检查间隔与结束确认的具体机制进入技术设计；不在产品层承诺即时或强制终止。

### 停止意图与通知方式分开

2026-09-13，Sir 曾质疑执行端需要监听/检查字段是否不够优雅；澄清责任和成本后，接受集中检查作为 best-effort。
`abort_requested` 表达持久化意图，不决定使用轮询还是推送。跨进程停止必须让执行端收到某种信号，不能
仅修改记录就令正在运行的代码停止；但这不要求每个业务 Handler 自行查询数据库。

把观察和取消集中在执行端 JobManager：一次批量检查本机 active Job 的停止请求，再对相应执行句柄
发出取消。没有本机 active Job 时不发这一查询。不为每个 Job 建一个数据库轮询循环，也不在 collect 的
每个 item、Organization 的每个 seed 中散布 `if job.abort_requested`。Handler 只遵循通常的异步取消和
资源清理合同；浏览器 Handler 继续使用已有 AbortSignal，而不理解数据库控制字段。

机制比较保留以下真实成本：

- 批量轮询复用当前两端已有的数据库访问与 worker，代价是额外查询和停止响应延迟；封装不会消除这些成本。
  当前发现 pending Job 的 30 秒周期不自动成为主动停止的响应合同，具体检查周期仍需设计。
- PostgreSQL LISTEN/NOTIFY 可替代周期查询来提示变化，但 LISTEN 绑定数据库 session，断开后注册消失；
  初始/重新连接时仍要读取持久状态。见 [PostgreSQL 官方文档](https://www.postgresql.org/docs/current/sql-listen.html)。
  当前浏览器数据通道是 `@supabase/postgrest-js`（`packages/core/src/base/db-api.ts`），不是这种 PostgreSQL
  session；改用通知需要补足浏览器的通知转发路径。`app/settings.py` 也已表达不能假定 LISTEN/NOTIFY 可用。
- 直接推送到执行 Peer 可以降低通知延迟，但要识别执行端并提供可达控制入口；当前 Job 没有执行 Peer 字段，
  浏览器 worker 也没有对应入站控制服务。它不是无成本替换一个字段，并会改变当前仅通过数据库协同的边界。

因此选择集中在 JobManager 的批量检查，不为停止另建通知基础设施。该结论按 ponytail 比较既有机制与新增
成本，并由 python-backend-code 检查 runtime/Handler 责任分离；已获 D-580 确认。best-effort 不消除实际取消
执行的责任，也不把持久化请求或终态当作强制终止所有外部效果的证明。

## 核验依据与实现前压力

2026-09-13 只读检查确认：

- `app/business/job.py` 已拥有 claim/close 的条件更新、`asyncio.timeout`、pending scanner 与 overdue 收敛；
  `run.py` 每 30 秒唤醒 `JobManager.check`。没有主动停止 API、请求字段或取消处理。
- `app/schemas/job.py` 已有 aborted 终态，但 enum 本身不会停止执行；Job `state` 是 Handler 的结果数据。
- `client-web/packages/core/src/job/manager.ts` 已有 active set、30 秒 worker 与每次执行的 AbortController，
  当前只用于 timeout；`source/manager.ts` 将 AbortSignal 传给 collect/backfill。
- `client-web/apps/client-web/src/core.ts` 会启动该 worker。它不是纸面上的未来 consumer，需要在本 unit
  配套同一停止协议；没有因此增加 client-web 管理 UI 的需求。

2026-09-13 的验收准备进一步区分了 worker 存在与实际业务执行资格：在 client-web 的 packages、extensions、
apps 跟踪源码中，仅找到 source/manager.ts 的两个通用 Job handler 注册，没有找到实际 SourceImplementation
的注册调用。因此不能仅凭 worker 已启动，承诺可用既有 Mail/Twitter Source 做浏览器 collection 验收。
双 core-py 验证完整跨 Peer 链路；浏览器侧使用公开 worker 边界的有限脚本验证，准确区分组件证据和业务旅程，
具体提案见 [Acceptance](acceptance.md)。本次没有启动浏览器或核验远程动态 Extension 的运行清单。

后续技术设计/预演应走过 pending claim 与 abort 竞争、running 取消与自然结束、timeout、进程退出与子任务
清理。保持 DB 条件更新为生命周期边界，不以 application 先读后写替代。需同步 schema/migration、两个
JobManager 与返回记录；这些是本提案的预计影响，不是已获授权的源码改动。

本轮按 python-backend-code 核对真实异步执行和取消边界；按 ponytail 保留现有数据库协同及两端异步机制，
不增加新的调度系统。当前阶段不增加自动化测试；验收仍在整体 Acceptance 阶段按真实黑盒边界设计。
