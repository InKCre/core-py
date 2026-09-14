# 校验与执行链预演

2026-09-14，P1/P2 的实现落点。D-602/D-603 已确认，不重新讨论是否允许 Pydantic；
下表区分输入、持久表示恢复和已有 typed 值的传递。这里只记录预演，源码尚未修改。

## P1：校验只留在有意义的边界

| 具体 owner | 当前问题与实施方式 |
| --- | --- |
| `app/configuration.py` | ConfigContract 接收已构造的目标模型时直接传递；mapping 输入用原生 Pydantic。PATCH 将 raw current 与提交字段浅合并，再验证一个新候选，不先验证旧值。 |
| `app/business/deployment_config.py` | 管理 GET 返回存储的 value，不调用 schema 校验；typed get 保留一次模型恢复。PATCH 在现有行锁内合并；不增加 config schema 表或重复解码器。 |
| ext-reg `runtimes/core-py/src/inkcre_extension_runtime_core_py/base.py` | bind/on_start 中丢弃结果的重复校验移除。get_config/get_state 的复杂 JSON 恢复保留一次。mutation callback 已得到模型，返回值继续传递；用闭包保留 typed 结果，避免 host 提交后 dump→validate 的往返。现有 store 在锁内调用一次 mutator，失败正常传播。 |
| Core Extension facade、Twitter setup/state 调用方 | 移除对 runtime 已返回模型的再次 model_validate。实际从持久 dict 恢复 state、或恢复当前运行实例的 config，不机械删除。 |
| SinkManager | 更新边界得到的 validated model 保留到 running instance 更新；启动读取持久值时仍构造一次。 |
| Source / `app/business/info_base/storage/main.py` | config/state 首次恢复保留；Mail/RSS/Twitter 收到已经是目标模型的 collect config 后不重验。Source 未加载时的 catalog 输入见 [REST 接合](preflight-rest.md)。 |
| AIManager / dialect | Provider 配置包含 SecretStr，首次恢复必要；dialect 不再对同一模型重验。模型 capabilities 的结果 codec 保留一次 TypeAdapter 恢复 union，移除额外的重复、排序检查；输入边界仍规范化。 |
| Agent / Peer codecs | Agent tools 读回恢复 tuple，不重做输入去重排序；ToolChoice union 仍需要原生类型恢复。Peer capability snapshot 同理；发布新 advertisement 的输入规范化不删除。 |
| Deployment config 使用者 | Source、Cron、Extension registry 等拿到已经恢复的模型后直接使用，不再 model_validate 一遍。 |
| Job `_prepare` | eligibility 与实际执行接合，避免一次执行的配置重复恢复；不能将输入错误变成永久 pending。handler/schema 未在本 Peer 注册与提交无效是不同情况。 |

这不是搜索 `model_validate` 后批量删除。Registry/AI/Peer 外部响应、LLM tool 输入、Resolver 对 bytes/JSON
的解析、GraphForm→持久模型转换均各有实际边界。尤其不能把浅层 model_construct 当作递归类型恢复。
正式评审逐调用点核对这些边界，验收看真实读写与使用结果，不添加 validator 调用计数测试。

## P2：一个执行端拥有本地取消传播

```text
条件 claim → 登记本地 task → handler → Agent / Source adapter
                  ↑                         ↓
     集中读取 abort_requested       等待实际执行和必要清理退出
                  └──────────────→ 条件终态更新
```

Core 在 claim 成功后、下一次 await 前登记句柄。集中观察 active job 的取消意图，初始采用 2 秒批次；
没有 active job 就不查询。保留原有 30 秒 pending discovery，不让每个 handler 自行读数据库。
每个句柄只发送一次主动取消，记住原因；pending 的直接关闭和 claim 使用条件更新处理竞争。

client-web 的 active Set 变为保存 AbortController、执行 Promise、结束原因的本地映射。
主动取消、timeout、正常完成沿现有条件关闭边界汇合；等 handler Promise 退出后再报告本端关闭。
旧 worker 不认识 abort_requested，因此 Core 和 client-web 两端发布都是完整交付条件。

`JobManager.check` 目前扫描并向 scheduler 安排执行，不会 await 整个 collection。现有 REST 等待 check
的问题是持久化后的扫描错误/延迟会影响受理响应；改为提交后 best-effort 触发，日志保留实际失败。
这不把 Job handler 改成 FastAPI BackgroundTask，也不让请求 session 活到后台。

本机安装的 APScheduler `AsyncIOExecutor.shutdown(wait=True)` 仍直接 cancel pending futures；源码明确
说明同步方法无法 honour wait。实施时先停止接纳本端新工作、排空/取消本端 active tasks，再关闭 Extension
资源和 scheduler。不能凭 wait=True 推断 Mail 连接清理已完成。

Agent turn/tool batch 使用正常 asyncio 取消传播。Mail to_thread 的线程不会随 awaiter 取消而停止，
其私有 task/锁/断连顺序及重复取消、异常保留已通过 [隔离实验](preflight-runtime.md)。本轮只在 Mail adapter
加入这项清理和 IMAPClient 原生有限 connect/read timeout，不创建通用强杀线程机制。

已有 expire_overdue 仍可能先于另一个 Peer 的清理结束关闭超时记录，这是 best-effort 的既有边界；不新增
executor lease、重领或回滚。`aborted` 表示本端执行已退出；`abort_requested` 本身不证明外部副作用已撤回。

显式整理 Job 使用 `core.organization.rumination.explicit.v1`，输入是 block。
handler 接 `RuminationBehaviorResolver.ruminate_local`，不经可再次委托的领域 facade；目录属于 Core Job
owner，不把任何 Extension 类型加入 builtin catalog。缺实体等执行错误沿普通 Job 结果报告。
