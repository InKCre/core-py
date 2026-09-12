# 不以排除遗漏作为结束前提：复测

D-555 已实施并完成 preview 初始世界执行。6/7 个 Job 完成，19/20 次执行自然结束；evidence stance
三次均结束，但 refinement 仍有一次无产出耗尽。因此不能宣布持续检索问题已解决，也不能把更快写出
不符合语义合同的关系算作质量改善。原始证据见 [discovery 记录](tool-repair-discovery.json)。

## 条件与变更

源码 ebf220ad043cb00926332abdbb686caa06e1e9a5。Preview application 34687842214 与临时调试部署
34687841831 均成功后启动验收。只替换六种探索型 Agent 的共享目标/结束指导，删除被替代的重复句；
rumination 的独立提示词与三工具组合不变。实际 thread 记录确认新指导进入运行。

仍为 qwen3.6-plus、12 次模型调用预算、max_seeds=3、同一初始 fixture；前三种行为顺序运行，后四种
独立入队。预算没有进入提示词，语义 Profile 仍未配置，只在组织前维护一次词法索引。本轮不新增测试，
只给既有驱动增加 discovery 输出模式，没有运行 upstream-change 阶段。自动候选及前序生成图不同，
不是严格单变量重放；不能把轮次差异全部归因于提示词。

## 执行结果

| 行为 / Job | 模型调用次数 | 结果 |
| --- | --- | --- |
| rumination / 89 | 4、4、5 | 全部自然结束 |
| supersession / 90 | 7、3、11 | 全部自然结束 |
| refinement / 91 | 9、12 | 第一次 no-op，第二次无写入耗尽 |
| evidence stance / 92 | 6、6、6 | 全部自然结束，三条 supports 写入 |
| synthesis / 93 | 6、5、11 | 前两次 no-op，第三次创建综合 |
| existing referent anchoring / 94 | 5、4、3 | 第一次 no-op，后两次锚定 |
| duplicate assertion / 95 | 4、3、2 | 全部 no-op |

共 116 次模型调用、137 次工具调用。两次工具错误均来自 rumination 第三次执行的首轮 draft_graph：
将 text 写成 content，收到缺失字段/额外字段错误后恢复，最终提交成功。没有为此追加修复。
最终图为 33 Blocks、24 Relations。

## 与本轮问题直接相关的轨迹

Evidence stance 不再出现 focal 轮 Job 84 的无产出搜索耗尽，但本轮 seed 分别是技术摘要 347、事故
提取内容 344、rollout 条件 348，而非完全相同的原始方案。它分别写入 341 supports 347、342 supports
344、341 supports 348；理由是原文的权威与包含相同内容。这里没有可见的、超出来源重述的证据贡献，
与既定“citation/repetition alone 不构成 stance”合同不符。可以确认执行结束，不能据此确认获得了
正确的 evidence stance 或证明结束指导单独有效。

Refinement 第二次的 seed 346 是 rumination 生成的“原始测试与转述”概念区分。调用 1–3 已读概念、
新闻及其引用的测试；4 起继续搜索 original test、evidentiary weight、distinction、methodology 等。
调用 5 随机读取 20 个 Block，后续仍换词和扩展邻域，最终 12 次耗尽，没有任何写入。模型可见文字在
调用 7/11 仍表示要寻找相关概念或更具体说明；新指导没有使这个执行形成有用的停止判断。

Supersession 第三次也多次搜索可能存在的 revision-1 technical changes Block，到第 10 次才写入，
第 11 次结束。因此自然结束不等于搜索已经高效。写前重读仍存在，例如同轮 get_entities 和 Resolver
获取相同文本；本轮没有消除这一已知成本。

这些观察支持的有限结论是：该判断原则已表达并被实际加载，但单靠本次措辞调整尚不能稳定解决探索
收敛。不能从调用记录断言模型的内部心理，也不能因此改预算、缩小开放探索范围或擅加新的执行约束。

## 语义观察与 best-effort 边界

正向观察包括：refinement 第一次正确拒绝将原文已经显式包含的 rollout 条件提取当作信息增量；duplicate
assertion 拒绝原文与局部提取的 whole-Block 重复边；anchoring 没有把尚待通过的 rollout replay 指向
已复现故障的历史实验；综合 357 保留三个来源 337/338/341 及 rollout 前提。

除上述 supports 外，仍有语义残余：347 是技术摘要而非完整提案，却又 supersedes 340；rumination 将
同一五月事故的原因/结果与排除内容连为 explicitly unrelated to，混淆了句内排除项和整个 Block；综合
使用“confirming the hypothesized failure mechanism”，其强度需要与实验复现、历史事件因果分别理解。
这些如实保留，不把 best-effort 解释为关系自动正确，也不因本轮观察而追加未获批修复。

## 清理与交接

执行、最终图与 Agent 日志已导出。33 Blocks、24 Relations、8 Jobs、7 Agents、1 Model、1 Provider
已清理，所有 remaining_new_ids 为空，无驱动 failure。临时配置已恢复/移除，本轮 Agent 日志导出后删除。
当前不继续修改提示词或工具；新的修复方案先经 Sir 复核。
