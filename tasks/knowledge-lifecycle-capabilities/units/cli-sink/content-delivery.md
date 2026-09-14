# 大内容与多模态交付

状态：产品方案已获 [D-579](../../decisions/D571-D580.md) 确认，沿用 D-578 输出原则。这里只设计调用者如何取得完整结果，不冻结 HTTP
编码、文件引用 DTO、具体显示预算或命名算法。[HTTP 表示](content-transport.md) 的 JSON / 原生 bytes /
multipart 路线与字段关联已按 D-584/D-585 确认。[本地文件输出](file-output.md) 已按 D-586 确认，包含接受
文件引用不是可逆类型编码的取舍；具体显示预算与完整链路预演仍待完成。

## 保持内容语义，改变交付载体

CLI 不要求所有 Resolver 最终都返回 text，也不替它们重新解析内容。Core 的实际结果可能是 str、bytes、
嵌套 dict/list、Pydantic model 或 dataclass。CLI 的文件是这次读取结果的副本，不是新的 Block、Storage
或 Resolver 类型，不写回 info-base，也不制造永久可寻址的 Core result entity。

| 调用 | 交付的内容 |
| --- | --- |
| `get … --content raw` | 原始记录内容；若它是 Storage pointer，仍交付 pointer 字符串，不自动下载其指向的文件 |
| `get … --content hydrated` | 通过 Core 的 Block/Storage 取得实际 str/bytes，不添加 Resolver 的解释 |
| `resolver invoke … --method get_solved_content` | 交付 Resolver 返回的完整结构，包括可能存在的元数据与嵌套 bytes |
| `resolver invoke … --method get_text` | 交付该方法返回的文本或 null，不宣称其等于文件的全部原始信息 |

get 的模式和默认 raw 已按 D-583 确认。文件交付不能把 hydration 偷换成 text extraction，也不能为了决定文件
名额外调用 Resolver 读取方法。CLI 仍从 Core REST 取得内容，不根据 raw pointer 自行连接 Storage 或外部 Source。

## 可读输出有限呈现，完整内容可落为本地文件

短文本和小型 JSON 可以直接输出。默认可读模式下，长文本或过大的结构化结果保存到本次调用的本地输出
目录，stdout 给出明确标为预览的有限内容和完整文件路径。文件保存的是本次取得的结果，不需要 Agent 再
调用一次 Resolver 才能取回未显示部分，也不会因为终端预览而重新生成摘要、OCR 或转录。

二进制结果保存为文件，无论它位于根部还是嵌套在 solved content 中。原有对象/数组结构及非二进制字段保持
可读，文件引用保留它所属的位置；不能只交付一个孤立的图片文件而丢失同次结果里的宽高等字段。D-586
使用 file 对象，不把路径伪装成原始 content 字符串或 Storage pointer；接受它与普通同形对象无法仅凭
最终 JSON 反向区分的呈现层残余，CLI 本身不将业务对象误当文件指令。

这种策略有一个明确的本地副作用：读取命令可能写临时文件。命令 help 与返回结果都应说明落点。默认
只在确实需要文件时创建 OS 临时目录，CLI 退出时不立即删除，便于 Agent 后续使用文件工具。临时目录不是
永久保存承诺；需要长期保留时由调用者指定输出目录。CLI 不增加缓存索引、TTL 服务、自动清理任务或新的
`cache` 命令。

## 显式导出使用一个目录，容纳异构与批量结果

提供 `--output-dir <directory>`。显式使用时保存完整结果，不受终端显示预算影响；一次调用使用其中的
独立子目录，返回实际文件路径。目录可以同时容纳结果 JSON、原始文本和多个二进制文件，调用者无需预先
判断 Resolver 将返回一个文件还是一个带多个文件的对象。不让同一个路径参数按结果类型隐式变成文件或目录。

```sh
inkcre-cli resolver invoke block:42 --method get_text --output-dir ./evidence
inkcre-cli resolver invoke block:84 --method get_solved_content --output-dir ./evidence
inkcre-cli get block:84 --content hydrated --output-dir ./evidence
```

文本本身保存为文本，不为了包装成 JSON 而改写正文。对象/批次保存完整 JSON 结构，binary 成员通过文件引用
连接。文件类型来自已有可靠内容元数据；没有时仍保存 bytes，不另建识别 ladder。文件与成员的关联不能只靠
人类猜文件名，也不自动解开 ZIP、生成媒体摘要或下载返回结构之外的附件。

显式导出时 stdout 返回这次导出的路径与必要回执；`--json` 选择回执的结构化形式。这个回执属于显式文件
交付操作，不推广成所有 CLI 命令的统一 envelope。确切文件引用与回执 DTO 见已确认的 [文件输出](file-output.md)。

## `--json` 不截断正文或改变根形状

未指定 `--output-dir` 的 `--json` 调用返回完整结构化结果：字符串不因默认终端显示预算而被截成另一段
字符串，大对象也不突然整体变成一个文件路径对象。需要保存大量 JSON 时可以直接重定向 stdout，或显式
使用上述目录导出。选择 JSON 不等于承诺结果体积有限；检索数量、是否请求 content 等仍由命令参数控制。

JSON 模式使用紧凑序列化，不做 pretty print；这一点也适用于 `--json` 下的导出回执。不为了缩进或排版
增加输出体积，也不把紧凑格式误解为裁剪业务内容。

二进制在 JSON 结果中一律使用声明过的文件交付表示，不把 bytes 猜成 UTF-8，不默认塞入大段 Base64。
这一表示不随文件大小改变；小 binary 也遵循相同合同。普通输出与 JSON 都指明文件位置与实际交付情况。
读取/写文件失败仍需报告实际故障，不能返回不存在的“已保存”文件。

“完整”只指本次 Core 方法的返回值。它不证明上游信息完整、Storage 未被外部改写，或 Resolver 内部没有自己的
能力边界。Domain 提供的截断或 unavailable 等信息应原样保留，CLI 不把文件导出宣传为消除这些边界。

## 现有证据与技术压力

`ImageSolvedContent`、`AudioSolvedContent`、`PDFSolvedContent` 继承 `ByteContentFacts`，同时含 `content: bytes`
与描述字段；`TextResolver` 可将 storage-backed bytes 解码为 str。这说明 hydrated 与 solved 的区别是实际
合同，不能靠 MIME 或 CLI 展示偏好合并。见 `app/business/info_base/resolver/{image,audio,pdf,text,inspection}.py`。

`app/business/sink/projection.py` 已遍历 model/dataclass/JSON 并发现 bytes，MCP 据此构造 Resource 引用；但其
URI 与 live re-read 是 MCP 交付方式，不直接带入普通 REST CLI。可复用的遍历/序列化部分需要按 owner 重新
评估，不能直接 import 整个 MCPSink，或把 MCP Resource 当普通下载 URL。

本方案要求“文件副本来自本次已执行结果”，因此技术设计必须核对 binary/复杂返回通过 REST 到 CLI 的实际
传输，避免仅为保存再执行一次可能 materialize 的 Resolver method。优先利用成熟 HTTP/序列化支持，不预设
结果表、持久服务端快照或新的 Result Manager。若现有机制不能承载，应在 preflight 前形成明确技术方案。

本轮使用 ponytail 核对的是交付责任：普通本地文件可供 Agent 已有工具读取，不引入特制阅读工具；Core
继续拥有内容取得与解释，CLI 拥有本次输出副本和显示。不修改源码或 durable docs。
