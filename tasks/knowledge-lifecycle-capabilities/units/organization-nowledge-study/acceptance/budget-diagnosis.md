# 预算耗尽诊断（2026-09-10）

结论：受控复现更支持 **12 次上限偏紧，同时存在可减少的工具探索开销**，未观察到持续死循环。
不能把原 preview 的 8 个 budget failures 全部归因到同一原因：原始 Thread 调用明细没有保存，且只有进程内存
持久化，当前无法恢复原执行的逐次记录。本报告区分代码证据与新的诊断实验，不把实验当作历史精确重放。

## 计数语义

`app/business/agent/thread.py` 中 `_run_turn` 每请求一次模型加 1；一次请求返回的多个 ToolCalls 只占这一次。
计数是每个 seed 的 turn 独立预算，不是整个 Job 共用。`tests/organization/acceptance/test_black_box.py` 的部署准备
选择了 12；它不是 Organization 全局固定上限。

第 12 次若仍返回工具调用，runtime 先执行工具、追加结果，然后返回 `MAX_MODEL_CALLS`。它不提供第 13 次让模型
查看结果并结束的机会。若第 12 次直接返回最终答复则正常完成。预算值也没有作为剩余次数告知模型。
所以“预算耗尽”只证明截止时模型仍请求工具，不证明无进展或死循环。

## 实验

复用 `qwen3.6-plus`、原验收保存的 Agent definitions/Tool sets、实际 Thread 循环、实际工具 handler 与精确图操作。
预算改为 24，只在隔离诊断中使用，观察第 12 次检查点之后的行为。

原始 18 项语料和首轮 35-Block 图 + revision 3 分别作为两个固定起点。图存储在临时 SQLite 副本中；lexical
retrieval 使用 preview 的真实维护及 HTTP 检索接口，保留与起点相同的信息。未配置 semantic retrieval。
不同案例从自己的初始图开始，不共享实验产生的修改。未传入预定目标 pair 或 source set。

本机 AsyncOpenAI 出现连接阶段错误，而同步 OpenAI 成功。最终实验用同步传输并移入线程，保持原 dialect 的消息、
Tool schema 和响应序列化。网络/数据库载体不同、选定 seed、固定图快照、无同轮并发和模型随机性，都限制其与
历史 preview 的可比性。起始 request 使用 behavior description + 原 judgment contract。

只保存 Tool 请求/结果与计数，不保存模型推理过程。完整轨迹：

- [原始语料上的两例](budget-diagnosis-results.json)
- [较复杂图状态上的三例](budget-diagnosis-expanded-results.json)

| 行为 / seed | 模型请求次数 | 终态 | 超过 12 时发生什么 |
| --- | ---: | --- | --- |
| synthesis / 1 | 7 | completed | 未达到 12 |
| refinement / 17 | 9 | completed | 未达到 12 |
| evidence stance / 11 | 14 | completed | #12 新增支持关系；#13 补读两个派生片段；#14 完成 |
| existing-referent anchoring / 24 | 11 | completed | #5/#6/#7/#9/#10 分别完成不同锚定 |
| synthesis / 36 | 16 | completed | #10 创建综合；#11～15 继续读取/检索、标记 candidate、读取新综合；#16 完成 |

五例没有重复的同名工具 + 完全相同参数请求；结合逐步结果，没有观察到持续重复的错误反馈循环。
这不等于证明每个动作都有必要：特别是 synthesis / 36 创建后仍有额外检索和自指向本行为的 candidate，存在
停止条件与效率的改进空间。终止和语义正确性也是不同指标；实验再次出现语义遗漏，不能因自然结束就判质量通过。

## 具体开销

- synthesis / 1 猜测 `read`、`get_syntheses_for_block`；evidence stance / 11 猜测 `content`；这些方法不存在。
- synthesis / 36 在 #1/#2/#5 分别使用不存在的 `read`、`incoming_relations/outgoing_relations`，或把
  `get_text` 交给 graph 工具。随后转用正确 Resolver 方法，属于可恢复但浪费请求的错误。
- 有多次空 lexical query，以及完成主要写入后的继续探索。空查询或后续检查本身不等于死循环，但会挤占紧预算。
- 原 definition 允许开放探索并强调谨慎验证，但没有给出“什么时候足够、该结束”的具体操作指导，也不显示预算。
  这是解释实验表现的一个可能因素，尚未通过单变量对照证明。

## 建议

下一轮先把 purpose-built Agent definition 的预算从 12 提到 **24**，保留上限，观察实际停止点与成本。
24 是给本次观测到的 14/16 次轨迹留出余量的实验档位，不是从五例推导出的可靠全局默认值。
不要因为 Job 失败而先做循环检测框架或自动重试；当前没有支持这种投入的证据。

同时可单独对照改善 Tool/SOP 提示：不清楚方法时先 describe；Resolver 读取与 Graph Navigation 的归属；主要
产物完成后只有具体未决问题才继续探索。先保留元工具设计，不从几次方法误用反推拆成大量工具。

预算调整不能替代原验收中的错误 scope/authority 修复，也不能证明 candidate-local failure 已隔离。
这些问题保持独立。此次仅完成诊断，没有修改生产 runtime 或已部署的 Agent 配置。

诊断结束已删除恢复到 preview 的所有语料与 maintenance Jobs，临时 SQLite 副本随运行退出删除；没有在 preview
新增 provider/Agent/config。本机 provider 凭据只用于本机调用，未写入证据。
