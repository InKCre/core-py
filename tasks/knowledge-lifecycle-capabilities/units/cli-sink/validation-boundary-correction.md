# 同类校验边界修正

状态：D-591 已纳入单元范围；本页为初步源码核验与预演清单，尚未实施。准则来自
[校验边界指南](../../common-patterns/validation-boundaries.md)，不在这里重复规则。

## 已定位调用链

| 路径 | 当前事实 | 修正方向 / 待核验 |
| --- | --- | --- |
| DeploymentConfigManager get/read/patch | 数据库 value 经 _validate_record 重验；PATCH 先验旧值 | 按 D-590 分离写入校验与读取表示转换 |
| SourceBase.get_config | 读取 source.config 后 model_validate；SourceManager.create 已按类型校验写入 | 一并处理 Source 管理与 extension 内直接加载相同配置的路径 |
| Storage.__init__ | storage_record.config 在构造实例时重验 | 定位现有配置写入边界，读取不再附带重复业务检查 |
| SinkManager → SinkBase | create/update 校验；实例加载、live update 再校验同一值 | 传递已建立的 typed 值；从数据库恢复时只转换表示 |
| AIManager._load_target | 读取 Provider config 后调用 dialect 模型校验 | 保留 adapter 所需类型转换；不混入当下启用/能力判断 |
| PeerManager / PeerModel.capability_snapshot | 配置读取、发布前及 capability snapshot 读取均可重验已持久字段 | 将写入/发布规范化与读取转换分开；不改变 delegation 的使用条件 |
| JobManager.create → _prepare | 创建规范化参数，准备执行再次 validate_parameters；非法参数被跳过 | 创建仍是输入边界；执行取得 typed 参数，不将重复校验失败变为永久 pending |
| client-web JobManager.create → prepare | parameters.parse 后持久化，prepare 又 safeParse 同一参数 | 与本轮 worker 停止能力一起配套修正；不在两端保留相反原则 |
| Agent / AI SQL TypeDecorator | process_result_value 调用与写入相同的 canonicalization helper | tuple、union branch、嵌套模型转换与唯一性/约束校验分开核对 |
| Extension runtime config/state | bind/get_config/get_state 和 mutation 前后均有 model_validate | 在实际 runtime 源码 owner 修正，不只覆盖 Core facade |

表中是已定位的机制，不代表每一项的写入路径、表示转换和全部消费者已经完成预演。first-party Extensions 的
相同 Source config/state 读取也在范围内：已定位 mail、telegram、github 等调用点，不以 extension 目录排除。
Resolver 对外部 Storage bytes 的解码另辨输入来源，不能由“Block 在数据库”推导其指针指向的 bytes 也已验证。

## 不应混删的路径

- Agent runtime 验证模型生成的 Tool arguments、Resolver method 验证外部调用参数，仍是实际输入边界。
- Provider / Registry / Peer HTTP 响应的解码来自外部协议，不属于本次数据库记录再校验问题。
- SourceCollectParameters.config 当前只是 dict；source/job.py 调用 validate_collect_config 是首次进入具体
  Source schema，不是已经验过同一 schema。应检查如何在入库时建立该合同，不能直接删掉唯一的具体校验。
- BlockForm → BlockModel 的 producer 映射、Typed union 解码和日期/SecretStr 转换不能仅凭 validate/parse 名称
  判定多余。目标是正确的边界，不是把这些函数出现次数降到零。

## 转换实验与代价控制

后续 [Runtime 预演](preflight-runtime.md) 已区分直接记录读取、typed 值传递、复杂模型恢复三类路径；
仅最后一类保留一次 Pydantic 原生构造及附带约束，避免自制通用 decoder。此取舍已于 2026-09-14 按
D-602 获 Sir 确认；实际调用链仍待实施验证。

本机 Pydantic 2.13.4 的一次内存实验确认：验证后 model_dump 得到的嵌套 JSON 再 model_validate，会再次调用
field validator；浅层 model_construct 则使 nested field 保持 dict，不能保证既有嵌套属性访问继续工作。
实验没有网络/数据库、源码文件或自动化测试产物；只证明这两个库行为，不证明具体领域已修复。

MailSourceConfig.parameters 是 IMAPParameters，AI Provider config 的 api_key 是 SecretStr；它们是具体转换
压力。优先保留已得到的 typed 对象并减少重复转换，其他路径核验 Pydantic/既有库的原生能力。不为“零校验调用”
自建通用递归解码器或用 cast 假装完成了转换。按 D-602 接受复杂类型恢复的一次原生构造，不再为同一库取舍重复请求复核。

参考：[Pydantic model_construct](https://docs.pydantic.dev/latest/concepts/models/#creating-models-without-validation)；
本机也读取了对应 BaseModel 方法实现，证据版本以 2.13.4 为准。

## Owner 与交付压力

Core 主要落点：app/configuration.py、各 owning manager/base、app/schemas 中的 persistence codec，以及这些
入口在 first-party Extensions 的调用。client-web 已在本单元因 Job 停止协议在范围内，配套纳入相同 worker /
持久对象读取问题，实际转换须保留 Zod-class 的实例行为与日期转换。

Core 当前依赖 inkcre-extension-runtime-core-py 0.1.2，下载自 ext-reg 的 runtime-core-py-v0.1.2 Release，
该 Release 的 target_commitish 为 be9629a6c24625f4e43b82fc39b9c39ab3735b1e。已读取安装包 base.py 的对应路径。
2026-09-13 继续核验发现，本地 ../ext-reg HEAD 60879eb 是旧 checkout；GitHub main 与 origin/main 均为
3fc45236afcaeaa500f6cef907812a1ac8c2040b，源码位于
`runtimes/core-py/src/inkcre_extension_runtime_core_py/base.py`，实际重复链路已读。源码 owner 已定位；
先前的缺失不能再作为未决 blocker。本地 main ahead 1/behind 17，后续使用独立 feature 工作位置，
保留原 checkout 的提交和未跟踪文件。修改需经过 runtime 发布及 Core dependency pin；不可编辑 .venv
或在 facade 打替代补丁。嵌套表示转换仍待预演，见 [preflight](preflight.md)。不向关闭的 session 发消息。

## 完成条件

按每条确认的调用链记录输入边界、读回表示与实际消费者，完成共同机制及必要调用方修正；不能只修第一个
显眼 GET。静态检查与原定黑盒 journey 覆盖真实使用，必要时增加一次性脚本压力，不自动扩成新测试套件。
该工作进入 CLI 的 implementation plan / impact handshake，不另建 task 或独立 implementable unit。
