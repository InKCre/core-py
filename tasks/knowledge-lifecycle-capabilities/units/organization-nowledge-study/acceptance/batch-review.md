# 批量实体读取与结束指导重验

结论：本轮初始世界已完成并清理，整组验收不通过。Refinement 三次均自然结束；rumination 仍耗尽，
synthesis 也耗尽。新增 get_entities 的指定 ID 分支存在真实模型调用失败，须先复核修复方案。

## 运行边界

- 服务代码：`faa74ba442342e4df3b04344cf7daa1256da1fac`。
- Preview deployment：34553741646 成功；CI：34553743079 成功；debug：34553740623 首次配置读回失败，
  重试后成功。没有为此修改代码或反复创建行为 Job。
- 定义：D-546 的两份 SOP 修正、D-547 的 get_entities；其余五份 SOP 不变。Qwen3.6-plus、12 次预算不变，
  预算不进入 system prompt。没有新增测试；复用两套交织信息世界的初始阶段，未跑 upstream-change 阶段。
- 前三种行为顺序运行、后四种独立入队。前序图变化会影响后续 seeds，不是逐 seed 严格对照，也不是单变量实验。
- 原始定义、工具 schema、完整轨迹和最终图：[tool-repair-batch.json](tool-repair-batch.json)。
- 被撤回运行的现场已先补齐导出并清理：[closure-cleanup.json](closure-cleanup.json)，仅作审计，不作验收证据。

## 运行结果

| 行为 / Job | 模型调用次数 | 结果 |
| --- | --- | --- |
| rumination / 49 | 8、10、12 | 第三次预算耗尽 |
| supersession / 50 | 5、3、4 | 全部自然结束 |
| refinement / 51 | 5、5、4 | 全部自然结束 |
| evidence stance / 52 | 11、6、2 | 全部自然结束 |
| synthesis / 53 | 12 | 写入后预算耗尽 |
| existing-referent anchoring / 54 | 4、9、7 | 全部自然结束 |
| duplicate assertion / 55 | 2、4、3 | 全部自然结束 |

共 19 次执行，17 次自然结束、2 次预算耗尽；116 次模型请求、109 次工具请求。5/7 Job 完成。
上一轮为 133 次模型请求、158 次工具请求、0 次调用错误；本轮请求数减少不能当作纯效率改善，
因为新增参数错误改变了读取路径，synthesis 也未能继续后续 seeds。

## 批量读取：随机成功，指定 ID 全部失败

22 次 get_entities 请求中，一次 `entity_ids=null, random_count=20` 成功返回当时全部 19 个不同 Block；
其余 21 次指定 ID 都把数组表达为字符串，全部验证失败。未观察到真实成功的指定 ID 或 Relation 批量读取。

实际 schema 的 entity_ids 通过 anyOf 表达 array/null，属性本层没有 type；OpenAI-compatible dialect 原样传递
tool.input_schema。模型能正确生成 Resolver calls 等普通数组，却在此反复生成字符串。因此高优先级推断是
schema 形状与当前模型/服务的参数生成不兼容，尚不能宣称已独立证明 provider 内部根因。

错误反馈还有具体问题：Pydantic 返回 “Input should be a valid tuple”，而不是模型使用的 JSON array 术语。
Job 52 随后甚至把方括号字符串改成圆括号字符串，仍然失败。不能靠重复该内部类型提示实现有效纠错。
总计 22 次工具错误：21 次上述错误，1 次 Resolver invoke 缺少 calls。没有偷偷加入字符串转数组兼容层。

## 两个重点行为

### Rumination：未解决，不能只归因于预算太少

第三次 focal 为 183（批准的方案 revision 2），与上一轮同一原始信息角色，仍在 12 次耗尽。

1. 已给 focal 文本，第 1 次又并读 get_text、get_raw_content、get_relations。
2. 第 2–5 次检索和读取前一版；第 6 次批量实体读取失败，第 7 次改用 Resolver 读取。
3. 第 8–9 次补读关系和假设/重放材料。
4. 第 10 次提交 supersedes、responds to、gates rollout on 四条关系。
5. 第 11–12 次继续查假设到重放的路径、新闻副本的邻域，随后耗尽。

这次没有重现“转交后因没出现下游关系而自己接管”的相同序列：第二次执行确实在标记 evidence stance 后
自然结束。第三次仍在完成当前修改后扩展到相邻问题；不能仅凭这条轨迹把所有探索都判为无价值，
也不能把移除一次参数错误直接等同于保证结束。先消除工具干扰，再讨论是否需要进一步改 SOP。

### Refinement：退出行为有改善，非稳定性证明

三次分别为 5、5、4 次调用；第一次针对独立的五月事故、第三次针对替代方案，均明确 no-op。
第二次把 177、178、179 三条团队材料分别以 refines 指向时间线 176，三条 mutation 同轮发起。
未观察到独立检索批量发起的明确收益；本轮更直接的证据是承认 no-op，不为找到 refinement 持续搜索。
候选已不同于上一轮派生 summary，不能把单次结果当作所有场景下预算问题已根治。

## 语义结果与残余

- `184 distinct from 176` 清楚区分五月缓存事故与六月支付事故；`183 supersedes 182` 正确衔接方案修订。
- `180 supports 179` 保留了实验支持假设的关系；synthesis 193 的五个来源没有把新闻副本当独立证据。
- Synthesis 保留 09:12、09:31、09:38 三个事件、团队 attribution 和未定根因；但最后一段把数据库团队
  “believes retry amplification contributed” 重述成 “observation that retry amplification occurred”，
  将相信提升为观测，与它自己前文保留的限定不一致，仍不合格。
- `183 gates rollout on 180` 及 `195 refers to 180` 把方案所需的 production-scale replay 与现存实验重放
  认作同一对象。文字相关不足以证明该实验就是上线门禁的那次重放，更不能证明门禁已通过；这是待复核推断。
- 三条 refines 混合了团队观测、约束、假设与官方时间线。新细节有价值，但不同信息角色是否满足细化合同
  仍需逐项复核，不能仅凭同一事故判定。结束文本误写一次“179 refines 179”；实际图为 179→176，不存在自环。
- Duplicate assertion 没有新增副本关系；正常结束并不证明副本发现覆盖充分。

## 下一修复候选：仅提案，未实施

建议先让 entity_ids 成为普通数组字段，默认空数组表示随机取样，random_count 保持原义；非空数组指定 ID。
这样消除 array/null 联合类型，不增加容错解析层或更长 description。Relation 分支仍要求非空 ID。
这是接口从 null 到空数组的调整，须先由 Sir 确认。随后按相同世界重验；在工具干扰消除前不继续叠加 SOP。
如果保留 null 是必要合同，则需另选保持合同的 schema 表达，不应无声改变它。

## 清理

已删除本轮 29 个 Block、27 条 Relation、8 个 Job、7 个 Agent、1 个模型、1 个 Provider，恢复或移除临时
organization 配置；相关日志已导出后移除，所有运行数据表 remaining_new_ids 为空。图和轨迹保留在文件中。
未将本次不通过结果隐藏为“阶段完成”；后续修复方案等待复核。
