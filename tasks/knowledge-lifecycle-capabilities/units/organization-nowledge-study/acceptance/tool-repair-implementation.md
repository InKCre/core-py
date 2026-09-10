# 工具修复实施记录

本记录承接 D-529–D-540；不是新的产品设计，也不表示整组语义验收通过。

## 已实施，尚待 preview 对照

- Resolver 显式过滤未命中不再返回全目录；公共方法直接投影到调用 schema，额外方法继续开放发现。
- 方法名错误返回可用名称与 describe 指引；方法参数错误返回字段错误与对应 schema。逐调用校验由实际
  Resolver owner 完成，保留同批成功项，而非让一个错误参数拒绝整个批次。
- 图查询改成邻域、路径、连通分量三个直接工具；get_entity 读取持久实体，空 ID 仅随机取得 Block。
- retrieve 返回实体引用和已有命中信息，不复制完整实体；两种检索的结果与错误仍独立。
- 精确写入工具采用已定关系定义及 *_block_id 名称，返回标识显式命名；候选标记不再要求自动执行能力。
- 草拟图仍不持久化，提交图才持久化。未改数据库、Agent runtime、模型、预算、候选选择或识别 SOP。

## 实际 schema 探测

直接向 qwen3.6-plus 提交实际绑定 schema，不读取或修改图。顶层只有 oneOf 的 Resolver 请求连续两次将
calls 输出为 JSON 字符串；仅增加 type=object 未解决。补充同源生成的顶层 properties 后，两次探测均输出
数组。邻域补充顶层形状后 entity_id 也输出为整数。未加入字符串解析或额外提示例子。

分支合同仍负责 describe/invoke 或 Block/Relation 的条件约束；顶层形状只是较宽的字段投影。
Resolver 参数定义来自 owner 反射：工具 schema 与实际逐项验证共享合同，不让通用调用分支绕过实际 owner。
最终探测响应见 [tool-schema-spike.json](tool-schema-spike.json)；探测不是完整 Agent 行为验收。

## 本地验证

- 类型检查通过；完整 pytest：15 passed / 53 skipped（未提供可用 PostgreSQL 的套件跳过）。
- 曾新增一项缺陷回归并执行；Sir 随后明确禁止新增任何回归测试或聚焦测试，该文件已撤掉。
  上述 15 passed 是撤掉前的历史结果，不作为当前测试数量。后续不新增此类测试，已有测试只同步必要接口变化。
- foundation 通过。完整 check 的格式阶段碰到无关未跟踪技能脚本；不修改该脚本，额外排除该目录运行
  相同格式/lint 检查：均通过，类型检查也通过。未改动无关技能目录。

## 运行环境

- WSL 的 SVC ensure 失败：SSH 172.16.249.14:122 在握手时被重置；未删除或重建其数据库卷。
- preview 基线首次读取返回 PGRST002 / HTTP 503，尚未创建任何测试实体。已重跑原 head 的数据库配置
  workflow 和部署均成功；日志配置独立重跑后成功，已读到实际 Agent 事件。
- 同模型、12 次预算、原 system prompt 的远端对照脚本为 preview-tool-repair.py；完整世界基线正在执行。
- 临时日志配置 helper 改为 PATCH 后独立 GET 确认，避免将更新响应视作最终读回；本分支每次 push 均在部署后
  恢复日志。helper/workflow 仍须在合并前移除。

## 验证约束更新

Sir 明确要求：不得新增任何回归测试或聚焦测试。静态检查与端到端黑盒验收是本轮验证路径；
已做 schema 探测只保留历史 JSON 证据，探测脚本也已撤掉，不保留或扩展为聚焦测试。
