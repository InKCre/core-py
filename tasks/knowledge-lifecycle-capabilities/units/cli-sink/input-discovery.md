# 动态合同发现与结构化输入

状态：按 [D-577](../../decisions/D571-D580.md) 获批；建立在 D-575/D-576 的命令边界上，不表示源码已实现。命令目录由
[command-surface](command-surface.md) 维护，本页只说明如何找到操作、知道输入并执行。

## 两个发现层次，而非调用前置流程

根级与子命令 `--help` 在本机可用，说明用途、语法、参数承载方式与可观察效果，不依赖 Core 正在运行。
Source type、Job type、Resolver method 和配置 schema 的实际合同则从所连接 Core 获取，不能用打包时的一份
Extension 清单替代当前运行能力。

目录负责选择，默认提供 exact ID/name 和简短说明；选定操作的 `--schema` 输出其结构化输入的 JSON Schema。
不在根 help 或每次目录查询中展开全部嵌套定义。需要方法选择时，`resolver methods` 可以按 Block 或 exact
Resolver ID 取得方法目录；实际 invoke 仍以 Block 为目标。

```sh
inkcre-cli source types
inkcre-cli source create --type <source-type> --schema
inkcre-cli resolver methods block:42
inkcre-cli resolver invoke block:42 --method get_solved_content --schema
inkcre-cli graph submit --schema
```

`--schema` 只查询合同，不执行对应操作，不要求提供尚待构造的业务输入。对已知类型、方法及合法参数，允许
直接调用，不保存“已经发现过”的会话状态，也不强制先查一次 schema。目录的存在不证明一次执行必然成功；
例如持久化 Source type 与某个 Peer 当前加载的 runtime 是不同事实，不能悄悄互相替代。

## argv 选择操作对象，JSON 保留业务数据结构

简单 ID、type、method、检索模式和等待长度使用普通位置参数或 options。嵌套配置、GraphForm、Agent definition
以及动态方法参数使用 JSON，不把字段递归展开为一组 `--set a.b.c`，也不增加 YAML 或另一种输入 DSL。

已确认的显式承载：

- `--input path.json` 读取文件；`--input -` 读取 stdin；
- `--input-json '{"refresh":true}'` 直接传入较小的 JSON 值，避免为一项参数先生成文件；
- 没有任何必填业务参数时可以省略输入，例如无参数的 Resolver 方法。

两种输入 options 表示同一份数据，不做多文件叠加或递归合并。`--json` 不用于输入，保留给后续设计的结构化
输出选择。是否写文件、从管道取得数据或使用小型 literal 由调用者决定，CLI 不要求 Agent 遵循固定工作过程。

对这批命令，selector 放在 argv，JSON 只填写剩余业务字段；`--schema` 必须准确描述这份 JSON，而不是把
selector 重复要求在 JSON 内。比如 Source create 的 `--type` 已确定类型，输入仍可有 nickname/storage/config；
Job create 的 `--type` 确定 handler，输入有 parameters/timeout_seconds。普通记录里的 type 字段不因此消失。
CLI adapter 为 HTTP 组装请求，不把这一 shell 呈现方式强加给领域模型或数据库。

```sh
inkcre-cli source create --type <source-type> --input source.json
inkcre-cli resolver invoke block:42 --method get_solved_content --input-json '{"refresh":true}'
inkcre-cli graph submit --input graph.json
inkcre-cli agent create --input agent.json
```

`source.json` 保留 `config` 的嵌套层级，不把 config 字段提升为 Source 根字段。`graph.json` 就是 GraphForm，
不再包一层 `graph`；Resolver input 就是选定方法的 arguments，不再嵌套 `method` 或 `arguments`。
表单不包含数据库管理的 timestamps/ID；GraphForm 的负数本地 ID 是已定义的 producer 引用例外，不被删除。

## schema 对应提交位置，不只给一个类型片段

| 操作 | 输入 schema 如何取得具体形状 |
| --- | --- |
| `update block:…` / `update relation:…` | D-596 确认的相应 partial update form；selector 不出现在 JSON，省略字段保持，不能包含数据库管理字段 |
| `source create --type …` | 创建字段与该 Source type 的 config schema，后者保持位于 `config` |
| `source update <id>`、`collect <id>`、`backfill <id>` | 从 Source 的实际 type 选择该操作的合同，不混用保存配置与单次收集参数 |
| `resolver invoke <block> --method …` | 从 Block 的 Resolver 取得该普通方法的参数合同 |
| `job create --type …` | 该 Job type 的 parameters schema 保持位于 `parameters` |
| `cron create --job-type …` | Cron 配置字段加对应 Job template；参数 schema 保持位于 `job_parameters` |
| `agent create` / `update <id>` | Agent definition 表单；model 与 Tool IDs 的选择提供配套发现，不枚举在每个响应中 |
| `config update <key>` | 由现有记录的 schema 取得 owner 的配置输入合同 |

新建或替换 deployment config 时，schema ID 需要显式选择：建议通过 `config schemas` 发现，并用 `--schema-id`
传入。它与查询合同的 `--schema` 开关不同，不把 schema ID 改称 type。输入是配置 value 本身，不再次包装
`value`。准确 replace/update 子命令与部分更新语义仍需后续逐组复核；不能假定所有 behavior config 都是
`{"agent": int}`，媒体解释已经有按 modality 选择 Agent 的真实例外。

没有足够 selector 时，可以取得共同表单；其中未特化部分必须明确仍是通用形状，不能把开放的 object 伪装成
已经完整说明 Extension 参数的合同。schema 查询应保留 defaults、required、enum、字段说明及可解析的 `$ref`。
如何组合已有 owner 合同属于 Technical 工作，优先复用 Pydantic/已有 schema，不自制 JSON Schema 解析器。

## 校验与作用边界

CLI 继续使用 Pydantic，表达自身输入和连接配置，不手写一套同类解析/验证机制。Core 用实际
owner 的模型校验动态业务输入；CLI 不复制 Extension 的 Source/Resolver 配置模型，也不因收到 JSON Schema
就预设需要将它反向编译成 Pydantic model。具体合同复用方式留给 Technical。

请求路径、payload 与内部模型的必要映射不改变模型 owner；错误保留调用者填写的字段位置，
例如 `config.protocol.parameters.host`，不把它改写成一个看似顶层的 `host`。不自动猜另一个 type/method，
也不在写入失败后自行修补并重发工作。

这里的 `--schema` 指输入合同，不由此推导一套动态结果的二次语义校验或完整协议生成框架。D-598 进一步确认
CLI 信任 Core REST 返回，响应侧使用解码、必要转换与静态类型描述，不增加 Pydantic/JSON Schema 再校验。
Pydantic 仍用于 CLI 自有输入。发现不执行 Resolver 内容读取，
因此不会仅为查看方法合同触发下载、AI 或 graph materialization；实际 invoke 的效果仍由该方法定义。

## 现有证据与待落地缺口

`app/schemas/source/main.py` / `SourceManager.sync_source_types` 已有配置、collect、backfill schemas；
`app/schemas/job.py` 已有 `parameters_schema`；`ResolverManager.get_method_contracts` 和 `invoke_method`
共用方法的 Pydantic input model；`ConfigContract.json_schema` 可投影 owner 的模型；GraphForm 已是 producer form。
这些不等于完整普通 REST 已存在。需要在 Technical 补齐对外发现及必要的操作表单投影，不新增独立业务 registry，
也不要求 Extension 为 CLI 注册另一份 schema。

本轮用 ponytail 检查的是这个技术复用边界。文件/stdin、JSON 和模型 schema 已能承载需求；新增内容限于 CLI
呈现和现有 domain 的 HTTP 接口，不在 Product 阶段选择 CLI 库或设计泛用动态命令生成框架。
