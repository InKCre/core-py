# Existing-Referent Anchoring Operation Contract

- **状态**：D-509 accepted exact-model Technical contract。
- **范围**：关闭 existing-referent anchoring 的 candidate、identity judgment、command、replay 与 query use；不设计新
  Entity materialization、same-as merge、通用 mention extraction 或 contextual-link vocabulary。

## 要产生的最小区别

```text
source information --has mention--> referring fragment
referring fragment --refers to--> existing identity-bearing information
```

`refers to` 的主语必须是实际完成指称的可寻址信息单元，而不能因为一个较大 Block 内含某处指称，就让整个 Block
直接充当主语。`has mention` 只断言来源包含这个指称片段；`refers to` 才断言该片段实际指向右侧已经存在的 referent。
后者比词面出现强，因为字符串出现不等于 identity resolution；它又比 `same as` 弱，因为左侧是一个指称表达，不是
referent 自身的另一身份。

referring fragment 是普通 `core.text.v1` Block，内容是来源中足以定位本次指称的最小 selected text。它不是新 Entity、
canonical name 或通用实体抽取结果，也不要求系统抽取来源中的所有实体。existing referent 也不是 Entity 类型，而是
已经包含足够身份信息、可作为跨来源/时间连续点的任意 Block。

只有当来源 Block 本身已经恰好是最小指称单元时，来源与 referring fragment 才可以是同一个 Block，并省略
`has mention`；普通复合信息不得使用这个例外。

## 例子

```text
R：Atlas 欧洲迁移项目；内部项目号 atlas-eu-2026，目标集群 pg-prod-3。
I：昨晚 Atlas 切换后，pg-prod-3 的 replication slot 保留了 800 GB WAL。
M：Atlas

I --has mention--> M
M --refers to--> R
```

以后从 R 出发可以先通过 incoming `refers to` 找到 M，再通过 incoming `has mention` 找到 I；读取 I 的语境仍可复核
为什么这里的 “Atlas” 指向 R。即使 I 中还有另一个实体，关系也不会错误地声称整份 I 在指代 R。

以下情况 unresolved/no-op：

- 系统里同时存在 Atlas 欧洲迁移项目和同名 Atlas 移动应用，而来源没有 disambiguating context；
- 候选 referent Block 只有裸文本“Atlas”，没有足够身份信息；
- 来源只是使用 “atlas” 作为地图册普通名词；
- 来源与候选主题相关，但没有任何表达实际 denoting 该 referent；
- 没有 existing identity-bearing Block；本模型不会为完成链接而新建一个标签节点。

## Whole-Block 规律在这里怎样应用

Whole-Block 规律不是通过把 `refers to` 解释成一个隐藏的 existential predicate 来绕过，而是通过让真正的指称表达
先成为 Block 来满足：`M --refers to--> R` 对 M 整体成立。一个来源可以拥有多个 M；同一 selected text 在不同语境中
指向不同对象时也可以形成不同 M。首版保留这个语义区别，但不承诺字符 offset、token position 或原始字节位置；这些
坐标会被 Resolver normalization、来源编辑和外部 Storage pointer 轻易破坏。

若需要表达“来源中的某个独立 claim 对 R 成立”，该 claim 仍须成为自己的 Block，再由对应精确模型连接。`has mention`
和 `refers to` 都不能承担 `reports about`、`supports` 或 domain-specific relation。

### 为什么不使用 `refers to:<selected-text>`

这个写法少一个 Block，但把 selector 与稳定语义谓词混在 Relation content 中：每个文本都会形成新的 content，现有精确
过滤与 fetchsert identity 无法直接复用；相同文本出现多次仍不能区分语境；来源编辑也会改变关系身份。因此 active
candidate 付出一个普通 Block 和一条 `has mention` Relation 的低成本，以换取稳定可查询的 `refers to` 语义。若未来确实
需要精确高亮，再为已证明的读取需求设计 source-native locator，而不在首版预埋通用 span schema。

## 候选形成

`ExistingReferentAnchoringBehaviorResolver.consider_candidate(seed)` 以 referring information 为通常 seed，但不假定所有
识别出的名词都值得锚定：

1. Resolver 提供完整文本、source-native identifiers、链接、作者/频道等可用含义；
2. LLM/Agent 临时识别可能具有跨来源复用价值的 explicit/implicit mentions；
3. lexical/semantic retrieval、exact identifiers 和 bounded graph neighborhood 寻找 existing identity-bearing candidates；
4. Agent 主动搜索同名/同类型竞争 referents、旧别名、版本/环境冲突和时间连续性；
5. Agent 为每个 resolved referent 选择足以定位该次指称的最小 source-grounded text；初始候选集合不限制 Agent 继续探索。

候选排名、referent/scope fields 和精确字符坐标不持久化。判断成功时，selected text 作为普通 referring-fragment Block
持久化；graph authority 是 `has mention` 与 `refers to` 组成的路径。

## Identity judgment SOP

对每个候选 pair 依次确认：

| 条件 | 必要原因 | Agent 要确认什么 |
| --- | --- | --- |
| **有意义的指称** | token、引用示例或偶然同词可能不值得建立语境路径 | 来源确实用该表达指向一个对未来 use 有复用价值的对象/概念/项目/系统等 |
| **片段充分且最小** | 整个来源过粗，裸 token 又可能让语境无法复核 | selected text 能识别本次表达；没有携带与指称无关的大段内容，也没有把两个不同指称混成一个片段 |
| **existing referent** | 本模型不创建新 Entity | target Block 已存在，且不是 Agent 为本次链接临时制造的标签 junction |
| **identity-bearing target** | 名称相同不足以支撑跨来源连续性 | target 含稳定 identifier、充分独特描述或可恢复关系上下文，足以和 plausible alternatives 区分 |
| **denotation continuity** | 相关、相似或同类型不等于“指的就是它” | 来源表达与 target 是同一 referent，包含别名、改名或时间变化时仍有可解释连续性 |
| **scope / time compatibility** | 同一名字可在环境、组织、版本或时期指向不同对象 | 来源上下文与 target identity 的适用范围相容；历史名称变更不会被误当成同时身份 |
| **竞争候选排除** | false anchor 的损害通常大于 missing anchor | 已考虑可合理找到的 alternatives；不是因为检索只返回一个结果就断言唯一 |
| **可复用路径价值** | Organization 不为每个名词或图形密度建边 | 该 anchor 预期能改善跨来源/时间 query/use，而不仅是重复 source 已显然可用的信息 |

结果只有：

- anchor：八项均有充分依据；
- `unresolved`：identity、scope 或 competing referents 不能排除，或者没有 existing anchor；
- `no-op`：确认只是同词/相关、没有 denotation、没有可复用价值或 exact edge 已存在。

首版由 purpose-built Agent 进行开放世界 identity judgment。稳定 ID、URL、账号/项目编号、别名与已知关系可以是强
evidence，但没有任何一个字段或 confidence threshold 单独授权 relation。

## BehaviorResolver 与 exact command

```text
ExistingReferentAnchoringBehaviorResolver.consider_candidate(seed)
  -> selected-text candidates + existing referent candidates + competitor context
  -> Agent applies the eight conditions
     |-> unresolved / no-op
     |-> record_organization_candidate(...) for an independently useful representation gap
     `-> anchor_existing_referent(source_id, selected_text, referent_id)
```

Agent definition 使用 Resolver/retrieval/navigation Tools、`anchor_existing_referent` 和谨慎的 candidate-marking Tool；不
取得 generic `submit_graph`，也没有 create-Entity Tool。

`anchor_existing_referent()` 在调用者事务中：

1. 验证 source 与 referent 是两个不同且已存在的 Block，selected text 非空；
2. 在同一 source + selected text + referent 路径已存在时复用它，否则创建 occurrence-local 的普通 text Block；不按
   selected text 在整个 info-base 中全局合并；
3. fetchsert `source --has mention--> referring fragment`；
4. fetchsert `referring fragment --refers to--> referent`；
5. 返回 referring-fragment Block ID、两条 Relation ID 与本次实际创建的效果。

命令不试图机械证明 selected text 的来源语义或 target 是否 identity-bearing，因为 heterogeneous Resolver meaning 没有
诚实的统一 substring/schema 检查；这些属于 Agent 的语义判断。它不创建 target、不合并 Blocks、不写 reverse edge、
不检查 cycle，也不把 selector 或 identity evidence 复制进 Relation payload。

reference graph 可以合法互相指称或形成 cycle；`refers to` 也不具有 lineage/transitive semantics，因此不建立 closure。

## Replay、automatic run 与 use

同一 source + selected text + referent 的顺序重放复用既有两跳路径；unresolved/no-op 不持久化。自动路径从新/变化
信息、显式 `candidate for` 与尚无相关 anchor 的有界 seeds 开始；一次运行的结构化诊断只声明本次 bound 与实际
选择，不声称所有 mentions 或 alternatives 都被检查。首版不为尚未证实的并发重复风险增加 mention identity schema
或唯一索引。

later use 复用现有 graph navigation/retrieval：

- 从 referent 沿 incoming `refers to` 找到具体指称片段，再沿 incoming `has mention` 找到过去不可稳定召回的来源信息；
- 从来源沿 outgoing `has mention` 看到它的已解析指称，并继续走 referent 的其它关系；
- 读取 endpoints 与邻域复核 identity/provenance，而不是把 anchor 当作物理 merge 或 canonical representative。

不新增专用 query index、Entity page 或 eager “read together” law。若 `refers to` target 后来通过 `edited` 获得新版本，
这只是 identity reconsideration evidence；是否补充/替换 anchor 仍由 anchoring behavior 重新判断。

## D-509 关闭的选择

1. 普通复合 source Block 不直接 `refers to` referent；指称片段先成为普通 Block，形成
   `source --has mention--> fragment --refers to--> referent`；
2. identity target 必须已经存在并携带足以排除 plausible alternatives 的身份信息；“只找到一个候选”不充分；
3. 选择额外 Block，而不是 `refers to:<selected-text>`；它保存可读 selected text，但不保存脆弱的精确
   offset、reason 或 identity payload，也不创建/合并 Entity；
4. 同一 source + selected text + referent 的顺序重放必须收敛；不同来源中的同字文本不得因 content fetchsert 被误并。
