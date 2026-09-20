# Spoke Unit TDD Promotion Applied

core-py local Unit TDD promotion 已应用，只记录本仓内部 implementation architecture，例如：

- memo extension package、route/service/resolver/storage/transaction boundaries；
- graph mutation 与 solved result 的 internal contracts；
- auth/config 的 local wiring；
- Memos extension 的 0.29.1 backend adapter 对 missing `updateMask` 的 raw-JSON key-presence
  inference 与 negative
  cases；
- tests、migrations 与 failure/residue handling 的实现真相。

具体 ownership 已投影到 `docs/30-unit-tdd/memos-extension.md` 与更新后的
`business-pipeline-and-authority.md`；临时 implementation observation 未被提升为共享合同。

## Agent Query：待实施时修正的 Agent Tool 分层说明

D-629/D-630，尚未应用。Owner 是既有 `docs/30-unit-tdd/business-pipeline-and-authority.md`，不是新文档
或 Hub 产品声明。该文档已要求 Tool handler 调用领域 owner，但 §6 将六个通用读取工具置于
Organization 章节，且未明确工具 controller / 领域 service 两个维度。

实施时在 §5 明确 `Agent runtime → 领域所属 Tool controller → 领域 service`，说明输入校验、结果
投影与业务效果的边界；共享读取能力从 Organization 消费语境移到其实际 owner 的说明，§6 只引用。
补一个 resolver controller 调用 ResolverManager、再调用 Resolver 实例的最小例子，不复制 schema 清单。
`app/business/agent/AGENTS.md` 添加指向该 authority 的导航，强调修改工具归属时先读；必要时更新
Unit TDD 索引的检索描述，不另建一套规则。验证是检查实际注册 handler → service 的调用链与文档一致，
并核对领域 service 不为 Agent 输出格式而丢失自身返回能力。既有测试策略不变。
