# Organization Nowledge Vertical Glossary

- **状态**：本 unit 的稳定讨论词表；由 D-464–D-525 已接受结论提炼，新增或改变实质含义仍需 decision。
- **范围**：只定义本 unit 新产生或被显著收窄的词。`info-base`、Block、Relation、Resolver、Collection、Application、
  Extension、Job 等沿用 Hub Product glossary，不在这里重新定义。
- **使用规则**：产品责任、实现位置和运行载体分别命名。除代码标识、专有名词和已经确立的 glossary 外，与 Sir
  讨论时使用中文。

## 基础模型

| 术语 | 本 unit 中的稳定含义 | 不表示 |
| --- | --- | --- |
| Organization | 对已经留存的信息应用明确语义模型，产生、修订或诚实拒绝一种可复用区别，使一类后续使用获得确定能力 | Collection、当前请求的答案、索引维护、图形清理或统一生命周期 |
| 组织模型（Organization model） | 一份概念性语义合同：语义问题、可接受判断、证据/权威规律、图表达、后续使用解释规律 | 数据库实体、Python 基类、registry、LLM/ML model |
| 演进性质（evolution property） | 信息使某种演进模型可能适用的非互斥性质 | Block 的唯一类型或持久状态 |
| 演进模型（evolution model） | 对某一种连续性、变化关系和后续解释负责的组织模型 | 所有信息共用的 progression state machine |
| 可复用区别（reusable distinction） | Organization 新增到 info-base authority、能够被未来调用者再次识别和使用的语义差异 | 为结构整洁而产生的边；一次调用中的临时推断 |
| 后续使用能力（later-use affordance） | 可复用区别让一类未知的未来请求能够做到的事，如区分当前/历史、避免重复计数或直接取得综合结果 | 对具体未来 query、主题或工作流的预知 |
| Organization operation | 在某次调用中把一个组织模型应用到现有图对象，并产生 no-op 或精确图修改的动作 | 通用 runner、Job 或持久 behavior row |
| 候选启发式（candidate heuristic） | 低成本提出值得判断的 Block、Relation、pair 或 set，控制成本并改善召回 | 语义事实、写图授权或跨模型统一规则 |
| 证据组装（evidence assembly） | 通过 Resolver、检索、图导航和必要探索取得一次判断所需的异构含义 | 把所有 Block/Relation 统一结构化 |
| 判断者（judge） | 对一次候选应用组织模型并给出 model-valid proposal、unresolved 或 no-op 的机制 | 组织模型本身；固定为 LLM、Agent 或 Human |
| 提案（proposal） | 判断者提出、但尚未成为 info-base authority 的精确模型结果 | 任意 GraphForm 或已持久化事实 |
| 命令（command） | 校验模型机械不变量并把有效提案写入普通 Block/Relation authority 的精确函数/API | 候选搜索、开放世界语义判断或通用 Organization dispatcher |
| unresolved | 现有证据不足以作出模型允许的肯定判断 | 失败、空字符串或永久不再考虑 |
| no-op | 本次判断完整结束且无需产生图修改 | persisted evaluation state；它仍可在未来新证据下重新考虑 |
| consumer | 按组织模型的后续解释规律消费已持久化区别，使承诺的后续使用能力实际发生的责任 | 新实体、worker、状态机或统一代码 owner |
| 执行适配器（execution adapter） | Job、route、Agent Tool 等既有运行入口的概念性角色 | 本 unit 要新增的类、协议或独立运行层；D-523 规定具体 operation 直接实现为 BehaviorResolver method |
| behavior-owned Organization Job | 某一 exact behavior 的独立自动调用载体；拥有 Job type、一次运行参数、claim 与 timeout，并薄调用同名 BehaviorResolver；D-519 把候选/判断/写图语义留给 Resolver | 组织模型本身、候选算法 owner、candidate-only Job、generic dispatcher、BehaviorReport 或来源产品的 Job family |
| Agent definition | 一个可复用、可被场景选择的完整 Agent 组合：system prompt、AI model、exact Tool set、tool choice 与 per-turn budget | 需要执行器再用第二份 allowlist 补完的候选配置 |
| 来源依据（source basis） | 一项综合结果实际从哪些已留存信息单元推导而来的完整集合，以入向 `synthesis` Relations 表达 | 重复写入 Block content 的 source list、固定数量门槛或自动真值 |
| Organization behavior descriptor | 一个 exact Organization behavior 在 info-base 中可寻址、可解释、可被 `candidate for` 指向的 ordinary Block；D-516 规定 exact Resolver type 是完整 identity、content 是空 canonical value；D-517 规定由已注册 target Resolver 在第一次真实 graph use 中惰性 fetchsert | Agent definition、Job、运行配置、待办状态、startup catalog sync 或独立 behavior 表 |
| BehaviorResolver | 以 behavior descriptor Block 为诚实 receiver，直接实现具体 Organization operation、`record_candidate()` 及 exact mutation/read methods 的 concrete Resolver；Agent-backed operation 读取自身 deployment config，一个共享 `record_candidate()` 让单一 candidate Tool 动态分派到 target | 信息 content Resolver、Resolver base、额外 ExecutionAdapter 层或通用 lifecycle |
| 跨模型候选（cross-model candidate） | 一个模型发现另一 exact behavior 值得考虑某个可寻址信息单元，并以 `candidate for` 保存的注意力信号 | 目标 behavior 已适用、已调度、必须成功或当前仍 pending |
| 来源事件（provenance occurrence） | 一次具体来源发生/发布所形成的信息出处；它可被多个 Block 复制 | 语义相同的所有独立来源 |
| 重新应用规律（reapplication law） | 某种图变化何时让一个既有组织模型值得重新运行 | 独立 Organization model、cascade engine 或持久 stale state |
| 跨模型不变量（cross-model invariant） | 多个组织模型都必须遵守的权威或效果限制 | 单独 runner、Relation 或 Job |

## 语义限定词

| 术语 | 本 unit 中的稳定含义 | 边界 |
| --- | --- | --- |
| 断言（assertion） | 一项信息所表达、可被支持、挑战、替代、细化或判为重复的命题性内容 | Block 不必只含一个断言；粒度不足以承载完整关系时必须 abstain |
| 范围（scope） | 一项信息或关系成立的适用条件，可涉及对象、时间、参与者、来源、地点、版本或情境 | 是判断问题，不要求所有 Block/Relation 具有统一 `scope` 字段 |
| 指称对象（referent） | 一段来源含义实际指向的、已经具有可辨身份的信息对象 | 名称或类型相似不等于同一 referent |
| 指称片段（referring fragment） | 来源局部、可寻址的普通文本 Block；保存足以定位一次已解析指称的最小 selected text | occurrence-local，不是 Entity、canonical name 或全局同名节点 |
| 连续性（continuity） | 两项信息在相关范围内属于同一可演进对象/断言线，而非仅仅主题相似 | 连续性本身不证明替代，也不要求一对一链 |
| 支配（dominance） | 在范围内，后项获得替代前项默认适用地位的语义关系 | 只属于 scoped supersession；refinement、support/challenge 不含支配 |
| 来源（provenance） | 信息来自哪个来源事件、主体或传播路径的可追溯依据 | 内容相同不证明 provenance 相同；Block ID 也不自动等于来源事件 |
| 断言来源事件（assertion provenance occurrence） | 相对于一项具体断言，一次独立产生其信息、证据或权威依据的现实事件 | 不是 Block、文本出现、URL、文档容器或每次转发；同一文档可包含多个来源事件 |
| 说话者归属（speaker attribution） | 一项话语、判断或承诺属于哪个主体 | synthesis 不得把 source/speaker 的立场伪装成系统自己的无来源事实 |
| 独立证据（independent evidence） | 来源事件和形成路径足以独立，因而可以作为额外 corroboration 的证据 | 两个 Block、两个 URL 或相同语义都不足以单独证明独立性 |
| info-base authority | 当前持久 Block/Relation graph 所表达的可复用信息事实 | candidate、LLM 输出、索引、读取投影、Job 状态和日志本身都不是该 authority |
| 权威规律（authority law） | 一个组织模型规定哪些来源、scope 和证据足以授权哪种判断与图表达 | 模型置信度、重复出现或运行载体身份不能替代它 |

## 已接受的模型与非模型责任

| 术语 | 角色 | 核心区别 |
| --- | --- | --- |
| 范围内替代（scoped supersession） | 精确演进模型 | 在已证明连续性、scope 和支配权威内，较新信息替代前项；产生当前前沿和保留历史 |
| 非支配细化（non-dominating refinement） | 精确演进模型 | 延续同一演进对象并增加内容，但不使前项失效 |
| 证据立场（evidence stance） | 精确演进模型 | 一项有来源的信息支持或挑战另一项范围明确的断言；双方继续存在 |
| 保留来源的多元综合（provenance-preserving n-ary synthesis） | 精确组织模型/方法 | 多项互补来源共同支持一项可独立使用的派生信息，同时保留来源依据、分歧、不确定性和说话者归属；`n-ary` 不表示固定数量 |
| 语境链接（contextual linking） | 开放模型家族 | 共享 candidate-to-assertion 纪律，但不共享一个万能 Relation 或 consumer |
| 既有指称对象锚定（existing-referent anchoring） | 语境链接家族中的精确模型 | 将来源中的隐含指称锚定到已经存在、身份可成立的信息；歧义时 unresolved |
| 来源感知的重复断言（provenance-aware duplicate assertion） | 精确模型 | 两个 Block 复制同一来源事件中的同一范围化断言；保留两者但不把它们当独立证据 |
| 依赖响应（dependency response） | synthesis 的重新应用规律 | 上游依据变化把“值得重新考虑”的压力传给 synthesis；不直接传导 stale/challenged 状态 |
| 规范性权威分离（normative-authority separation） | 跨模型不变量 | 重复出现或模型置信度只能支持描述性结论，不能凭空生成规范性/操作性权威 |

## 图表达与读取

| 术语 | 稳定含义 |
| --- | --- |
| 图区别（graph distinction） | 可复用区别在 Block/Relation authority 中的具体表达；可能是一条 Relation，也可能是派生 Block 加完整 Relations |
| Relation content primitive | 精确模型写入的简洁自然语义，如 `supersedes`、`refines`、`supports`、`challenges`、`refers to`、`duplicates assertion`、`synthesis`；这是使用指引，不是 registry/ontology |
| Resolver 读取投影 | Resolver 以诚实接收者身份读取当前图意义并返回使用侧解释；信息 content Resolver 只解释其 Block 内容，非平凡的 Organization Relation 解释由 exact BehaviorResolver 持有；读取不因此取得候选或写图权威 |
| 元工具（meta-tool） | 以一个稳定能力 owner 为边界，在一个 Agent Tool ID 下提供 typed capability discovery/invocation 或若干同意图模式；减少模型的 Tool 选择面 | 把 Resolver、retrieval、graph、mutation 等无共同语义 owner 的能力折成万能 Tool |
| Relation content 常量 | exact behavior module 公开的 module-level `Final`，是 writer、query 与 exact consumer 共用的持久 token 代码权威 | 全局 relation registry、枚举、数据库排他写权限或可随意改名的实现细节 |
| Graph Navigation query | 对持久 Block/Relation authority 执行有界、presentation-neutral 的拓扑读取；可按精确 Relation content 过滤，但不解析内容、排名或写图 |
| 应用层解释 | 应用把 Resolver/graph/retrieval 的读取结果用于当前请求，例如按 provenance occurrence 计数或选择临时代表；不成为图 authority |

当前接受的 Relation content 与方向如下；表是模型合同的使用指引，不是全局 registry：

| Relation content | 方向 | 表达的区别 |
| --- | --- | --- |
| `supersedes` | newer -> predecessor | 后项在已证明的 continuity/scope/authority 内替代前项 |
| `refines` | refinement -> predecessor | 后项细化前项，但不产生 dominance |
| `supports` | evidence -> assertion | 有来源的证据支持目标断言 |
| `challenges` | evidence -> assertion | 有来源的证据挑战目标断言 |
| `has mention` | source -> referring fragment | 来源包含这个可寻址的指称片段 |
| `refers to` | referring fragment -> existing referent | 该指称片段指向既有指称对象 |
| `duplicates assertion` | lower Block ID -> higher Block ID | 两端复制同一 provenance occurrence 的同一断言；方向仅用于稳定存储，不表示优先级 |
| `synthesis` | source -> derived synthesis | 目标是由该来源参与形成的 synthesis；全部入向 `synthesis` Relations 共同构成完整 source basis |
| `candidate for` | information -> exact behavior descriptor | 来源信息值得由目标 Organization behavior 考虑；不表示 pending command、适用性或成功 |

`edited` 是本 unit 复用的普通版本连续性 Relation，而不是六种 Organization 模型新增的输出 primitive：

| Relation content | 方向 | 表达的区别 |
| --- | --- | --- |
| `edited` | older -> newer | 后项是前项的一次新编辑版本；旧 Block 保留，Relation 本身不自动表示 dominance、refinement 或证据立场 |

可观察到 `edited` 时，精确模型可把它作为候选或重新应用信号。Storage pointer 背后的外部信息若无可观察变化，
系统不能保证产生该信号；这是明确的 best-effort 缺陷，不批准额外状态或全局版本系统。

## 暂停使用或必须加限定的词

| 词 | 处理方式 |
| --- | --- |
| `Organization behavior` | 含义过载。改说组织模型、Organization operation、执行适配器或具体模型名；只在自然语言泛指整项能力时使用 |
| `computed consumer` | 停用。分别说 Resolver 读取投影、Graph Navigation query、应用层解释或具体 consumer law |
| `planner` | 停用；Agent/LLM 不只规划，也可能通过精确 Tool 产出图修改 |
| `generic rumination fallback` | 停用；rumination 与 evolution、linking、synthesis 平行，不是它们的统一 fallback |
| `Crystal`、`Memory` | 仅用于描述 Nowledge；不得作为 InKCre info-base 的通用对象或 ontology |
| `currentness` | 只在范围内替代模型中指当前前沿/历史解释；不是全库 freshness 或通用 Block 状态 |
| `freshness`、`stale` | 必须说明具体 owner；retrieval freshness 是派生记录兼容性，不能替代信息时效、synthesis 重新考虑或 supersession |
| `derived-information dependency lifecycle` | 已撤回；使用来源依据、依赖响应、append-only continuity 和普通 supersession/refinement |
| `relation as force` | 仅是 D-475 研究压力：Relation 可能传递注意力/变化影响；尚无通用 force model 或 cascade runtime |
| `domain vocabulary` | 当前无 Product 位置，不进入本 unit 设计 |
| `Entity materialization` | 自动新建身份承载信息仍延期；既有指称对象锚定不包含它 |
| `OrganizationBehavior` runtime entity / registry | 仍不计划。D-505 复用 exact Resolver type/ResolverManager 表达和执行 behavior，不新增 behavior table、runtime base 或第二套 registry |
| Agent run-time Tool allowlist | 已撤回；为不同场景选择不同 Agent definitions，不为假设的错误配置复制 Tool authority |

## 维护规则

1. 对话或文档出现新词时，先判断它是否只是现有 glossary 的实现位置、运行载体或例子。
2. 只有含义会改变 Product/Technical/Acceptance 判断的新术语才加入本表，并关联 decision。
3. Product 稳定且跨 unit 有用的词，待本 unit closure 后按 Hub shared-doc workflow 提议晋升；晋升前本表不冒充
   durable Product authority。
