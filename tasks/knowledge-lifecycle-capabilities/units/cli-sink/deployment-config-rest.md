# Deployment config 的发现与管理 REST

状态：按 [D-590](../../decisions/D581-D590.md) 确认，尚未实施。承接 D-577 的输入发现与 D-589 的分层讨论纠偏。只列接口增量与直接实现缺口，
既有配置消费行为留给内部预演，不重新作为业务决策。

## 路径与呈现

| REST | CLI | 合同 |
| --- | --- | --- |
| GET /configs | config list | 已持久配置记录，不混入未配置的默认值或虚拟记录 |
| GET /configs/{key} | config get | key、schema、value、created_at、updated_at |
| PUT /configs/{key} | config replace | 创建或完整替换；body 为 {schema, value} |
| PATCH /configs/{key} | config update | body 为 value 的顶层部分字段，不再包 value；不改 schema |
| DELETE /configs/{key} | config delete | 删除配置记录；204，无记录为 404 |
| GET /config-schemas | config schemas | 本机注册 schema 的 id、keys 与 description，不附全部 JSON Schema |
| GET /config-schemas/{id} | config schemas 的精确选择 / --schema 查询 | 同一描述加 input_schema |

GET 和 PATCH 返回 200；PUT 创建返回 201，替换返回 200，均返回实际配置记录。PUT 的创建/替换由持久化操作
结果判断，不靠 CLI 预先 GET 或单独读存在性推断。状态码遵循
[RFC 9110 §9.3.4](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.4)。列表分页随管理列表共同合同收敛。

config schemas 是当前 Peer 的代码合同发现；configs 是 deployment 的持久数据。schema 未出现在前者，不影响
读取后者，不伪造 deployment-wide schema catalog。本轮不增加持久 schema 表或跨 Peer schema 汇聚。

## 首次配置的发现

现有 register_schema 只登记 schema ID 与模型；各 owner 已另有 CONFIG_KEY 常量。建议在同一注册处增加可选
keys 元数据，让 CLI 知道哪些业务 key 使用该 schema：

```python
DeploymentConfigManager.register_schema(
  RUMINATION_CONFIG_SCHEMA,
  RuminationConfig,
  keys=(RUMINATION_CONFIG_KEY,),
)
```

keys 默认空 tuple，是 owner 声明的已知用途，不是限制写入 key 的白名单，也不要求一个 schema 只能对应一个
key。注册元数据与 ConfigContract 放在同一 registry entry，不再增加 key registry 或独立 manager。
description 取模型已有说明；input_schema 仍由 ConfigContract.json_schema 提供，不维护第二套 schema。

所有本轮触及的现有 deployment config owner 在自己的注册处提供现有 key 常量，包括 organization、retrieval、
Resolver、Source、Cron、extension registry 配置；不在路由或 CLI 集中复制这些对应关系，不从 ID 字符串推导 key。
这是普通配置发现信息，不让 owner 声明 CLI/Agent 专属能力；也不变成配置实例的自动创建或默认值持久化。

列表中的一项示例：

```json
{
  "id": "core.organization.rumination.config.v1",
  "keys": ["core.organization.rumination"],
  "description": "Deployment selection of one reusable Agent definition."
}
```

CLI replace 继续显式传 --schema-id；输入只包含 value。已知 key 与 schema 时可直接写，不强制先发现。
不在 CLI 从 keys 反向自动选择 schema，因为同一 key 可能有不同 schema 版本。

## 管理读取和修复

管理 GET / list 返回数据库实际保存的 schema 与 value，不先按业务模型校验或注入默认值；因此未知 schema、
旧版或错误配置仍可查看。响应 DTO 描述记录形状，不额外验证其业务 schema。DeploymentConfigManager 的
typed get 保留类型化消费接口，但不把它现有的重复 schema 校验当作保留条件；读路径只承担必要的表示转换。
具体调用与 Pydantic 构造方式在实现预演中核对，不以手写通用反序列化器替代一次错误的过度校验设计。

PUT 仍按明确 schema 校验、规范化完整 value。PATCH 在现有行锁内将原 value 与提交字段浅合并，再校验完整
候选结果，而不是要求旧 value 先通过验证。这样一次合法 PATCH 可以修复原有错误；未修复的问题仍由 Pydantic
正常指出，不增加旁路写入或专用 repair endpoint。

PATCH 的对象/数组字段完整替换，null 为普通提交值，是否有效由 schema 决定，不表示删除字段。body 使用
application/json，这是本接口明确的浅合并合同，不冒称 JSON Merge Patch。PATCH 本身不规定唯一 patch 格式，
见 [RFC 5789 §2](https://www.rfc-editor.org/rfc/rfc5789.html#section-2)。

PUT/PATCH 仍需当前 Peer 的 schema 实现；未知 schema 时无法声称已验证。GET/DELETE 不需要该实现。
删除只删除记录，不将其表述为统一的 reset-to-default：缺失配置的含义由既有 owner 决定。

CLI 示例：

```sh
inkcre-cli config replace core.organization.rumination \
  --schema-id core.organization.rumination.config.v1 --input-json '{"agent":42}'
inkcre-cli config update core.organization.rumination --input-json '{"agent":43}'
```

第一条由 CLI 组成 PUT body {schema, value}；第二条直接用输入作为 PATCH body。输出保持配置记录形状，
不增加配置有效性标签或预制下一步操作。

## 实现证据与验证范围

app/routes/deployment_config.py 已有 GET/PUT/PATCH；app/business/deployment_config.py 已有 schema registry、
read/get 区分、upsert 与行锁 PATCH。目前 read 经 _view 调用 _validate_record，会使非法/未知配置的 GET 失败；
PATCH 也先验证旧值。app/configuration.py 的 ConfigContract 是无持久化/registry 的模型工具，不把 keys 放入它。
源码调用检索显示业务使用 typed get，管理 read 当前由配置 route 调用；落地时再次检查所有调用点。

需要验证首次配置发现、完整替换、浅 PATCH、读取与修复非法配置、未知 schema 记录的读取/删除。沿用单元手工/
脚本黑盒验收，不新增自动化测试。注册元数据、管理 read、typed get 的重复验证与 PATCH 变化是本轮真实 Core 影响，需要纳入实现计划；
不会因写进本页而获得源码实施授权。现有合法请求的 PUT/PATCH body 保留，GET 的实际值语义变更须写入 REST 文档。
