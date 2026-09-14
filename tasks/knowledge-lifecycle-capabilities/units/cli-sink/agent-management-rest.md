# Agent definition 管理与引用发现

状态：按 [D-589](../../decisions/D581-D590.md) 确认，尚未实施。范围来自 D-575；本页不新增 Agent 对话、Thread 管理、AI Provider
写入或本机执行能力。Deployment config 的配置发现与管理随后单独收敛。

## 接口与 owner

| REST | CLI 对应意图 | 返回 |
| --- | --- | --- |
| GET /agents | agent list | 持久 Agent definitions；列表沿 D-597 的共同合同 |
| GET /agents/{id} | agent get | 一条完整 definition |
| POST /agents | agent create | HTTP 201 与创建的 definition |
| PATCH /agents/{id} | agent update | HTTP 200 与更新后的 definition |
| DELETE /agents/{id} | agent delete | HTTP 204；不存在为 404 |
| GET /ai/models | ai models | deployment 的 AIModel 记录，不仅列出本机可执行模型 |
| GET /ai/models/{id} | ai models 的精确选择 | 指定 AIModel 记录 |
| GET /agent-tools | agent tools | 当前接入 Peer 已注册 Tool 的 id 与 description |
| GET /agent-tools/{id} | agent tools 的精确选择 / schema 查询 | id、description、input_schema |

AgentManager 补 definition 管理与 Tool 发现；AI 模型读取由 AIManager 提供。REST 只解析输入、调用 owner
并映射响应。CLI 的模型发现归 ai 命令组，Tool 发现归 agent 命令组；不因 Agent 引用模型而混合两个领域。
新增 ai 命令组本轮只承接已批准的模型发现，不据此扩展为 Provider / Model 写入管理。
不创建新的 CRUD service、数据库表、Tool catalog 或额外 AgentToolRegistry。

Tool 列表只读取注册信息；单项 schema 使用现有 registration.bind 的动态 input model factory，不执行 handler。
局部 Tool 清单不是全 deployment 清单，未列出某 Tool 不证明其它 Peer 没有该实现。具体 CLI 单项选择语法
沿用命令解析阶段统一决定；已知 ID 可直接用于 definition，不强制先发现。

## 表单与编辑

创建表单使用独立 Pydantic AgentForm，不直接把 SQLModel table 当写入表单。可写字段沿用现有 definition：

```json
{
  "name": "我的整理 Agent",
  "system_prompt": "……",
  "model": 7,
  "tools": [],
  "tool_choice": null,
  "max_model_calls_per_turn": 12
}
```

tools 默认空数组，tool_choice 默认 null；其余字段必填。例中的 7 和 12 只是示例，不是 preset 或新增默认值。
id、created_at、updated_at 由数据库管理；读取与写入成功响应保留这些实际记录字段，没有成功 envelope。
精确 Tool IDs 继续使用现有集合语义、规范化与非空/不重复约束。nullable ToolChoice 复用现有 union，不发明
CLI 自己的 tool-choice DSL。

PATCH 使用与 Source / Cron 一致的顶层替换：省略保持，tools 整组替换，tool_choice 可显式 null。完整候选值
经表单校验后只更新可写字段；不把输入缺省值覆盖到未提交字段。持久化方法拥有短事务，沿用已有数据库时间戳。

保存 definition 不是执行资格检查。不调用 can_execute、绑定全部 Tool、探测 Provider 或启动一个试运行 Thread。
model 的存在性沿用数据库 FK；本机缺少 Tool / dialect、模型暂时禁用，不阻止保存一个给其它执行端使用或
尚在配置中的 definition。模型能力、Tool choice 和实际输入能否一起执行，仍由现有 Agent / AI 执行边界判断。
API 不因此宣称任何保存成功的 definition 都一定可运行，也不另造一份跨 Peer 执行认证机制。

模型发现返回 id、provider、native_model_id、name、capabilities、enabled 与时间戳。capabilities 保留既有
chat/embedding、modalities 与 features；不折叠成一枚由当前 Peer 推断的 available 标记，不附带 Provider config。

## 实现预演使用的既有约束

Thread 快照、行为配置引用与删除后缺失引用的处理沿用现有 Agent / Organization 合同，依据见下节。
这些不是本轮新增的 REST 决策；预演需确认接口没有暗中引入执行、取消、配置改绑等副作用，不反复要求 Sir
确认已有业务规则。AgentForm 不含 behavior/config_key；行为配置仍通过 config 管理。

## 已核验证据与预演落点

- app/schemas/agent.py：agents 已持久 name、system_prompt、model、tools、nullable tool_choice 和正的
  max_model_calls_per_turn；model FK 指向 ai_models，tools 为 text array，不引用持久 Tool table。
- app/business/agent/main.py：AgentManager 已拥有 Tool 注册与 bind；run 加载 definition 后把 prompt 变成
  SystemMessage，并把参数和 bound tools 放入 Thread。当前没有 definition CRUD 或公开 Tool 发现方法。
- app/schemas/ai/main.py、capability.py、chat.py：AIModel、capabilities 与 ToolChoice 已有 canonical 合同。
- app/business/organization/_shared.py：行为配置使用时加载 Agent；缺失引用不由配置模块自动修复。

实现前继续核对 table validator 与新 form 的复用位置，避免复制规范化逻辑；动态 Tool schema factory 的失败
不能阻断基础 Tool 列表或 Agent definition 读取。列表与错误原则沿 D-597 的[共同合同](list-error-contract.md)，
长输出覆盖、动态 schema 展示与实际映射仍需预演。以上仅是设计与源码核验，不是实现或黑盒验收结果。
