# Agent Tool 合同修复方案

通用依据统一见 [Agent Tool common patterns](../../common-patterns/agent-tools.md)。本文件只负责本 unit 的具体修复
与批准状态，不把尚待确认的接口职责提升为通用规则。

状态：2026-09-10 D-540 关闭同模式工具的逐项确认，进入技术收口与实施；本文件不表示以下改动已经实施。
实施状态统一见 [工具修复实施记录](acceptance/tool-repair-implementation.md)，以下保留方案依据。
逐工具评审：resolver 的用途、过滤规则、独立批次与参数纠错已按 D-529 接受；响应取舍已按 D-530 接受。
后续同模式调整按 D-539/D-540 自主完成；分支 schema 先验证兼容性，不因确认而宣称技术方案已验证。

## 图查询：改为直接工具（D-531）

撤回 graph_retrieval describe/invoke 方案。D-532 进一步合并两类邻域、移除独立随机 Agent 工具后，直接提供
get_entity_neighborhood、find_path、get_connected_components 三项图查询。直接展示参数 schema，
去掉方法名/通用 arguments/发现过滤器这些额外交互。各工具仍薄调用 Graph Navigation owner，保留原始查询结果。
仅为元工具存在的 query discovery/dispatch helper 在核对无其它调用者后移除，不扩展新图能力。
迁移本 unit 的 Agent Tool sets；已有绑定与调用点需一起核对，不影响独立 MCP 工具的外部合同。

参数含义优先放字段 description，自明字段不补文字；机械约束使用类型/enum/bounds。工具说明仅概括用途。
分页、路径受限/未找到、missing seeds/truncated 影响使用语义，保留；具体工具参数与返回合同继续按既有查询核对。

邻域输入明确 entity_type（Block/Relation）和 ID，两种 ID 可能重合，不能只靠数字猜类型。Block 分支保留已有方向、
内容过滤与分页；Relation 分支保持该 relation + 两端 Blocks 的闭合结果，不默默扩展语义，也不对不适用的参数
静默忽略。具体 schema 在合并接口中直接表达分支。

Resolver 公共方法直接进入 invoke schema（公共读取包括 get_label/get_text/get_solved_content/get_raw_content/
get_relations/get_transfer_url），保留具体 Resolver 的额外方法发现路径，不把任意未知方法视为通用方法。
公开参数以 owner 合同为准，避免通用分支与扩展分支同时匹配导致绕过通用参数校验。

基础读取职责已由 D-534 确认并命名为 get_entity：取得普通 Block/Relation 的持久字段与实际 ID，content 保持
原始持久值，不 hydrate/solve；内容解释仍由 Resolver 承担。MCP 当前 inkcre_open_entities 是职责参考，内部 Agent
复用 InfoBase owner，不依赖 MCP 或继承其传输包装。
先前空 ID 随机取得 Block 的意图延续；明确 ID 未找到仍返回未找到，不回退随机。具体引用形状、批量与 Relation
空 ID 语义继续核对，不根据 get_entity 名称自动新增随机 Relation 查询。
这是当前 unit 的验收后修复轮次，整组功能继续共同交付。前置开发追踪已在 PR #100 preview 验证可读。

## Retrieve：候选与按需读取（D-535 accepted）

保留 query、mode（lexical/semantic/hybrid）与 limit，默认模式暂不变。工具说明只概括“检索信息”；字段说明承担
必要语义：query 的检索词/语义描述，mode 的方式，limit 是每种模式的结果上限。类型/enum/bounds 直接表达机械规则，
不加调用例子或 next_request。

响应侧优先处理完整实体与检索摘要的重复：当前 lexical 每项返回完整 Block + label + excerpt + evidence + rank。
实际 preview 记录中，改为实体 ID + 原有摘要/排序信息时，紧凑 JSON 字符数：migration 2316→1131、Nimbus
8651→4206、retry 5991→2668。这是字符体积检查，不是已实现效果或 token/调用次数承诺。

已接受 retrieve 负责返回可寻址候选和已有命中信息，完整基础记录通过 get_entity、内容解释通过 Resolver 获取。
lexical 保留已有 label/excerpt/evidence/rank；semantic 保留实体引用与 score、现有分支元信息，不为了对称新增
摘要生成或隐式 hydrate。实体引用应与 get_entity/邻域入口一致，具体引用形状仍需共同确定。

hybrid 保留两种模式的独立结果与错误，不混排不可比较的分数，不自动生成答案或静默回退；某分支未配置时返回
简短、准确的能力错误，另一分支结果可用。空匹配不包装成“没有相关信息”或系统错误。

已接受的取舍：候选响应更轻，但需要完整内容时增加一次按需读取；应在同一预算的真实轨迹中检查总请求成本与
信息质量，不以响应字数降低单独判断成功。此前“不裁剪 Resolver 的实际结果”仍成立，这里改变的是 retrieval
Tool 的候选投影，不改变 retrieval owner 的原生 API。

## Record organization candidate（D-536 accepted）

保留一个工具及两个参数：block_id（D-538，替换 information_id）；behavior 从当前注册、能记录候选的 Resolver 选择。
行为选项继续由 runtime 生成，每项只有必要的短语义说明；不新建静态行为清单、不按行为拆 Tool。
Tool description 只表达“标记整理候选，不执行整理”。不新增 reason/confidence、示例或 next_request。

当前 `behavior_resolver_classes()` 还要求 can_run_automatic/run_automatic。这不是 record_candidate 的调用依赖，
却会排除只能记录候选、执行由其它入口承担的 Extension Resolver。建议候选工具目标筛选只要求注册的 Resolver、
行为说明及 record_candidate 能力；自动 Job 的可执行性仍由其原 owner 判断，不门控候选标记。

错误分清 Block 未找到、行为不可用和无效参数；行为不可用时给出可用目标名称，方便重新选择，不自动换到
rumination，也不隐式执行。重复标记继续复用原候选关系。

响应保留现有 descriptor / relation / created 三项，不包完整实体、状态报告或固定任务链；明确 created 只表示
候选 Relation 是否新建，不表示目标行为已执行。ID 可供 get_entity / 图查询继续使用。

此工具只承诺写入 attention signal，不把语义判断、执行调度、已评估或完成状态混入。诊断中出现无新增需要的
重复标记，仍需由行为判断质量处理；本轮不禁止同一行为的合理后续候选，也不引入循环检测或候选消耗状态。

## Record supersession（D-537 accepted）

保留两个端点参数和 successor --supersedes--> predecessor 方向。工具说明承载必要定义：同一主题下，后继信息
有权在前任全部适用范围内完整取代前任。字段说明解释端点，不加入长 SOP 或实现细节。
端点名称使用 successor_block_id / predecessor_block_id（D-538）；不再用 description 重复“Block ID”，已有
工具定义和名称足以表达的部分不重复说明。
对应 Agent definition 的 system prompt 承载识别 SOP；核对当前 definition 与初始 judgment context 的实际交付，
不能假设原有简短 prompt 已包含完整过程。首先使工具定义自足，再核对过程指导；SOP 的实质变化单独记录以便对照。
完整覆盖、语义时序与替代 authority 仍由已接受 behavior 判断，不因写入成功宣称语义已被再次证明。

预期错误分清端点缺失（指出缺失 ID）、相同端点，以及加入关系会形成已有 supersedes 环；错误说明清楚
“已有从 predecessor 到 successor 的路径”，不只输出泛化的 ValueError，不附 next_request 或自动交换方向。
现有 cycle 检查与顺序重放语义不变；暂不为错误返回额外构造完整路径/图区块。

响应保持 relation / created，无附加状态、报告或原实体副本；需要检查时可组合 get_entity 与图查询。
此方案仅改善 Tool 合同，不改变已接受完整替代模型，也不承诺解决原验收中的 scope/来源传播混淆。

## Record refinement（D-539 accepted）

参数为 refinement_block_id / predecessor_block_id；工具定义为同一主题、
相同或更窄范围内补充相容细节，前任仍可作为较粗描述独立使用，不取代其当前地位。识别 SOP 归 Agent definition。
保留端点不同/存在、成环检查及顺序重放，错误明确其原因；响应只含 relation_id 与 created。

## 后续语义核对（D-539）

Sir 已委托依据已接受产品设计与实际 Agent prompt 自主判断关系定义和识别过程，不再逐条要求复核既定语义。
本次核对不是批准新的接口职责或新增产品条件。以下是既定合同的承接方向，尚未修改源码：

- evidence stance：可归属的证据在可比较范围内，为完整断言提供支持或挑战理由；不宣告断言真伪。
  使用 evidence_block_id / assertion_block_id / stance；保留 supports/challenges 枚举。同一对端点的相反立场
  错误不应被描述成“整个图不允许意见冲突”；不同证据可以持不同立场。
- synthesis：产生保留来源、分歧、不确定性和说话者归属的多源综合信息。source_block_ids 是实际贡献来源，
  不是所有浏览过的上下文；副本不增加独立佐证。previous_synthesis_block_id 表示此次修订的旧综合，
  延续 edited 关系，不解释成 supersedes。来源缺失、来源集合不足等机械错误与语义质量分开。
- existing referent anchoring：将来源中的指称片段连接到已有、可区分身份的对象；不把整个复合 Block
  当作指称，也不新建目标实体。source_block_id / selected_text / referent_block_id 保留原有职责。
- duplicate assertion：完整断言来自同一来源发生实例，且没有独立证据、推理、决定或实质增量；
  文字相同或结论一致不充分。left_block_id / right_block_id 不暗示取代、删除或指定权威副本。

核对依据：technical-design 下各对应 operation-contract；实际 app/business/organization/{refinement,
evidence_stance,synthesis,referent_anchoring,duplicate_assertion}.py 的 judgment_contract；
tests/organization/acceptance/test_black_box.py 的 _BEHAVIORS / _create_agents。
目前 system prompt 仅给出简短行为目标；较完整条件通过 _shared.build_seed_message 的 judgment_contract
进入初始消息。不能声称 system prompt 已承接完整 SOP。现有条件总体与上述关系定义一致，但条件清单
不等于完整识别过程。工具定义应先补足；SOP 的位置/内容调整另记对照变量，不在工具修复对照中悄悄修改。

## 目标与依据

让 Agent 能从工具合同知道如何发现、调用和纠正操作，减少方法猜测、无效请求与无关上下文。
依据：[Tool 检查](acceptance/agent-tool-review.md)、[预算诊断](acceptance/budget-diagnosis.md)、
[真实追踪验证](acceptance/preview-agent-debug-verification.json)。历史八次失败没有原 Thread 明细；不能把这些
发现宣称为每次失败的确定根因，也不能把追踪小任务成功当作工具改进有效的证据。

修复保留 resolver / retrieve 的组合与 owner 结构，图查询按 D-531 改成少量直接工具；保持七个行为独立、精确写入、
单一 candidate 工具和普通图结果。
这一轮固定 `qwen3.6-plus`、12 次请求预算、候选选择和 Agent system prompt/行为 SOP。仅修改工具描述、schema、
发现和预期错误反馈；已有语义 authority 错误和局部失败扩散继续保留为独立未解决项。

## 1. 先修发现与纠错闭环

主要落点：`app/business/organization/tools.py`，方法合同仍由 ResolverManager / Graph Navigation owner 提供。

- 优先通过 schema、发现和错误响应教导。description 仅保留必要用途/语义并尽量短；一般不提供调用例子。
  已知道合法方法时允许直接 invoke，不强制每次先 describe、不添加 runtime allowlist。
- `resolver.describe` 只有在未指定任何过滤器时才列全目录；显式指定的 Block 都不存在时，返回 missing_blocks
  与空的匹配结果。修复当前一次返回约 43KB 无关 catalog 的行为。
- 未知方法的 describe 保留 missing_methods，并附紧凑的合法方法名或可执行的发现指引；不再只有空结果。
- 未知方法的 invoke 明确告知方法不存在、请调用 describe，同时返回可用方法名列表；不返回完整的下一次请求。
  合法方法名来自 owner 的实时合同，不在 Organization 中复制一份清单，也不自动猜测并调用“近似方法”。
- 参数无效时返回对应方法的结构化 field errors 和所需的局部 schema；保留 index、Block、method 等关联。
  正常子项继续返回原结果，失败子项提供错误；不因一项失败自动重试整批或丢弃成功项。
- 未预期异常由开发追踪保留原错误。这里只转换已经识别的能力/参数错误，不把任意异常包装成可重试建议。

禁止引入 `next_request` 或换名的预制调用对象；不在说明中补回已撤回的调用例子。
未知方法响应中的名称列表来自 owner，完整参数 schema 仍通过 describe 按需取得。
错误字段的最终形状在实施前与 MCP 现有投影核对，保留其外部错误和资源交付语义。

## 2. 补齐对读取和写入都必要的参数语义

统一命名检查已完成，逐入口结果见 [Tool 命名检查](acceptance/tool-naming-audit.md)。覆盖现有全部工具、公共
方法及返回字段；当前是设计映射，源码改名尚未执行。

先按 D-538 检查命名，再决定是否需要 description。当前输入命名的同类修正包括
refinement_block_id、evidence_block_id、assertion_block_id、source_block_ids、previous_synthesis_block_id、
source_block_id、referent_block_id、left_block_id/right_block_id。它们显化现有 Block 身份，不改变各工具职责，
也不表示未评审工具的其它方案获批。实现同步修改 schema、handler/operation 参数和本 unit 调用者，避免新旧
名称互相翻译；不做数据库字段重命名或无需求的兼容别名框架。

主要落点：`app/schemas/organization_behavior.py` 与相应 Tool descriptions。

| 参数/能力 | 必须向模型说明的内容 |
| --- | --- |
| action、methods、resolvers、blocks、calls | 哪些是发现过滤器，哪些只用于调用；空过滤与未命中不同；calls 可批量独立读取 |
| method、arguments | method 来自 describe；arguments 遵循该方法返回的 input_schema；明确展示当前 owner 的可调用合同 |
| retrieve query/mode | lexical 适合辨识性词语/短语，semantic 依赖可用 profile；hybrid 返回独立分支而非融合排名；空匹配不证明资料不存在 |
| graph direction/contents/cursor | from/to 方向、Relation content 精确匹配、分页游标来自先前结果；不是语义搜索或 Block 内容读取 |
| source_block_ids | 综合实际采用且有实质贡献的完整依据，不是所有读过的 Block；重复传播不增加独立佐证 |
| previous_synthesis_block_id | 更新既有综合时的旧结果，产生 edited 连续性；不是另一个普通 source，也不自动断言 supersession |
| selected_text、referent_block_id | 来源中的最小、足够的指称片段；目标已存在并有身份依据；不能把整条 claim 当作指称路径 |
| successor/predecessor、refinement/evidence endpoints | whole-Block 断言、方向与行为区别；机械写入不会替模型补做 scope/authority 判断 |
| candidate block_id/behavior | 具体值得考虑的信息和已注册行为；是注意信号，不是已执行、已完成或要求立即重跑 |

写入描述从已接受模型合同提取最小使用信息，不新增 scope/referent/unit 的统一结构，也不把本轮案例写成专用规则。
description 必须出现在实际绑定给 provider 的 schema 中；Python 注释或 task 文档本身不足以解决问题。
上述内容是待核对的语义清单，不要求逐条扩写为 description。能由机制表达的规则优先由机制承担。

## 3. 对齐 schema 与实际校验

主要落点：Resolver 元工具输入、直接图工具输入 schema、方法 owner 合同。图工具不再处理 action 分支。

- 用 describe/invoke 的同源分支定义生成 schema 与运行时校验：invoke 的 calls 非空；describe 不接受非空 calls；
  invoke 不接受非空发现过滤器。保留现有平坦 JSON 请求形状与合法显式空数组，不新增一层 operation 包裹。
- 推荐先做小型 Pydantic RootModel/分支模型 spike，核对 AgentManager 绑定和真实 provider 接受度，再替换隐藏的
  model_validator 条件。若 provider 不支持该 schema 形状，记录具体限制后调整技术实现，不用复杂手写 schema
  复制一套业务规则。
- 在方法 owner 上补 docstring/参数 metadata，声明现有范围和 bounds；反射只投影这些声明。优先使用 Annotated /
  Field 等现有 Pydantic 能力，不另建方法 registry。保持直接 Python 调用已有的约束，不为了 Agent 改窄 owner API。
- 已有 bounds（例如 neighborhood limit 1～100、find_path max_hops）进入生成 schema；空文本、distinct source IDs
  等规则在可表达时投影，并有清楚描述。不虚构系统不能机械验证的语义保证。

## 实施顺序与影响面

1. 在当前可追踪 preview 保存未修工具的真实基线；记录 source SHA、模型与 definitions、语料状态、自动 seeds。
2. 完成同源 schema 小型 spike，冻结实际字段兼容与 provider 接受结果；核对 MCP 对 owner 合同的消费。
3. 实施 Resolver 发现/错误修复、字段语义与 schema 投影，并迁移图查询的直接 Tool IDs 和 Agent Tool sets。
4. 静态验证后部署到 PR #100，重新启用并确认追踪，再做整个信息世界的端到端对照。

顺序表示依赖，不是拆成多个 delivery slices。预计修改 surfaces：

- `app/business/organization/tools.py`、`app/schemas/organization_behavior.py`；
- `app/business/info_base/resolver/main.py`、必要的 Resolver 合同/方法描述；
- `app/business/graph_navigation_retrieval/main.py` 的既有方法合同和错误；
- 相应局部回归验证、unit/deployment 文档、task evidence 与 release fragment。

不改模型预算、自动 candidate 策略、Agent runtime 调度、正式 Thread persistence、数据库 schema 或 shared Hub。
MCP 是共享 owner 的现有消费者：发现 schema 会更完整，但不得缩减其可调用能力或改变成功结果、Resource 行为。

## 验证与判断

Sir 最新约束：不得新增任何回归测试或聚焦测试。此前新增回归文件已撤掉；已有测试只同步必要接口变化。
机械条件通过静态检查与代码审阅核对，实际行为通过端到端黑盒验收观察；不另建针对单个工具的测试套件。

效果对照使用真实 preview、相同模型/12 次预算/system prompt/SOP 与还原后的相同信息世界。
整组验收从自动 Job 开始，不提供目标 pair/source set。自动 seeds 的差异必须在证据中说明，不能
把不同候选恰好变简单解释成改进。原先 SQLite 诊断只作参考，不当作这轮远端 A/B 的同等基线。

从实际追踪比较：未知方法/参数拒绝、错误后的下一步是否有效、无关 schema 响应量、重复或空查询、有效读取/写入、
自然停止/预算终止与耗时。结合图结果判断，不能把“更快结束、少写图”单独当作成功，也不能接受以降低语义质量
换来的少调用。只做有解释力的有限重复，保留全部运行，不挑一次好结果。

若工具误用减少但正常工作仍超过 12，再单独评估预算档位；若主要仍是 scope、来源语气或模型判断问题，则转入
对应已知修复项。此次工具修复不承诺解决所有语义问题；unit 仍需完整 best-effort 黑盒复验和 Sir 的整体判断。

## 运行与证据维护

Sir 已授权 preview 操作，无需逐次确认。每次部署后核对实际开关/日志可读，不能只看配置脚本成功。
临时 PR100 配置 helper 目前只在自身文件变化时触发；新部署可能覆盖 backend，执行前必须确保对当前 head 再启用。
实施时一并落实本分支的配置衔接，合并前移除 PR100 专用临时 workflow/script。

导出真实轨迹并检查不含 provider 凭据；按本次已记录 IDs 清理临时数据。完成每轮后更新 implementation-evidence、
unit packet 与 PR 的诊断结论。同模式调整按 D-540 实施；需要改变既定能力或产品语义的新取舍另行复核。
