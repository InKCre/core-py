# Runtime 预演：持久表示与取消

2026-09-13；对应实现计划 P1/P2。本页区分已观察事实、实现方向与需 Sir 复核的取舍；没有修改业务源码。

## P1：不能把类型恢复误称为无校验解码

已检查 `app/configuration.py`、`app/business/deployment_config.py`、Source config/Job 路径、
`app/schemas/agent.py`、`app/schemas/ai/capability.py`、OpenAI-compatible Provider config 与 Mail schema。
它们存在三种不同问题：

| 边界 | 事实 | 可行修正 |
| --- | --- | --- |
| 管理面直接读记录 | DeploymentConfigManager._view 先按当前 runtime schema 验证 value，再 dump 回 JSON | 直接返回持久 value；不依赖 schema 已加载，也不填入当前默认值 |
| PATCH 和同次调用传值 | prepare_patch 先 normalize(current)，PATCH 本身又提前 validate(current)；返回 _view 再验证；部分调用方对已得到的 typed config 再 model_validate | 合并原始完整候选后仅验证新值；typed 对象直接传递，返回持久结果不重验 |
| 数据库 JSON → 可执行 Python 对象 | Mail parameters/排除策略/checkpoint 是嵌套模型，Provider api_key 是 SecretStr，Agent tool_choice/AI capability 是 union | 必须恢复这些类型；浅层 model_construct 和静态 cast 不完成此工作 |

本机 Pydantic 2.13.4 隔离实验进一步确认：同一个已构造对象再传入 model_validate，after model validator
仍会运行；默认 revalidate_instances 并不能用来保证所有自定义检查跳过。model_construct 则保留 nested dict，
不会生成 Params 或 SecretStr。实验只有内存中的合成值，没有数据库、凭据或新测试文件。

[Pydantic 官方说明](https://docs.pydantic.dev/latest/concepts/models/#creating-models-without-validation) 明确区分了
这两条路径：不验证的 construction 也不做嵌套模型转换。该库的普通模型恢复同时执行类型转换与约束，不能
仅把 model_validate 改名为 decode 就声称校验已经消失。

### 已确认的取舍（D-602）

直接读记录、REST/CLI 响应和已构造 typed 对象传递，严格去掉额外检查；PATCH 只验证合并后的新值。
对于确实需要从 JSON 恢复复杂 Python 模型的执行入口，允许保留一次 Pydantic 原生构造，并接受它附带执行
模型约束。不能把它宣传成完全无校验，也不再叠加一次专用的“持久值合法性”检查/错误包装。

简单且已有明确 owner 的表示（如数据库 text[] → tuple）直接转换，不需要 Pydantic。通用 Source/Extension
config/state 允许外部类型，不能只覆盖当前几种配置就宣称实现了通用 decoder。这里不推荐为了消除最后一次
库校验而添加每种 Extension 必须实现的 decode hook、递归 schema walker 或另一套并列模型。

这比 P1 原先“所有读回只转换”的字面承诺更窄，2026-09-14 已按 D-602 获 Sir 确认，并提炼为 Python 后端
通用指南。设计取舍已闭合，不代表各调用链已实施验证。CLI 本身仍只解析 REST JSON/MIME，不受此例外影响。

## P2：停止链路已经定位，但不能以终态冒充清理完成

```text
JobManager.run → handler.handle → Organization → await Thread.current_turn
                                           → gather(Tool tasks)
                               → Mail → IMAPAdapter._run → to_thread(IMAPClient)
```

Organization `_shared.py` 与 media interpretation 直接 await turn；Thread 的 tool batch 使用 asyncio.gather，
CancelledError 记录后重新抛出，未发现这里有 shield 将取消吞掉。因此普通 async 路径可以沿现有 await 传播，
不需要给每个 Tool 增加数据库检查。Tool 内已经发出的 thread/外部效果仍另行判断，不承诺撤回。

Core JobManager 目前只处理 TimeoutError/Exception，未记录本地运行句柄；CancelledError 不会沿这些分支
关闭。client-web active 只有 Set，AbortController 专用于 timeout；需用执行句柄及原因区分 timeout/abort，
等待 handler 的 Promise 结束后再关闭。两端条件更新继续阻止终态覆盖，不能以意图字段变化释放 Cron 占位。

### Mail 的实际资源清理缺口

`extensions/mail/adapter.py:IMAPAdapter._run` 在 asyncio.Lock 内 await to_thread(function)，`__aexit__` 随后
通过相同 _run 执行 disconnect。本机 threading.Event 控制的隔离实验得到：

```text
awaiter_cancelled → cleanup_acquired_lock_before_worker_finished → worker_finished
```

这说明取消 awaiter 会先释放外层锁，仍在执行的 IMAPClient 调用可能与断连并发。锁的存在本身并未保护
这个退出分支。修正应由 IMAP adapter 保持该次线程调用的完成与连接清理顺序，Job runtime 不理解 IMAP。
开始连接途中取消也需要清理，不能只处理 __aexit__（__aenter__ 未返回时它不会被调用）。

当前构造 IMAPClient 没有传 timeout；本机库支持 SocketTimeout(connect, read)，可复用其有限网络超时，
不自建 IMAP 请求计时器。参考 [IMAPClient API](https://imapclient.readthedocs.io/en/3.0.1/api.html)。
网络 inactivity timeout 不是整个命令的硬 deadline，不能将其宣传为强制杀线程。

2026-09-14 已完成下述隔离替代验证；业务源码尚未修正。JobManager 集中检查应避免重复对同一 handle 发
cancel 干扰清理。现有 expire_overdue 仍会按数据库时钟关闭逾期记录，
它是既有遗失执行收敛机制，不是 handler 清理完成的确认，也不据此承诺全局零重叠。

Mail adapter 修正属于已确认的真实取消链路影响，实施计划应包含对应 Extension fragment 与真实 IMAP 验收。
不扩大为所有协议的取消框架；独立 blocking 操作是否有残留效果按实际调用链记录。

### 已通过的替代清理实验

实验继承实际 IMAPAdapter，局部替换 _run/__aenter__，以 threading.Event 控制同步连接、操作、断连，
保持真实的 async context 生命周期与锁。同步方法是受控 double，不连接 IMAP server，也不访问数据库。
为 import Core 提供的是指向 loopback 未使用端口的占位 DSN 和非凭据常量，禁用 dotenv；不依赖真实账号。

候选 `_run` 在锁内保留 to_thread 的 task，并通过 shield 等待它。收到取消时记住 CancelledError，继续等
同一 task 完成，不重新执行同步函数；结束后取出真实结果/异常，再向上传播取消。若同步函数同时失败，
异常保留在取消的 cause 中，不丢失。重复取消仍只影响等待方，不取消正在排空的私有 task。

`__aenter__` 失败或被取消时先调用同一串行路径清理已取得连接，因为 Python 不会为失败的 __aenter__ 调用
__aexit__。正常退出继续使用已有 __aexit__。这几处都留在 adapter，不让 JobManager 理解 IMAP。

下列六次受控取消和一次正常生命周期全部通过：

- 连接中取消：connect 完成后 disconnect，连接不泄漏。
- 操作中取消：operation 完成后才 disconnect，锁始终覆盖同步操作。
- 断连中取消：disconnect 完成后才传播取消。
- 操作中重复取消：第二次取消不会提前释放锁或结束清理。
- 操作被取消且同步 I/O 失败：清理完成，取消仍可观察，原始 OSError cause 保留。
- asyncio.timeout 触发取消：同步操作和断连完成后向调用者表现为 TimeoutError。
- 正常执行：connect → operation → disconnect，不改变无取消路径。

每个取消场景均检查：同步函数尚未返回时外部 task 未结束、锁仍持有；最终 _client 清空、无并发连接操作、
取消没有被吞掉。这证明候选清理顺序可行，不证明已经终止任意线程、进程崩溃后的清理或真实 IMAP journey。
实现仍需使用已检查的 IMAPClient 有限网络超时，并在原定 Mail 黑盒旅程验证真实协议路径。
