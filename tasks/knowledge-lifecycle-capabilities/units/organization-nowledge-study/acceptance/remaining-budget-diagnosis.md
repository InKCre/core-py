# 三种剩余预算耗尽：轨迹诊断

状态：Sir 要求诊断；后续仅按 Sir 建议应用 null 类型提示，其它修复待复核。证据为
[references 原始记录](tool-repair-references.json)，代码 f4362ad。

## Sir 复核后的进一步定位

### focal 轮 evidence stance / Job 84 根因复核

**后续讨论：不完备信息下怎样结束（待评审）。** Sir 指出无法读完整图与担心遗漏之间的张力。
当前方案不是让模型确信图已搜全，而是区分“本次结束探索”与“断言图中不存在相关证据”。no-op 只是不修改，
不构成不存在性证明。因而继续探索应基于下一项获取动作的预期信息价值，而不是停止前必须消除一切遗漏可能。
这是判断原则，不要求输出理由、固定步骤或额外报告，不暴露预算，也不限制 Agent 只能使用初始候选。

初始 seed 足以支持适量探索；发现具体引用、可定位来源、相关命题或能够纠正已知检索错配的新路径，都可支持
继续。负结果也可能使改换策略有价值，不要求每轮必须命中新 Block。仅仅“可能还有证据”、对同一空泛目标
反复换词则不自动构成有价值的新线索。无具体有希望的下一步时可以结束，即使仍承认图中可能有遗漏。
后续新信息或新线索可以重新触发组织；这不是本次必须解决全图的理由，也不新增永久 no-op 标记或状态机。

拟将任务成功标准表达为“实现当前有依据的组织改进”，而不是“排除所有遗漏后给出结论”。这与已有允许 no-op
不同：不止准许退出，还解除退出对充分检索的隐含证明责任。实际能否改善需复测，不能承诺换一句 prompt
就消除模型行为问题。未实施。

Sir 接受“有产出但继续工作而耗尽”可以有价值；本例没有任何写入，因此继续诊断，而非把预算终止一概当失败。
原始证据为 tool-repair-focal.json。12 次模型返回的可见文本均为空，只有工具请求；不能把下述策略归因
描述成模型亲口表达的想法，也不能声称已证明其内部停止条件。

**已证实的输入条件。** Seed 305 是修订方案：批准状态、三种计划采用的机制，以及 rollout 以 replay passes
为前提。它不是宣称修复已奏效或 replay 已通过的实验结果。邻接的 311 只是抽出的方案标题，304 是旧方案，
这三者不能仅凭内容相关、版本先后或同源重述产生 supports/challenges。
自动 seed 选择将 candidate、近期关系端点/Block、随机 Block 合并；本轮 305 进入时并非已验证的 stance pair。
宽泛候选本身符合自动组织的职责，不应因此要求用户提供问题或让确定性筛选承担语义判断。

**已证实的轨迹。** 调用 1/2 读取输入已有的 305 和邻域已完整返回的 311；调用 3/4 得到旧方案 304。
调用 5 起持续搜 approval、replay test production、balancing/retry 等；调用 10 又搜索 approval decision、
replay test passed。没有命中可用的批准记录或修复验收记录。调用 8 的 Nimbus 已扩大到事故材料；调用 11
邻域才返回应用假说 301；调用 12 的 Reliability Lab replay load 为空，实验 302 正文没有 load。
12 次检索中 6 次为空，其余多次返回已知方案；不存在工具错误或写入失败后的重试。

**资料边界。** Fixture 的实验 302 复现了 routing rule 引发的故障模式，没有检验新的 remediation 机制，
更没有报告它们通过了 rollout 验收。即便更早定位 302，也不能直接把它当成“方案有效/验证已通过”的证据。
这不排除它对某个更窄命题有价值，也不意味着所有方案/决策类 Block 都不适合 evidence stance；但不能
把条件“通过后才能 rollout”变成需要被证实已经发生的事实。

**最有解释力的根因假设。** Agent 未把宽泛 seed 收敛成实际可比较的断言与证据问题，转而围绕方案寻找
可能存在的证明材料；这些材料未出现时，继续换词寻找，而没有结束当前没有成立的比较。现有专用 SOP
着重“判断一对完整 Block 的方向/scope/stance”与“已 settled pair 后停止”，共享 no-op 指导则很概括。
它们允许退出，但在“尚未形成 pair”时没有在实际行为上阻止无依据的继续求证。故问题不是缺一条禁止循环
的规则，而是目标形成与信息价值判断没有生效。此处是对轨迹和指令结构的推断，不是已隔离验证的单一因果。

长词法查询和重复读取是可见放大因素；语义通道缺失进一步提高寻找材料的成本，却不是足以解释全部失败的
根因。即使读得更快、召回更好，仍需承认没有合适关系可写；不能靠提高预算或放松 whole-assertion 语义掩盖。
这也不是“有了很多产出还想多做一些”：整个执行没有 record_evidence_stance 或其它写入。

本轮只诊断并更新 packet。未改工具、提示词、候选选择、预算或测试；后续方案仍须 Sir 复核。

### guidance 轮之后：能力组合与确认性复读复核

D-554 已实施恢复专用 rumination definition，原先“待复核”提案的当前状态以本段为准。
Agent 只绑定 get_draft_graph_schema、draft_graph、submit_graph；完整独立提示词只使用输入的 focal/context，
不再与共享探索提示拼接。现有黑盒和 preview 驱动同步装配方式。其它六个 definition 的工具列表未变：

| 行为 | 自有写入 | 读取/探索的具体用途 |
| --- | --- | --- |
| supersession | record_supersession | 比较完整版本、scope 与可追溯连续性 |
| refinement | record_refinement | 比较增量及适用范围，识别已有关系 |
| evidence stance | record_evidence_stance | 寻找可比较断言、证据与来源路径 |
| synthesis | create_synthesis | 获取多源材料、既有综合与来源/副本关系 |
| existing referent anchoring | anchor_existing_referent | 找到既有身份承载 Block，消歧并复用已有路径 |
| duplicate assertion | record_duplicate_assertion | 比较完整断言、追踪 provenance occurrence 与副本连接 |

六者共同读取工具为 get_entities、resolver、retrieve 和三种图检索工具；公开 Resolver 入口是读方法适配。
find_path/connected components 提供跨边路径和连通分组，不等同于单个邻域，不能由本轮少用判定可删除。
它们都没有 draft_graph/submit_graph 或别的行为的精确写入，candidate 工具保留已确认的前置整理协作。
本轮没有发现足以支持继续削减这些工具的职责偏移；这不声称每个工具在每次执行中都必需。

共享提示词已明确无需仅为准备写入重读已有完整内容。派生内容准确性残余按 Sir 确认的 best-effort 接受，
不实施此前提出的额外准确性提示。静态检查与代码核对覆盖装配方式，未新增自动化测试或新一轮真实模型运行。

Sir 追问原 rumination 是否拥有图探索能力。迁移前 a8c929d^ 的 organization.py 提供草稿 schema、draft_graph、
submit_graph，入口预先提供 focal 文本与直接关系；test_rumination_graph.py 的 Agent 仅绑定 draft_graph、
submit_graph。旧 runtime 按配置选 Agent，不能从测试断言所有历史部署都没有额外工具，但仓库原有用法
不包含主动图探索或 candidate 工具。本 unit 的验收将通用读工具与 record_organization_candidate 加给
rumination，并使用共享候选指导，实质扩大了 Agent 的能力组合。只改 focal 措辞没有恢复原用法。
建议恢复 rumination 专用 definition（草稿 schema/draft/submit），移除主动探索和 candidate 指导；保留其它
behavior 的能力以及外部把 Block 标为 rumination candidate 的机制。此建议尚未实施，待 Sir 复核。

已检查当前写入工具 description、输入 schema、返回模型和 guidance 实际回执：submit_graph 返回 ID 映射，
exact relation 返回 relation_id/created，synthesis/anchor 返回相应 ID 与 created；均未附带读回确认指令。
共享 prompt 明确说成功回执足以确认，不应为验证写入复读。AgentManager 从 definition 构造系统消息，
Thread 传递完整消息历史；所查仓库路径没有追加确认指令。此结论不涉及服务商可能存在的内部机制。

guidance 轮共有 11 个发生写入的执行，10 个在最后写入后无工具调用直接结束；另一个 supersession 在
写入后搜索 Nimbus remediation revision 3 approved，属于后继探索，不是读回结果。此前报告中的明显重复
读取主要在写入前（输入已有 focal 内容却再读取，或同批邻域与实体读取重叠）。因此不能把当前残余继续
归为“谨慎确认写入”。工具职责措辞、输入与工具结果呈现差异仍可影响动作选择，但现有证据不证明某句
说明是根因，更不能因为没有找到外部诱导就断言模型天生谨慎。

派生内容准确性可通过更精确的语义指导改善，但不能承诺只改 prompt 即解决。候选最小原则是保持源信息的
断言强度与否定范围，明确区分新增推断、原文事实与信息未给出；同时保留反刍产生新理解的空间。对于
“未独立 reproduction”扩成“未 investigation”、新增 gating 被称为 preserved，这比泛泛要求谨慎更贴近
错误。已有保留 uncertainty 指导不足以证明新增一句必然有效；不引入强制重读或自审循环。尚未实施。

Sir 再次明确：rumination 在本 unit 是迁移，不是重新设计产品行为。已查迁移前 a8c929d^ 的
app/business/organization.py：原入口明确为 focal-Block rumination，输入包含 focal_block 与 direct_relations，
Agent 由配置选择。当前验收 definition 的开放式措辞不能反向成为产品 authority。修复应恢复目的，
不是重新批准一个范围更小的新行为；也不能声称旧代码禁止一切外部检索。

检索优化提案（待复核）：保持单一 retrieve 与 mode，不改召回算法，不新增工具或查询语言。
在 query 字段准确区分 lexical 的词面条件与 semantic 的意义描述；用少量共享方法指导说明查询应来自
已知材料、邻接关系能定位时可沿图获取，允许 Agent 自主选择。空结果不附 next_request 或预制查询，
不强制失败次数或先图后搜。语义 Profile 配置是另一项验收条件，不用同时开启来掩盖词法策略问题。
先评审契约与提示词的最小修正，再用现有黑盒运行观察空查询、已有内容复读与语义结果，不新增测试。

此前“路径低效”不是 rumination 最上游的问题。入口明确传 focal_block，既有产品称 focal-block
rumination；但验收专用提示词以 Reconsider information openly 开头，共享提示词允许沿新线索继续，
没有明确要求探索服务于 focal Block 的反刍。这里有职责表达扩张：允许使用检索不等于要求整理整个主题。
不应以增加检索效率来掩盖这个问题。尚未修改 rumination 提示词，待复核其最小修正。

Evidence stance 的空结果不是“缺语义检索所以无路可走”：已有 Nimbus 名称和时间线 234，
后者邻域可以到达应用假说 237。模型最终也能缩短关键词，但很晚才这样做。因此更直接的失败是
查询策略与现有能力不匹配，语义通道缺失使其更明显；不能从单轮判定模型总体智力不足。

重复读取要分开判断：检索 excerpt 后取完整实体本来可能必要，不能一概判成浪费；
Job 68 调用 3 邻域已返回完整 234，调用 6 再读，以及 Job 70 调用 3/4 已返回完整 225/226，
调用 7 再读，才是明确重叠。AgentThread 将 ToolResultMessage 追加到历史，并向下一次模型调用
传递 state.messages，未发现此层截断或丢弃。提示词强调读完整内容，却没有明确说明邻域中的
完整 Block 已满足读取要求；“工具动作替代信息需求判断”是有证据的候选原因，尚非已证明因果。
不因此禁用检索后取完整内容，也不增加去重缓存或运行时限制。

Sir 提议在 tool description 解释 null 可能来自实体类型错误；已局部应用到 get_entities 和
get_entity_neighborhood。保留 null 原语义、返回形状和类型输入，不自动重试或猜测类型。
其它提示词、检索能力、预算未修改；没有新增测试。尚未部署复测这项描述变更。

## 共同条件与结论边界

- 三次执行均在 12 次模型调用后停止，不是工具异常重试。不能据此证明死循环，也不能证明只需提高预算。
- 三者首次 hybrid 检索都返回 SemanticRetrievalNotConfiguredError，随后使用 lexical。
  `OrganizationRetrieveInput.query` 仅说明 “Search terms or a semantic description.”；没有区分词法匹配要求。
  `LexicalRetrievalManager.retrieve_local` 使用 simple plainto_tsquery 以及完整查询字符串匹配，
  不是按自然语言意图召回。语义式长查询与实际能力不匹配是可观察的放大因素。
- 已有共享提示词允许 no-op、禁止无新线索的继续搜索，不能再称“缺少退出许可”。日志没有可见的
  解释文本，不能声称知道模型内在退出条件。下述判断来自调用与实际返回。
- 验收脚本仅在组织行为之前执行一次 lexical maintenance；新写入 Block 不保证进入检索索引。
  这是检索与当前图不完全同步的额外限制，不能据此断言本轮一定漏掉了可用 anchoring target。
- 工具 is_error=false 不代表调用有意义：Job 68 将 Block 249 当作 Relation 查询，得到 null。
  D-552 的 get_entities 改动有效，但不代表全工具实体类型误用已消失。

## Rumination / Job 65 / 第三次执行

Thread：928de583-c48c-4fa5-8671-d10fc8d78713，seed 241（批准的修订方案）。

1. 调用 1–3 读取 seed、检索并读取旧方案 240。
2. 调用 4–5 搜索 Nimbus 并读取事故材料。
3. 调用 6 搜索 Reliability Lab replay Nimbus 只返回新闻 239；调用 7 删除 Nimbus 后才找到实验 238。
   实验正文没有 Nimbus 这个词，新闻却有；词面相关性与所需来源不一致。
4. 调用 8 批量读取实验和多份材料的关系，才沿图发现假说 237；调用 9 读取它。
5. 调用 10、11 分开写入已知端点上的四条关系；调用 12 标记实验为 evidence stance 候选，随后截断。

判断：有持续进展，不是确认回执的循环。成本主要是先文本检索扩张上下文、后读图，以及分散写入。
新闻已有 cites 指向实验，读关系能提供直接定位，但实际到调用 8 才读取。两次 submit_graph 的端点
此前均已读取，第一次结果也不提供第二次所需的新 ID，分开写入没有可见的数据依赖必要性。
这支持“路径和调用组织低效”，不支持“模型必须找到成果才肯退出”。最后仍有效写入，无法证明
再给一次会结束，也不能排除当前预算对这种有效工作确实偏紧。

## Evidence stance / Job 68

Seed 238，初始上下文已列出 cites、responds to、candidate for 关系。

- 调用 1 读 238/239/241/249；2 错将 descriptor Block 249 作为 Relation；3 查询新闻和方案的关系。
- 调用 4、6、7、10 的长查询分别包含 assertion/claim、caused、cause/root cause 等，均为空。
  调用 5 的 Nimbus incident cause 只得到不认定根因的时间线 234。
- 调用 6 又读已在调用 3 邻域完整返回的 234；8、9 重新查询已知 candidate 关系及 descriptor 反向关系，
  没有提供待判断断言。
- 调用 10 缩短为 Nimbus routing change 才找到数据库观察 235；11 读取；12 才搜索 Nimbus。
  尚未读到通过 234 的入边可达的应用假说 237，也未写 stance。

判断：主要堵在获取可比较断言之前。长词法查询、候选路由元数据绕路、已有内容复读共同消耗调用。
已有时间线 234 和 graph 工具，但没有使用其邻域寻找相关假说。不能把失败归因于 stance 判断太严格：
最有价值的候选尚未进入判断，也不应该放松 whole-assertion 语义条件来换取写入。

## Existing-referent anchoring / Job 70

Seed 248（前序生成的欧洲并发上限摘要）。

- 调用 1 读 seed；2 hybrid 长查询为空；3–4 读取 225、248 邻域，已获得 225/226 的完整内容。
- 调用 5 搜索 Atlas concurrency，得到 225 和不同产品 233；6 更长查询只返回 225；7 再读 225/226/233。
- 调用 8 Atlas concurrency limit referent、9 Atlas service parameter limit 均为空。
- 调用 10 再查 226 邻域；11 才搜索 Atlas，找到 rollout 等更广材料；12 批量读取，随后截断。

判断：尚未形成可写的身份锚定；在“关于该实体的文档”中持续搜索“承载该实体身份的 Block”。
添加 referent/parameter 等任务概念到词法查询没有产生身份依据。重复内容读取和串行改词增加成本。
初始 fixture 没有专门的 Atlas 服务身份 Block，但这不证明任何文档都不能承载身份，也不证明全图不存在
目标。保留 no-op 是正确的；本次轨迹不能证明模型已判定无目标后故意拒绝退出。

## 待评审方向，不是修复授权

优先澄清真实检索能力与 Agent 调用方式的契合，而非继续叠加通用“允许退出”提示词。
分别讨论：语义通道未配置的验收条件、词法查询的简洁契约/反馈、已返回内容的复用及已有图关系的使用。
Rumination 另有无数据依赖的写入拆分；另外两种行为则尚卡在目标发现。不要统一收缩探索权限，
不要把预算透露给模型，不新增测试，也不因三者同为 max_model_calls 就提出同一种修复。
