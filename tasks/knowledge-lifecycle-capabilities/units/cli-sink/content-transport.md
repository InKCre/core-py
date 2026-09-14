# 内容的 HTTP 表示

状态：2026-09-13 按 [D-584/D-585](../../decisions/D581-D590.md) 确认 JSON / 原生 bytes / multipart 路线及
multipart 字段关联。MessagePack 是未选方案。D-583 的实体/Resolver 逻辑结果保持不变；本页不定义本地
文件引用或导出回执，也不表示完整端到端实现已验证。

## 压力来自动态 bytes，不只是响应大小

一个 Resolver 可以返回 text、null 或含多个 bytes 成员的对象。仅把 bytes 序列化为 Base64 字符串能够保存
字节内容，但在没有具体输出 schema 时，通用消费者无法仅凭值区分它与普通字符串。CLI 又不能复制每种
Extension 的结果模型，或根据 content/data 等字段名猜哪些字符串应当解码为文件。

需要分别判断返回值本身是 bytes，还是它是含 bytes 的结构化对象。前者不需要任何对象序列化格式；后者
才需要关联结构与二进制成员。不能从 nested bytes 直接推出所有内容结果都应该使用 MessagePack。

## 原生 HTTP 路线：按结果形状选择表示

| 实际返回值 | 原生表示 | 保留的语义 |
| --- | --- | --- |
| JSON 可表达的值（含字符串、null） | application/json | 不替内容字符串猜 JSON、HTML 等格式 |
| 返回值本身是 bytes | application/octet-stream | body 就是原始 bytes，不编码为 Base64 |
| 对象或数组中包含 bytes | multipart/related | JSON 结构与多个 binary part 在同一响应中传输 |

单独 bytes 通过 FastAPI Response 即可发送；已有 iterator/file 时可以使用 StreamingResponse/FileResponse。
Content-Type 声明 body 的表示，不是开启流式的开关。JSON、MessagePack、multipart 都可以通过 HTTP 流传输；
是否降低内存还取决于 producer/consumer 是否逐段处理。当前 Storage/Resolver 已先形成完整 bytes，不能
只换响应类就宣称端到端常量内存，也不为此扩展 Storage/Resolver 的 streaming API。

裸 binary 默认使用 application/octet-stream，避免把本来是 bytes 的 JSON/HTML 文件误当普通结构化结果。
若以后使用真实文件 MIME，应同时明确文件交付标记与解码合同；不能只看 MIME 等于 application/json 就丢失
其 byte 语义。Content-Disposition 可表达已有 filename，但不是承载任意业务 metadata 的地方。

含 bytes 的 solved content 不能简单抽出 `.content` 返回，因为这会丢失同次结果里的宽高、描述等字段。
例如 ImageSolvedContent 继承 ByteContentFacts，既有 bytes，也有 byte_size/detected_media_type 和 image facts。
即便 get 只请求一个 Block，返回值仍是已确认的记录数组；若 hydrated_content 是 bytes，也属于结构化情形，
不能为了直接下载把记录或数组边界去掉。

multipart/related 是复合对象的一次 HTTP 响应，不是多个请求。一个 JSON part 保存结果结构，另外的 part
保存 bytes；同一个 Resolver 结果可以同时交付 metadata 和全部 binary，不需要缓存服务端结果或再次读取。
MIME 的 boundary / Content-ID / part Content-Type 已有标准，**JSON 成员位置如何对应 part 仍是应用合同**，
由下文的关联表表达，不能声称协议已自动恢复任意 Python 对象。不能靠猜 content/data 字段或业务字符串等于 cid
来识别 binary。RFC 2387 对根 part 的 type/start 机制不代替这个字段关联合同。

实现可复用 aiohttp 的公开 MultipartWriter/MultipartReader（当前环境已有 3.14.3，仍是传递依赖）。进一步的
[依赖选型与局部实验](project-and-dependencies.md) 已按 D-598 确认 Core 使用 MultipartWriter，CLI 通过 HTTPX 接收并用
标准库 BytesParser 读取；已核验这条局部路径的 bytes 保真，完整端到端验收仍待实施。采用 aiohttp 时需
在 Core 显式声明依赖，不把“采用 HTTP 原生格式”描述成“标准库和现有框架已经无成本实现全部功能”。

## Multipart 字段关联（D-585）

multipart/related 的第一个 part 为 application/json，保存两项：value 是原结果结构，其中 bytes
位置暂以 null 占位；parts 是相对于 value 的 JSON Pointer 到 binary part Content-ID 的映射。外层响应使用
`multipart/related; type="application/json"; boundary=…`。既然 root 固定为第一个 part，不再增加 start 参数。

例如 Resolver 原本返回含 content bytes 与 width 的对象，JSON root 为：

```json
{"value":{"content":null,"width":640},"parts":{"/content":"body-1@inkcre"}}
```

另一个 part 声明 `Content-ID: <body-1@inkcre>` 与 `Content-Type: application/octet-stream`，body 就是原始
bytes。示例 ID 只表示两端如何关联；实际 ID 由 MIME 编码侧生成，不是 Block ID、下载 URL 或持久资源。
CLI 用映射将 part 关联回字段，不依赖 part 到达顺序、字段名、文件名或字符串恰好像 cid。

JSON Pointer 使用 RFC 6901 的现成语法：例如 get 批次第一条记录的 hydrated_content 对应
`/0/hydrated_content`，对象键中的 `/` 与 `~` 使用标准转义。没有映射的 null 仍是普通 null；空 bytes
仍有自己的 binary part。value 内本来就存在 value/parts 字段、cid 字符串或类似文件标记的普通对象，也不会
被误当传输控制。这是把关联信息与业务值分开的目的，不是让 Resolver 追加特殊字段。

这层两字段封装只用于 multipart 的 HTTP 表示。没有 bytes 时仍直接返回原 JSON；纯 bytes 仍直接响应。
接收端恢复逻辑结构，CLI 再按已确认规则将 bytes 保存成本地文件，原 metadata 与数组根形状不变。封装本身
不透传为终端的 result/status 外壳，也不成为 Resolver 返回模型或所有 Core API 的统一 envelope。

代价是原始 HTTP 消费者需要理解这份小型关联合同；multipart 标准不会自动完成它。相较于在业务 JSON 中
保留特殊 sentinel 对象，显式映射不占用业务值的合法形状；相较于另造 HTTP header 承载字段路径，JSON root
可以直接表达 Unicode 路径和结构化映射。MIME 分帧与解析交给库，仅保留 InKCre 必需的字段关联适配。

已完成的局部 HTTP 实验只验证 part 传输，未验证完整字段关联。后续预演需通过真实序列化边界核对嵌套
对象/数组、空 bytes、普通 null 与特殊字符键，不为本合同新增自动化测试或扩展到任意 Python 对象。

## 与其它路线比较

| 路线 | 优点 | 实际代价或不足 |
| --- | --- | --- |
| 原生 binary + multipart | 文件 bytes 不转码，普通 HTTP/MIME 工具可处理，CLI 可逐 part 落文件 | 需要定义嵌套字段与 part 的关联；HTTP 客户端不一定自动解 multipart |
| JSON + Base64 | 单一 JSON 响应，Pydantic 原生支持 | bytes 通常约增加三分之一体积；动态字段的 byte 类型需 schema 或额外类型信息 |
| MessagePack | 对象内原生区分 str/bytes，整体往返代码较少 | 消费者需要 codec；不能像 JSON 直接查看，也不自动解决 streaming/大文件 |
| JSON + 独立下载链接 | 适合本来就独立可寻址的稳定文件 | 任意 Resolver 本次返回值并非既有下载资源；会引入快照生命周期或重执行，当前不推荐 |

按 D-584 选择原生 binary + multipart：它与文件交付目标相符，也使普通 REST 消费者不必使用专用对象
codec。这是可读性、互操作与关联合同成本的取舍，不声称比 MessagePack 更少代码。MVP 不同时维护两套
等价路径；上一轮可行性证据仍保留，但不是执行计划。

## 未选 MessagePack 方案与序列化证据

上一轮提案仅为 entities/get 与 Resolver invocation 增加 Accept 协商：JSON 的 bytes 为 URL-safe Base64，
CLI 选择 application/msgpack 保留原生 str/bytes 区别。它避免在业务 JSON 中放特殊标记，但消费者需要 codec。
当前锁与实际 PDM 环境已有 msgpack 1.2.1，来源是 logtail-python 的传递依赖。这不构成采用理由；D-584
之后不为内容传输新增 msgpack direct dependency，也不添加该候选所需的 python-mimeparse 协商依赖。

模型/dataclass 转换为普通结构，日期等维持现有 JSON 风格的字符串，bytes 保留至编码器。局部实验使用
`TypeAdapter(Any).dump_python(..., mode="python")`，再用 `msgpack.packb(..., use_bin_type=True,
default=to_jsonable_python)` 与 `unpackb(..., raw=False)`；这是可行性证据，不是已冻结的通用序列化实现。
实际 Resolver 返回值、别名与既有序列化器仍需在实现预演中核对；不承诺支持任意 Python runtime object。
Pydantic 继续用于模型投影与稳定 DTO；当前选择不需要可插拔 codec registry，HTTP 失败仍可返回既有 JSON
错误体。CLI 按 HTTP 状态及 Content-Type 处理响应，不因表示不符隐式重发可能 materialize 的 Resolver 调用。

## 局部核验与证据

2026-09-13，在当前 PDM 环境（FastAPI 0.139.2、Pydantic 2.13.4、msgpack 1.2.1）执行了一次无文件、无网络
的内存 codec 实验。样本包含嵌套 model/dataclass、0–255 全字节集合、空 bytes、Unicode、datetime、null，
以及形状类似 `{type: "bytes", data: "AA=="}` 的普通 authored JSON。往返后 byte 值与字符串类型正确，
普通对象没有被当作特殊标记。编码样本为 376 bytes，对应紧凑 JSON/Base64 为 500 bytes；这不是吞吐/性能基准。
没有新增测试文件、业务代码或依赖，也未进行 HTTP / preview 端到端验收。

同日补充一次临时 FastAPI + HTTPX ASGITransport 内存 HTTP 实验：Response 直接返回原始 bytes；另一端点用
aiohttp.MultipartWriter 生成 multipart/related，经 StreamingResponse 返回。使用标准库 email.BytesParser
读取 JSON 与两个 binary part，核对 0–255 字节、混合 CR/LF、空 bytes、Unicode 均保留，且未使用 Base64。
这个实验验证了原生响应与 multipart byte 传输可行性，没有定义最终 JSON 位置关联，也没有验证逐 part
落盘的内存特征、真实网络代理或部署。全部在内存完成，无新增源码/测试文件、依赖或数据库动作。

一手依据：

- [MessagePack specification](https://github.com/msgpack/msgpack/blob/master/spec.md)：原生 String/Binary、Array/Map 类型。
- [msgpack Python API](https://msgpack-python.readthedocs.io/en/latest/api.html)：packb/unpackb 与原生类型选项。
- [FastAPI JSON with Bytes as Base64](https://fastapi.tiangolo.com/advanced/json-base64-bytes/)：Pydantic 支持 bytes 的 JSON Base64 表示。
- [RFC 9110 Accept](https://www.rfc-editor.org/rfc/rfc9110.html#name-accept)：响应表示协商。
- [python-mimeparse](https://github.com/falconry/python-mimeparse)：媒体范围和 quality 匹配能力。
- [FastAPI responses](https://fastapi.tiangolo.com/advanced/custom-response/)：Response、StreamingResponse 和 FileResponse。
- [RFC 9110 multipart types](https://www.rfc-editor.org/rfc/rfc9110.html#name-multipart-types)：同一 HTTP body 中的 multipart。
- [RFC 2387](https://www.rfc-editor.org/rfc/rfc2387.txt)：multipart/related 的 root 与复合对象机制。
- [RFC 6901](https://www.rfc-editor.org/rfc/rfc6901.html)：JSON Pointer 对对象成员/数组元素的标准定位语法。
- [aiohttp multipart](https://docs.aiohttp.org/en/stable/multipart.html)：MultipartWriter/MultipartReader 公开 API。

本轮通过 python-backend-code 核对原生 HTTP 边界，并按 ponytail 补齐标准协议与成熟库的比较。上一轮从
“nested bytes 需要类型区分”过早跳到了 MessagePack，遗漏了裸 binary 与 multipart 应分别评价的适用面。
传输路线及关联合同现已确认；本地文件引用与导出回执在 [文件输出](file-output.md) 中复核，不把后两者混成 HTTP 协议字段。
