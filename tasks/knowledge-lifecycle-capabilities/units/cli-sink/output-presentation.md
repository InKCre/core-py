# 结果呈现与可组合性

状态：输出原则已获 [D-578](../../decisions/D571-D580.md) 确认；D-579 确认大内容交付与紧凑 JSON；
D-597 已确认错误/退出码合同，并将长输出分页与部分失败处理提炼为通用模式。
本页先决定默认呈现、机器可用结果，以及它们必须保留的业务信息，不设计所有命令的渲染模板。

## 按结果语义呈现，显式选择 JSON

默认输出供 Human/Agent 阅读的内容，`--json` 返回该命令稳定的结构化结果。不能仅凭 stdout 是否为 TTY
判断消费意图：Agent 常通过 pipe 捕获 stdout，但仍可能更适合阅读普通文本。TTY 只影响颜色等终端表现，不
切换结果格式、字段语义或业务行为。默认不启交互 pager，不让脚本因为等待按键而停住。

| 结果 | 默认呈现重点 |
| --- | --- |
| Recall | 可继续寻址的实体引用、命中依据/已有摘要、所属检索模式；保留模式内顺序，不把异质分数伪装成统一尺度 |
| `get` | 明确实体种类的记录字段及调用者选择的 content；不额外调用 Resolver 生成解释 |
| Graph query | Block/Relation 引用、实际方向、relation content 及查询边界，不展开整幅图的 solved content |
| Resolver method | 单项字符串保留自然文本；对象/数组保留 JSON 结构，不为每种 Resolver 增加 CLI renderer |
| 管理列表与详情 | 列表提供选择所需的 ID 与关键字段；详情保留该对象的实际配置和状态 |
| 写入与执行控制 | 返回真实创建/修改的对象引用、必要结果；区分 Job 创建、运行与结束，不添加无信息量的成功包装 |

默认可读不意味着每条命令都必须把 JSON 再翻译成散文。JSON 本身合适的结果可以直接呈现 JSON；已经返回
文本的 Resolver 方法也不需要为了可读而改写文本。多项结果必须保留逐项身份，不能拼成失去归属的一段正文。

`--json` 提供正式的脚本消费合同，不是提取终端表格，也不是承诺透传任意 HTTP body。它保留该命令的领域
结果及可继续操作的引用；批量入口不因只有一个结果而临时改变顶层形状。具体 DTO 在命令级设计，不套一层
通用 `{success, data, metadata, next_actions}`。按 D-598，CLI 信任 Core REST 的业务返回，只解码与转换，
不调用 Pydantic 响应校验；也不能在转换中静默丢失需要交付的字段。

JSON 模式不做 pretty print，使用紧凑序列化。格式紧凑不改变字段、内容完整性或业务语义；默认可读输出
不由这条机器格式要求反向决定。

## 格式选择不改变事实

普通输出和 JSON 都必须保留对调用者决策有用的边界：是否截断、下一页位置、没有匹配、缺失引用、搜索上限，
以及真实 Job 状态。默认摘要与完整记录有不同目的，但不能把摘要描述成完整信息，也不能只在 JSON 中告诉
调用者还有未读内容。不得为了排版整齐把两个状态合成一个“失败”。

实际依据：`app/schemas/graph_navigation_retrieval.py` 的 path result 区分 `not_found` 和 `limit_reached`，
neighborhood 有 `next_cursor`；`lexical_retrieval.py` 的 match 有 evidence/excerpt/rank，semantic 的 score
具有自己的 profile/metric 语义。CLI 呈现不能消除这些区别，也不要求 domain 为终端输出重新定义结果。

同一实体在多个 recall mode 中命中、get 的 raw/hydrated 默认选择与批次 DTO 已分别由 D-583/D-594 确认，
详见相应命令合同。本页不另建一份形状 authority。

## stdout 是结果，stderr 是过程

stdout 只放该次命令的结果；连接过程、等待进度和诊断走 stderr，不能污染重定向得到的 JSON 或原文。
错误仍保留能定位问题的原因；分流不意味着消音或损害可观测性。

支持 stdout 重定向与既有 `--input -` 的组合，但不声称任意前一命令结果都能原封不动作为下一命令输入。
例如 Job 返回记录与下一次命令接收的 Job ID 是不同形状；可脚本消费的稳定字段足以组合，不因此增加内嵌
jq、模板语言或另一套管道协议。字段名与引用保持一致，不要求 Agent 猜别名之间的对应关系。

批次的成功项和失败项仍在结果中保留关联，日志不代替结果。退出码表达 CLI 调用的完成语义，不把所有领域
结果都折叠为布尔值。限时 wait 返回 running 不是错误；Job 失败与观察 Job 成功是不同事实。准确 exit code
规则及批次部分失败的呈现已按 D-597 确认，见 [管理列表与错误输出](list-error-contract.md)。分页与部分失败的
共同依据维护于 [common patterns](../../common-patterns/agent-tools.md)，不是仅适用于 Job 或某一种 Recall 的特例。

## 大内容与多模态交付

文本、bytes 与嵌套多模态结果不能只靠 `--json` 解决。已确认的 [内容交付](content-delivery.md) 区分有限呈现、
完整内容保存与文件寻址；具体 [HTTP 编码](content-transport.md) 与 [文件输出](file-output.md) 已获
D-584–D-586 确认。默认输出不能悄悄丢内容，也不能把 binary 强行 decode 为文本。

技术复用按 ponytail 核对：领域结果与引用已有 owner，Pydantic 留在自有输入边界。CLI 只需要适合终端的呈现与
必要交付，不建立第二套业务完成状态，也不为默认可读输出引入完整的渲染插件体系。
