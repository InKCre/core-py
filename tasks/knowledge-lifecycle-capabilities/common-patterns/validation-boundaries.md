# 校验跟随输入边界，而不是调用层数

状态：来自 D-590/D-598/D-602 的设计指南；尚未提升为 durable truth。适用于本任务后续设计与实现；具体修正
范围归单元授权，D-591 已将现有同类边界问题纳入 cli-sink。这不是禁止一切运行时检查。

先确定数据从哪里进入、哪一层建立合同，再决定校验位置。外部提交在写入边界按 owner 的 schema 校验；
已经通过该合同持久化的数据，读取时应信任其作为系统内部事实的地位，不因为经过另一个函数、manager 或
协议 adapter 就重新校验同一 schema。数据库约束守住持久不变量，不能用重复应用层验证替代。

类型化读取、反序列化与格式转换有各自的表达职责，但为了类型提示或统一响应形状而重新构造 Pydantic model，
不能成为重验已知数据的理由。实际执行所需的复杂类型恢复按下文的 Python 指南处理。API 的响应类型描述
输出合同，也不要求内部逐层重复进行业务校验。

使用时才成立的条件与写入合同不同，例如当前执行端是否拥有某项能力。此类判断留在实际使用的 owner；
不要借它把所有数据库读取重新定义成不可信输入。导入或迁移确实需要验证时，在对应边界完成，而不是给
正常读路径永久叠加检查。

发现重复校验时，修正建立合同的位置或删去多余检查。不要先让错误的读路径成为障碍，再把“允许正常读取”
包装成一项需要 Human 决策的放宽或特殊豁免。

CLI config 是本次实例：写入校验完整候选，GET 返回持久记录；PATCH 不要求旧值先合法。既有 typed get
目前仍有重复验证，这个实现事实不是应当保留的设计约束；具体类型恢复按 D-602 取舍处理。

D-598 将这个判断明确应用于 CLI 消费 Core REST：跨过 HTTP 不自动产生第二个业务校验 owner。已确认 Core
拥有该返回合同时，CLI 只解码和转换，不因需要类型提示或展示字段就再次验证完整响应。静态类型描述与
运行时校验是不同工具；不必为了禁用一个本不需要的响应 validator，再建无校验对象构造框架。

该指南不等于任意第三方 HTTP 都天然可信，也不删除 JSON/MIME 解码、真实请求错误或不能完成转换时的诊断。
适用性取决于已确认的 authority 与调用边界，不能仅凭数据经过“网络”或“数据库”来机械地增加或删除检查。

## 使用 Pydantic 时，避免重复建立校验边界

D-602 确认取舍，D-603 明确指南应落在 Pydantic 使用方法上，而不只抽象为通用的库选型原则。
Pydantic 同时承担输入约束、Python 类型构造和序列化；应按调用点实际需要的职责使用，而不是每经过一个
manager、adapter 或 persistence layer，就再调用一次 model_validate。

| 调用位置 | 应怎样使用 Pydantic |
| --- | --- |
| 外部输入进入 owner | 按该输入合同验证；FastAPI 已提供相同的 typed Form 时，manager 直接使用，不 dump 后再 validate |
| 内部传递已构造模型 | 直接传递实例；不要为了确认其类型再调用 model_validate，after model validator 仍可能重跑 |
| PATCH 持久配置 | 旧值取 dict，浅层合并 patch，再对完整新值 model_validate 一次；不先验证旧值或先 normalize(current) |
| GET 持久记录或消费可信 REST 返回 | 返回/消费已有 JSON 表示，不为了“再确认合法”加载业务 schema、补默认值或构造完整模型 |
| 执行端确需恢复复杂 Python 类型 | 从持久 JSON 调用一次原生 model_validate/TypeAdapter，得到嵌套模型、SecretStr、日期或 union，随后传递该结果 |
| 简单持久表示转换 | text[] → tuple 等直接转换；无需复用带唯一性/排序检查的写入 validator |

例如配置 PATCH 的次序是：

```python
candidate = {**stored_value, **patch}
config = Config.model_validate(candidate)
# 持久化时用 config.model_dump(mode="json")；本次调用后续直接使用 config。
```

复杂类型恢复允许 Pydantic 附带执行字段约束和 validators，不要求另建无校验模型、递归 decoder 或
Extension decode hooks。model_construct 不会递归恢复嵌套模型，不能机械替换 model_validate；静态 cast
也不完成转换。保留构造的调用点应解释所需的实际 Python 类型，而不是声称数据库又变成了不可信输入。

这项取舍不授权在构造前后叠加“持久值必须再合法”的专门检查，也不要求把原生 ValidationError 再包装成
自有异常。构造失败保留诊断，不回退为 raw dict 或默认值。validator 若有外部查询或业务副作用，应检查其
职责位置；不要因为恢复模型也会运行 validator，就把这些行为合理化为读取的必要部分。

此指南针对 Python/Pydantic 后端；CLI 的可信响应解码仍不需要 Pydantic 运行时校验。它既不是“一切读取都
不能调用 model_validate”，也不是“一次 model_validate 永远合理”：先确认该处是否真的需要新的模型实例。
