# Organization Nowledge Vertical — Implementation Evidence

> **状态**：Verify / Acceptance active；2026-09-08 implementation 与静态验证完成，PostgreSQL/真实 provider
> Acceptance 尚未关闭。

## 已实施的拓扑

- Resolver typed method discovery/schema/invocation 已从 MCP Sink projection 移到 `ResolverManager`；MCP adapter 改为消费
  owner contract。
- `app.business.organization` 已从单文件迁移为同名 package；七个 concrete BehaviorResolvers、六个 exact graph
  commands、单一 candidate command、三个读取元工具与七个 automatic Job handlers 已实现。
- rumination 的 explicit local/Peer behavior 已迁移到 `RuminationBehaviorResolver`；route 与既有 acceptance caller 保持
  capability/request contract，media Job 改为直接调用 `organization_media`。
- Graph Navigation 已增加 exact-content bounded connected-component query，返回 seed partition、member/proof graph、
  missing seeds 与 truncation。
- Core bootstrap/profile 已接入七个 Resolver/Job contracts；没有新增数据库 schema、migration、dependency、默认 Agent、
  config 或 schedule。
- 两个 accepted information worlds 已冻结为独立 authored corpus；credentialed black-box runner 从普通 Block/Relation
  input、purpose-built Agent definitions/config 与 automatic Jobs 执行两轮，并只输出 before/after graph 与 Job evidence。
- 本地 durable docs 已从 `OrganizationManager` 单路径更新为当前精确行为拓扑；未修改 `docs/_shared/**`。

## 当前验证证据

- 受影响 source/tests Ruff format + lint：通过；
- `pdm run typecheck`：0 diagnostics；
- import/registration smoke：7 个 behavior Resolver、10 个新 Agent Tools、7 个 automatic Jobs 加既有 media Job 均可发现；
  所有 Tool factories 与 Resolver/Graph query schemas 可实际绑定。该检查发现并修复了 `typing.Collection` 不能直接生成
  Pydantic JSON Schema 的运行时问题，集合参数现在只在 Tool contract 中投影为等价 tuple。
- 独立 corpus loader 验证 2 个 worlds、18 个首轮 artifacts；黑盒 runner 先走正常 lexical maintenance，再运行七个 Jobs，
  第二轮加入普通 `edited` change 后重新维护 retrieval，并输出 graph 与 current/history、source basis、referent path、
  duplicate component later-use readback。
- 新 organization integration/acceptance modules 在无显式数据库/provider 环境时按合同 skip；受影响 test collection 通过；
- task design 与 implementation 保持为两个可审阅提交；implementation delivery 由 D-527 授权。

## 尚待验证与 residual

- 真实 PostgreSQL exact-operation/connected-component journey 尚未运行；本机声明的实际 database target 是
  `wsl.win-ws.localhost` Docker，而不是本地 PostgreSQL。正确执行 `svc dev ensure database` 后，SSH 到
  `172.16.249.14:122` 在 key exchange 前 reset，已有 loopback ports 也拒绝连接。
- credentialed two-world black-box Acceptance 尚未运行；需要显式测试数据库和真实 chat provider 环境，由 Human 审阅
  graph/use quality，不能由静态检查替代。
- 完整 `pdm run check` 仍会先碰到与本 unit 无关的未跟踪 `.agents/skills/python-backend-code` format residual；不得为
  获得绿灯修改或提交它。
- 单独 `pdm run test` 为 `10 passed, 43 skipped, 10 errors`；十个 errors 仍全部来自 Homebrew `libpq` 的 `initdb` 找不到
  同目录 `postgres` binary，与 preflight 的既有环境 residual 一致。
- MCP reflection authority move 当前依赖 type/import/smoke review；仓库没有既有 MCP automated journey 可重跑。
- project-owned database provider reader 已修复为优先读取 SVC schema-v3 `dev.targets` 并兼容旧 v2；真实
  `svc.local.json` 验证由 `provider_matches=false` 变为 `true`。远端 WSL SSH/tunnel 仍不可达，因此数据库 journey 继续
  保留为环境 residual。
- Hub Product/Product-TDD promotion 尚未开始；必须在实现与 Acceptance evidence 足够后使用 Hub-first workflow，不能从
  Spoke 直接修改 shared docs。

## 下一步

1. 完成最终 diff review，修复真实 correctness/maintenance 问题；
2. 运行 foundation、受影响 lint/type、现有可运行 tests 与尽可能完整的 repository gate；
3. 若环境恢复，运行 PostgreSQL journeys 和 `pdm run test:organization-acceptance`；否则保留明确 residual；
4. 根据证据更新本文件与 packet state，再请求 Sir 复核实现/验收结果；不自动 commit。
