# CLI 本地文件引用与导出回执

状态：2026-09-13 按 [D-586](../../decisions/D581-D590.md) 获确认，尚未实现。沿用 D-578/D-579 的内容交付与紧凑 JSON；D-584/D-585 已确认
HTTP 传输。本文只讨论本机交付，不改变 Resolver、Storage、HTTP 表示或服务器资源生命周期。

## 用 file 表达已保存的本地副本

CLI 对已取得的 bytes 写文件，再在对应结果位置输出 `{"file":"路径"}`。它只是 CLI 的文件交付表示，
不添加 type/status/size 等重复字段，也不把路径伪装成原始字符串或 Storage pointer。stdout 的路径为绝对路径。
根 bytes 使用同一表示；结构化结果保留其它字段与对象/数组边界。例如：

```json
{"content":{"file":"/tmp/inkcre-example/001.bin"},"width":640}
```

示例路径并非当前机器的实际落点。普通字符串、数字、null、对象不因内容像路径、Base64、JSON 或 file 引用
就被重新解释。只有 HTTP raw bytes 或 multipart 关联所明确标记的 bytes 位置会生成本地副本与引用；不导入
Extension schema，不根据 content 字段名决定文件化，不重新调用 Resolver。

这里保留一个已确认的取舍：file 是输出约定，不是可逆的类型编码。如果业务数据本来恰好是同形的
`{"file":"…"}`，仅凭最终 CLI JSON 无法证明它原本是对象还是 bytes。CLI 不解析这种对象为文件指令，
不提供自动反导入、自动跟随路径或完整 Python 类型往返。需要准确保留 bytes 类型的程序仍可使用已确认的
HTTP 关联合同。D-586 接受这个呈现层残余，不为它新增全结果 envelope、保留词转义或文件索引。
这明确了 content-delivery 中“文件引用与业务字段区分”的实际边界，不宣称任意结果都可反向恢复类型。

## 显式导出仍返回一个入口文件

`--output-dir DIR` 在指定目录内创建本次调用的子目录，并根据根值保存入口文件：

| 根值 | 入口文件 |
| --- | --- |
| str | result.txt，保存正文，不增加 JSON 引号 |
| bytes | result.bin，保存原始字节 |
| 其它 JSON 值，包括对象、数组与 null | result.json，保存完整紧凑 JSON；嵌套 bytes 使用 file 引用 |

JSON 中的 binary 文件可用编号命名，例如 001.bin，不以业务对象的键拼接路径。没有可靠的文件类型信息时
保留 .bin，不为文件命名增加解析器或内容分类 ladder。编号不成为领域身份，不做按内容去重。

stdout 只需给入口文件回执，JSON 形式为：

```json
{"file":"/work/evidence/inkcre-example/result.json"}
```

不再重复目录、文件总数、success、所有 binary 路径或已经保存在入口 JSON 中的 metadata。文件引用位于
原结果中的位置，调用者打开入口文件即可继续使用。这是显式导出操作的回执，不用于包装普通 JSON 结果。

保存到 result.json 的引用相对于该 JSON 文件，stdout 直接呈现的引用则为绝对路径。例如保存文件中的
`{"content":{"file":"001.bin"},"width":640}` 可以随整个目录移动。只变更本次生成的文件引用，不改写
业务原有路径字符串；不需要把显示输出再解析一遍来寻找 file 字段。

## 与默认输出的连接

未给 output-dir 时，仅在 bytes 或可读输出超预算时创建 OS 临时目录；进程结束后仍保留供后续工具读取。
可读输出超预算时按相同入口文件规则保存完整值，再给有限预览与入口路径。`--json` 的字符串和对象不因
大小切换为导出回执，也不截断内容；只有实际 bytes 被替换为 file 引用。

目录、路径与文件写入使用标准库即可，不创建缓存数据库、TTL、下载服务或 CLI 专用阅读器。写入失败不
返回成功回执；报告实际错误及已产生的目录，不隐式重执行内容方法，也不引入文件写入回滚服务。

实现前在脚本化黑盒核验中覆盖 text、根 bytes、嵌套 bytes、批量 hydrated、空 bytes 与目录整体移动后的
文件读取。这里只列验证面，尚未创建输出文件、源码或自动化测试。方案按 ponytail 收敛本地文件交付职责。
