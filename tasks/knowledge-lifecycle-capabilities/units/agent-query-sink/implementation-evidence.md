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

## 尚待

- 推送 Core draft PR 后，以 preview 与真实模型完成 A1–A4；记录实际 Agent/Sink/Job/entity IDs 与材料依据。
- Hub PR 合并与本 unit 最终发布均不在当前授权范围；不能把 draft PR 或本地检查写成 unit 已关闭。
