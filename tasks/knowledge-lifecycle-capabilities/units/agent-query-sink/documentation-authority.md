# 文档 authority 修正

D-631 将本项纳入 agent-query-sink；目前为实施计划，尚未修改 durable docs。

## 已确认的长期判断准则

以单条声明而非整篇文件或物理目录判定 authority，先问“这句话在定义谁的合同”。

1. **语义 owner**：谁负责决定该行为及其变化，谁的规范文档拥有它。发现需求的消费者、首次交付的
   unit、代码当前位置均不能自动成为 owner。跨领域依赖方向由架构文档定义，领域具体行为由领域文档定义。
2. **声明范围**：产品意图归 PRD；跨实现必须一致的合同归共享 TDD；本实现的机制归 Spoke TDD；
   操作步骤归运行/开发文档。重要或多次使用不自动意味着应该提升到 Hub。
3. **定义与消费**：消费者可说明自己选用什么、如何组合及自己的约束，但不得替依赖定义可用能力、
   生命周期或失败语义。保留理解消费场景所需的简短摘要与引用，不维护一份可独立修改的依赖规范。
4. **变化传播**：若该能力的合同改变，是否必须在多个消费者文档中重新决定同一事实？若是，则很可能
   有多个 authority。owner 修改合同，消费者仅调整真正受影响的集成事实；不是要求依赖变化永不影响消费者。
5. **证据与状态**：现行合同、观察到的实现、历史方案、示例分别标明。代码用于核实实际行为，不能仅凭
   代码与文档不一致就自动改写产品要求；先判断是实现缺陷还是文档过期，纠正后留下一个现行规范来源。

文档不是简单按“Hub 高于 Spoke”覆盖：Hub 无权因存放位置而拥有本地机制，消费者文档也无权覆盖领域
合同。冲突按声明的语义 owner 与适用范围解决。AGENTS 负责导航及局部重复风险，不复制整份架构合同。

## 已发现的同类问题与预期修正

| 文档/声明 | 问题 | From → To |
| --- | --- | --- |
| business-pipeline-and-authority §6 的通用读取工具合同 | Organization 是消费者，但其章节承载通用能力与工具接合规则 | 跨领域 controller/service 规则放架构层；具体能力归相应领域说明；Organization 只说明组合用途 |
| organization.md 的 Reading and Agent boundary | 混合行为自己的工具选择与通用实体/Resolver 结果合同 | 保留行为选用与写入约束；通用工具 schema/结果规则引用相应 owner |
| organization.md 的 Graph use 首段 | get_connected_components 的通用返回/截断合同与 duplicates 用法混写 | 查询合同归 graph-navigation-retrieval.md；Organization 保留如何解释 provenance occurrence |
| semantic-retrieval.md 的 Rumination And Agent Boundary | 仍规定整理触发/Agent runtime；“无 periodic trigger”与现有 Organization automatic Jobs 表述冲突 | 删除独立定义；保留必要的检索/整理关系与引用，核实触发的现行 owner 合同 |
| Agent subtree AGENTS / TDD 索引 | 无明确导航到工具 controller/service authority | 补精确引用，不在多处复制规范 |

还需按上述准则检查直接相关的 Sink/MCP、Resolver、检索文档及共享声明，记录发现而非预判全都有问题。
单纯提及其它领域或举例并不是越界。历史验收材料可以保留当时背景，不伪装成当前能力规范。

## 准则与具体合同的归属

将 InKCre 文档 authority 准则补入 Hub 现有 `00-meta/submodule-profile.md`，扩展其现有 ownership
部分，适用于同一 repo 内的领域边界及 Hub/Spoke 边界；不放 PRD，也不另建文档 framework。shared-doc
skill 引用该准则，避免复制为第二份规则。具体 Python Agent Tool controller/service 合同仍归 Core
`business-pipeline-and-authority.md`，不能因本次重要而提升为 Hub 实现规范。

这增加本 unit 的 Hub 文档影响面，旧 Handshake 的“无 Hub 修改”已失效。实施时遵循 Hub source 先改、
经授权提交推送后 Spoke 单独 bump ref；禁止编辑挂载目录。当前仅做只读调查及 packet 更新。

## 验证

逐项核对旧位置是否还在独立规定已迁走的合同、新 owner 是否完整、消费者链接是否可达、实际代码是否
符合现行合同。以 Resolver tool controller → ResolverManager → Resolver 实例为一个阅读路径，但同时
核对 retrieve 与图查询，避免只为单例修文档。无需新增文档 gate、全局 claim registry 或自动化测试。
