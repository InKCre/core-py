# 管理列表与错误输出

状态：按 [D-597](../../decisions/D591-D600.md) 确认，并将长输出分页明确为各查询指令的通用模式。
这里只补各已确认命令共同需要的结果边界，不改变领域业务，
也不授权源码实施。当前包版本为 FastAPI 0.139.2、Pydantic 2.13.4。

## 分页依据输出规模，而非领域白名单

长输出分页适用于各查询指令，不能限定为 Job 历史特例。共同依据见
[通用模式](../../common-patterns/agent-tools.md)：让调用者按预算逐步读取，同时保留准确结果边界与续读位置。
不同查询复用各自 owner 的机制，不因此要求同一种 cursor 或新建通用分页框架。

本轮的 Source、Cron、Agent definition、Peer、Extension、deployment config、AI model、embedding profile
列表，以及 Source/Job type、Resolver、Agent Tool、config schema 目录，默认完整返回当前小清单，不设隐藏
截断。D-600 补齐可选分页，并将枚举结果从裸数组改为“领域清单 + next_cursor”；具体合同统一见
[查询续读](query-continuation.md)。不靠全局 total/Page 抽象解决，也不改变列表元素的既有 DTO。

列表元素保持各页已确认的 DTO，不为分页讨论重做字段投影。按自然 identity（id、key 或 Extension coordinate）
升序输出，不引入任意字段排序 DSL；默认可读呈现可以只显示选择所需列，JSON 保留完整列表结果。

## Job 历史的具体落点

Job 每次派发都会增加记录，GET /jobs 使用 limit 与 cursor，CLI 为：

```sh
inkcre-cli job list --limit 20 --json
inkcre-cli job list --limit 20 --cursor 281 --json
```

按 id 降序取最近分配的记录；cursor 为上一页最后返回的 Job ID，下一页选取 id < cursor。limit 默认 20，
使用正整数，不额外发明一套 opaque cursor 编解码。type/status 过滤沿 D-587，翻页时由调用者保留同一过滤。

HTTP 与 CLI JSON 结果为 `{"jobs":[...],"next_cursor":281}`；没有更多记录时 next_cursor 为 null，空表则
为 `{"jobs":[],"next_cursor":null}`。数据库取 limit + 1 行判断是否还有下一页，不计算 total，不开启跨请求
snapshot，也不增加 --all 或自动遍历整个历史。默认可读输出同样显示下一页位置，不能悄悄忽略续页信息。

ID 是分页位置，不等于提交时间的严格先后。新分配的 Job 不会挤动较旧页的位置，但并发提交、状态变化或
删除仍会改变后续查询可见集合；这是一组实时列表查询，不是历史快照。没有因此引入 version 或游标存储。

图邻域已有 next_cursor；graph path/components 和 lexical/semantic retrieval 各有自己的查询边界。
查询范围与结果交付分页不是同一参数，不能用翻页暗中增加 top-k 或扩大图探索。长文本/多模态仍沿已确认的
完整内容文件交付，不能为取得下一段而重新执行 Resolver。这里不把文件交付冒充新的查询分页协议。

## 普通 HTTP 沿用既有错误表达

HTTP 错误保留 FastAPI 的 `{"detail":...}` 形状。输入校验沿 Pydantic 的 loc/msg/type 等原生字段，保持结构，
不把整份 ValidationError 压成无法定位的单个字符串，也不为 CLI 建立 Core 全局错误码表或新的错误中间件。

准确的异常映射在相应普通 REST 边界完成：输入不合法使用 422，目标不存在使用 404，已有状态冲突使用
相应 409；保留实际 HTTP 状态和领域原因，不将所有 ValueError/IntegrityError 机械映射为同一状态。
Unexpected errors 保持真实 5xx 与服务端 traceback，不吞掉异常、伪装成功或扩大为全库错误体系重构。

只有本次请求输入的验证失败才转为 422；不能把方法内部或输出处理中的 Pydantic 错误伪装成用户输入错误。
动态输入由现有 owner 验证，REST 边界只补上真实请求层级。例如 Job parameters 的 source 错误应在
body.parameters.source，而不是 body.source。这是路径投影，不是第二次验证。

## CLI 的输出流与退出码

成功结果在 stdout，失败诊断在 stderr。已知的调用错误在 --json 下输出一条紧凑诊断对象；HTTP 错误保留
http_status 与 detail，本地输入、连接或文件错误没有 http_status。CLI 不为每种领域增加退出码或重试策略。

CLI 将结构化校验 loc 投影回调用者实际提交的位置：config replace 的 JSON 是 value 本身，不能提示调用者
在输入文件中凭空补一层 value；argv selector 的错误则指向对应参数。只沿该命令已知的 HTTP 映射增删路径
前缀，不自制校验解释器，不解析错误消息来猜字段。其它 Pydantic 字段和服务端原因保留。

例如 config replace 的某个字段错误可以在 stderr 表示为：

```json
{"http_status":422,"detail":[{"loc":["agent"],"msg":"Input should be a valid integer","type":"int_parsing","input":"abc"}]}
```

若对端返回的不是 JSON，诊断保留其状态与实际文本，而非改称“连接失败”。响应已取得但文件保存失败也应
报告实际交付故障，不自动重复 Resolver 调用。未预料的 CLI bug 保留原生异常诊断，不为了漂亮错误体而
全局捕获并隐藏 traceback；结构化的已知错误合同不等于所有内部日志都必须变成 JSON。

| Exit code | 意义 |
| --- | --- |
| 0 | 本次命令正常完成，包括空检索、没有路径、读取到 failed Job 或 wait 正常用尽观察预算 |
| 1 | 请求、执行或内容交付失败；也包括已声明批次中存在逐项错误 |
| 2 | CLI 用法或本机输入校验失败，尚未发出业务请求 |
| 130 | 用户中断 CLI；不因此中断已经受理的远端 Job |

HTTP 422 属于接入 Core 对请求的拒绝，退出 1；本地 argv/JSON 输入校验失败才退出 2。help/schema 成功查询
正常退出 0。HTTP 204 没有业务结果，默认不输出成功包装，JSON 模式输出 null。

批次保留 D-583/D-594 的逐项结果：某项缺失或某种 recall mode 失败时，成功项和失败项都留在 stdout，
最终退出 1。stderr 只需说明存在逐项错误，不再复制整份结果，也不自动重跑成功项。即使全部项失败，仍
保留相同批次形状。整批共享的 HTTP/连接故障没有批次结果，stdout 留空，诊断在 stderr。

只有 CLI 自己已声明的批次错误变体参与这个判断，不递归搜索任意 Resolver 输出中的 error/status 字段。
读取到 Job.status=failed 与该次读取失败不同；同样，业务结果中的 not_found/limit_reached 不是默认的
命令失败。输出结果后仍可非零退出，调用者不能因 exit 1 就假设没有任何成功项或实际效果。

## 依据与实施前检查

- app/schemas/job.py 的 JobModel.id 为数据库分配的 bigint PK；当前 JobManager 没有面向历史列表的接口。
  对应带过滤和 cursor 的查询应留在 JobManager，不把 SQL 放入 route。
- app/business/peer/main.py::get_all 与 app/routes/extension.py::list_extensions 已返回完整清单；其它
  管理列表仍需在各 owner 接出，不能以现有 HTTP 缺口推定必须建设通用 query/repository 层。
- app/routes/deployment_config.py 与 extension.py 已使用 HTTPException(detail=...) 和 Pydantic errors；
  其中重复读库校验的修正归 D-591，本页不改变该边界。
- [FastAPI 错误处理](https://fastapi.tiangolo.com/tutorial/handling-errors/) 提供 detail 与默认异常 handler；
  [Pydantic 错误结构](https://docs.pydantic.dev/latest/errors/errors/) 已能表达字段路径与原因。
- [gh run list](https://cli.github.com/manual/gh_run_list) 默认限制最近 20 次执行，是限制历史查询而非裁剪内容
  的参考；不复制其 workflow 特有过滤。我们的 cursor 是本地合同选择，不宣称 gh 使用同一 API。
- [gh 的退出码](https://cli.github.com/manual/gh_help_exit-codes) 将取消定义为 2、认证需求定义为 4；本方案
  不照搬，而为 Python CLI 保留用法错误 2、中断 130，HTTP 认证状态仍可由诊断读取。库选型需核对实际适配。

后续预演检查一次完整 stderr/stdout/exit-code 组合、分页 SQL 与路径投影；优先静态机制，必要时做隔离
脚本实验或真实黑盒 journey。不为结果包裹、字面值和字段映射新增自动化测试。

长输出检查应覆盖管理/能力清单、Job 历史、Recall、图查询、批量实体和 Resolver 结果，分别标明查询分页、
本次结果的分批呈现或完整文件读取。只核验 Job cursor 不能证明已经满足 D-597 的通用长输出原则。

逐项覆盖与清单响应调整已按 D-600 确认，见[查询续读](query-continuation.md)。错误、退出码和 Job 分页
决定保持；旧裸数组形状仅对这些枚举接口被明确替换。
