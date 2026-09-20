# 实现与验收记录

2026-09-20，branch `feat/agent-query-sink`。本页只记录本 unit 的易变交付证据；稳定合同归
`docs/30-unit-tdd/` 与代码。

## 已实现

- 通用读取 Tool controller 已从 Organization 迁回 info-base、Resolver 与 Graph Navigation；exact IDs 保持不变，
  composition root 显式注册 Core tools。Agent registry 只拥有绑定与执行机制。
- `core.agent-query.v1`、`core.sink.agent-query.v1` 与 `submit_query_result` 已实现；实例 endpoint 在 enable 时
  挂载、disable 时按 route identity 撤下。Job state 保存回答、引用和普通结束原因。
- Sink lifecycle 对同一实例串行化；无 active resource 的 SinkBase hooks 默认为 no-op。
- REST 增加单个 Sink type 读取，CLI 增加 Sink 管理与 `query`。
- durable docs 已按语义 owner 纠正；长期 owner 判断准则先写入 Hub PR，再单独更新 shared ref。

## 已通过的本地证据

- `pdm run check:foundation`；`pdm run check`（14 passed，60 skipped）。
- `pdm run -p cli check`；`pdm build -p cli` 生成 sdist 与 wheel，产物未入 Git。
- SVC development runtime `readyz`、migration、roles 与 catalog 就绪，source fingerprint 对应当前实现。
- 冷启动 Agent Tool discovery 包含既有 exact IDs 和 `submit_query_result`；Sink/Job catalog 分别包含
  `core.agent-query.v1` / `core.sink.agent-query.v1`。
- 通过构建 wheel 的 CLI 创建并启用临时 Sink，发现动态 query schema，创建 Job，观察并 abort；disable 后 exact
  route 返回 404，随后删除实例。临时 Agent ID 不存在，因此这条旅程只证明 REST/CLI/Job/lifecycle，不声称回答质量。

## Preview 与真实模型

Core draft PR #111 的 Preview 在实现 SHA `b384709` 上通过 delivery checks，Core `/readyz` 报告 migration、catalog、
roles 与 privileges 就绪。验收使用隔离 virtualenv 安装本次构建的 CLI wheel，只通过 REST 连接 Preview。临时
AI provider/model 使用 `core.alibaba-model-studio.v1` 与 `qwen3.5-omni-flash`；Agent 1、Sink 1、Block 1–5 和
Relations 1–2 均为本轮 Preview 数据。

- **A1/A2**：Job 2 比较 Block 2 的 Graph Navigation 与 Block 3 的 Lexical Retrieval，交付有依据的互补边界和
  两个真实引用；CLI bounded wait 先返回 running，随后取得 finished 结果，并可用 get/resolver 重新打开依据。
  Job 4 从 SQLite 官方 Architecture Block 1 准确说明 Page Cache 与 B-tree 分工。Job 12 对材料不能证明的
  “所有场景最优”结论明确回答证据不足并引用 Block 2/3。
- **A3**：PostgreSQL binary-backed NASA 视频 Block 4 通过 `subtitle` Relation 连接作者 VTT Block 5；Job 8 从
  媒体实体出发找到并读取字幕，准确说明软件仿真受其覆盖范围限制，实物 spacecraft/flat-sat 才能继续验证。
- **A4**：Job 13 在 running 时收到 abort request 并结束为 aborted；Job 14 以一秒 wall-clock budget 结束为
  timed_out。第二个 Sink 2 同时启用后，两条动态 schema 均可发现；撤下 Sink 1 时仅其 route 消失，Sink 2
  继续工作；重新启用 Sink 1 后 route 恢复，旧 Jobs 仍可分页查询。通用 Job API 创建的 Job 15 也被同一
  handler 受理并按一秒预算结束。
- **Organization 回归**：临时 Agent 2 驱动 explicit rumination Job 16。真实 trace 先调用迁移后的
  `get_entities` 读取 focal Block 1，再调用既有 draft schema/draft/submit 链路，写出 Block 6 与 Relation 3；
  Job finished。临时 Organization config 与 Agent 随后删除。
- **D-627**：本地 preflight 已确定最后一调用提交、提交后异常与取消的状态映射；Preview 又真实覆盖
  completed/max-model-calls 未提交、max-model-calls 已提交、abort 与 timeout。一次 provider 429 被记录为外部
  quota 波动，不改写为产品状态。

真实模型也证明 `tool_choice=auto` 可能直接结束而不提交；推荐模板因此改为 `required`。当前 Alibaba adapter 在
该模式下可能持续再次提交直到预算结束，D-622 的 last-successful-result 合同可保持正确结果，但存在额外模型调用
成本；本 unit 不为单一 provider 添加 runtime 特例。

## 最终镜像复验

修正提交 `2dbbfce` 的 repository、portable database、CLI 与 Preview deploy checks 全部通过；最终代码镜像
`/readyz`、migration `d41cc84db0c5`、catalog、roles、privileges 与动态 query schema 均就绪。Job 17 未在预算内
提交结果，按合同明确 failed；缩小已知材料后的 Job 18 读取 Block 6、交付准确回答与真实引用并 finished，证明
新镜像的完整受理、执行和结果链路。当前剩余提交只更新本 evidence，不改变已验收代码路径。

## 尚待

- Hub PR #29、Core PR #111 的合并、版本准备、production 与 PyPI 复验均需要后续明确授权；draft PR 不能写成
  unit 已关闭。
