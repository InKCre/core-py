# 三种剩余预算耗尽：轨迹诊断

状态：Sir 要求诊断；后续仅按 Sir 建议应用 null 类型提示，其它修复待复核。证据为
[references 原始记录](tool-repair-references.json)，代码 f4362ad。

## Sir 复核后的进一步定位

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
