# 收集、整理的 Job 入口与实体修改

状态：[D-595/D-596](../../decisions/D591-D600.md) 已确认收集/整理通过 Job 受理、Block/Relation 原地编辑与删除，
以及下文的具体技术方案；尚未实施。此前直接调用 rumination 门面与排除实体修改的
提案已撤回，不再作为执行依据。

## 显式整理提交 Job

```text
CLI organization ruminate <block>
  → 普通 REST POST /jobs → 持久化 Job 并返回 201
  → capable Peer 的 JobManager claim
  → Organization-owned handler → ruminate_local(block)
```

保留 `inkcre-cli organization ruminate 42` 这个便捷命令，将其转换为以下请求，不另增动作路由：

```http
POST /jobs
Content-Type: application/json

{"type":"core.organization.rumination.explicit.v1","parameters":{"block":42}}
```

新增的 exact Job type 已按 D-596 确认；它的 parameters 使用已有 RuminationRequest 的 block 输入，handler 由
Organization 拥有。现有 `core.organization.rumination.automatic.v1` 只接收 max_seeds 并自行选取候选，不能
拿它冒充处理指定 Block 的任务。两个类型复用已有 rumination 实现，不新增 dispatcher 或独立结果表。
执行资格复用 Organization 的本地 Agent 配置可用性检查；claim 后调用 non-delegating local path，不让 Job
再次走 Peer delegation。默认执行期限沿现有 Organization Job 的 1800 秒，可由 JobCreateForm 覆盖。

CLI 返回实际 Job 记录，后续直接使用 D-587 的 job get/wait/abort。不增加 --peer 或执行 Peer 参数：REST
接入点负责受理，实际执行者由已有 Job claim 机制选择。手动派发与自动候选选择是不同维度；用户仍可通过
job create 手动派发 automatic 类型，也不为 explicit 类型新增 Cron 禁用规则。

Source collect/backfill 继续使用 D-588 的便捷 REST 入口；它们本来就调用 JobManager.create，不执行 Source
业务。所有本轮 CLI 收集/整理入口都受理为相应 Job，而不是长时间保持业务执行 HTTP 请求。

此前拟议的 POST /blocks/{id}/ruminate 不建立。Block 是 Organization 的输入，不决定行为的领域归属。
实际已有的 POST /organization/ruminate 是 Peer inbound，保持原合同供既有消费者使用；不能把它改成提交
Job，也不能因为使用 HTTP 就把它当作 CLI 的普通 REST。D-593/D-594 已确认的管理与检索接口不因此改成 Job。

## 原地编辑与删除

与根级 get 的实体引用形式一致，使用 update/delete；本批每次修改一个明确实体。

| CLI | 普通 REST | 输入 |
| --- | --- | --- |
| update block:42 --input patch.json | PATCH /blocks/42 | 可选 content、resolver、storage |
| update relation:8 --input patch.json | PATCH /relations/8 | 可选 from_block_id、to_block_id、content |
| delete block:42 | DELETE /blocks/42 | 无 body |
| delete relation:8 | DELETE /relations/8 | 无 body |

PATCH 只含提交字段，省略保持；storage:null 明确清空引用，其余字段不能显式设为 null。不接收数据库管理的
id/timestamps。更新返回 HTTP 200 与 D-583 一致的普通实体记录；Relation endpoint 字段只在 REST 边界映射
为 Manager 使用的 from_/to_。删除成功 204，不另造成功对象；目标不存在 404。

Block content 编辑的是存储表示，Storage-backed Block 仍填写 pointer；不把 hydrated content 当作原地写入
接口，也不隐式增加 Storage bytes 写入或 Resolver 调用。删除 Block 的关联 Relation、索引记录等沿已有 FK
行为处理，不递归删除相邻 Block 或 Storage bytes。CLI 不另做一次图遍历和客户端级联。

新增信息继续使用 D-594 的 graph submit / POST /graph：GraphForm 已能表达一个 Block、多个互联 Block，或只
在既有 Block 间增加 Relation。无需为同一新增行为再接出重复入口；已有实体修改则使用上述明确的 PATCH/DELETE。

## 旧 Block PATCH 的输入丢失

app/routes/block.py::edit_block 目前接收 BlockModel，再无条件传递 body.content/resolver/storage。
BlockModel.storage 缺省为 None，但 BlockManager.edit_block 用 Undefined 区分省略与清空，导致请求未提交
storage 也会清空原引用。使用记录作为表单还混入了数据库管理字段。

本轮替换为 partial update form，只将实际提交的字段交给现有 manager，保留 Undefined 语义；输入边界只
验证本次表单，不先重验旧记录。内部调用者无需改为依赖 REST DTO，也不为映射增加第二个持久化模块。

## 依据与预演落点

- app/business/organization/jobs.py 的 rumination handler 使用 AutomaticOrganizationJobParameters；
  app/business/organization/rumination.py 已有可复用的 ruminate_local 与自动选取候选路径。
- app/routes/source.py 的 collect/backfill 已创建 Job；D-588 将响应前的 worker scan 移到受理之后。
- app/business/info_base/block.py 已有 edit_block/delete；relation.py 已有 update/delete。问题是 REST 表单
  与 CLI 操作缺口，不是缺少 InfoBase 的持久化能力。
- app/schemas/info_base/relation.py 的 endpoint FK 使用 ON DELETE CASCADE；索引记录同样级联，Source 的
  block projection 引用为 SET NULL。不存在为了删除 Block 而读取 Resolver/Storage 的需要。

后续预演从 CLI 创建 Job 的请求体一路检查到实际 handler，确认没有直接执行或委托执行的旁路；再检查
PATCH 的实际提交字段、更新返回投影和 DELETE 的数据库效果。验证优先静态机制和脚本黑盒边界，不为字段
逐个创建实现级自动化测试。
