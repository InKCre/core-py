# PR #100 preview 黑盒验收

2026-09-10；被测提交 `a8c929d87619ee2f036629aef006bc75297729b2`。模型为真实 DashScope
`qwen3.6-plus`，使用已获 Sir 授权的本机 provider 凭据。凭据不进入本证据目录。

## 运行边界

普通 Core/PostgREST 输入 → 部署中的 scheduler → 七种 Organization Job → 普通图读取。
每个 Job `max_seeds=3`、timeout 900 秒，每个 Agent turn 最多 12 次模型调用。
18 项首轮语料来自已接受的两个 information worlds；没有传入 focal ID、pair 或期望 relation。
七个 purpose-built definitions 使用各自精确写入工具与三个读取元工具，另有一个 candidate 工具。
此轮仅维护 lexical projection，没有配置 embedding provider；semantic retrieval 不可用。

首轮 rumination 先执行，其余行为并发执行；全部结束保存快照后，才新增 Nimbus remediation revision 3
以及普通 `edited` relation，再运行第二轮。并发行为可读取同轮已经提交的结果，不声称彼此隔离。
preview 初始 Blocks、Agents、providers 和 Jobs 均为空。冷启动后 Core ready、PostgREST 可访问。

原始图和 Job 证据见 [preview-100-results.json](preview-100-results.json)。只记录输入、持久结果和 Job
终态，不读取或保留模型推理过程。运行器是一次性 HTTP 验收脚本，与仓库内直接调用本地 JobManager 的
测试入口不同；本次证据验证了实际 preview scheduler 和远端 provider 的调用路径。

## 首轮观察

- Lexical Job 索引 18 项，failed/unavailable 均为 0。
- Organization：rumination、supersession、duplicate assertion 正常结束；refinement、evidence stance、synthesis、
  existing-referent anchoring 因 `Organization Agent exceeded its per-Turn model-call budget` 失败。
- 图由 18 Blocks / 6 Relations 增长至 35 / 36，其中 7 个 Block 是 behavior descriptors。
- 失败 Job 仍可能已写图，因此必须同时检查 Job 和 graph，不能以 failed 推断无持久效果。

已发现的实质问题：

1. **范围覆盖错误**：Relation 18，`1 --supersedes--> 2`，把新的欧洲 50 上限公告作为旧 30 上限的完整替代；
   Block 4 却说明旧租户在迁移前仍受 30 上限。当前 graph relation 没有表达这个限制，不能据此把旧规定一概视为历史。
2. **综合遗漏关键条件**：Block 30 依据 Blocks 1/2 综合出“2025-03-12 起上限由 30 增至 50”，没有纳入 Block 4 的
   渐进迁移条件。其两条 `synthesis` 来源边真实存在，但最终文本可能误导对旧租户的使用。
3. **来源语气被增强**：Block 24 把 Block 10 的事件先后写成“timeline attributes checkout errors to a routing change”；
   原文明确没有判定唯一根因。它还把数据库团队关于 retry amplification 的判断写成观察事实。后续 referring
   fragments（如 Block 34）进一步复用了这类文本。可追溯来源并不等于忠实于来源。
4. **局部预算失败扩散**：四个 Job 的一个 turn 达到预算即退出整个 batch，剩余 seeds 的处理无法完成；与 accepted
   candidate-local failure continuation 预期不一致。不能用增加全局预算替代对错误范围与实际阻塞原因的检查。

可保留的有效结果：Nimbus revision 2 → revision 1 的 supersession（Relation 26）对应明确的批准替代；
Lab replay 与转载报告的 duplicate edge（Relation 33）恢复了同一来源传播关系。但本轮小样本不证明稳定可靠性。

## 第二轮与后续读取

第二轮结束为 44 Blocks / 63 Relations，其中包含主动输入的 revision 3（Block 36）。正常结束的三个行为为
rumination、supersession、existing-referent anchoring；另外四个仍因相同 per-turn budget 错误失败。
两轮共 14 个 Organization Jobs：6 finished、8 failed。这只是执行统计，不能当作语义正确率。

- `36 --supersedes--> 17`（Relation 50）表明新修订可被自动发现；Block 39 的综合来源包含 revision 3。
  但是首轮没有相应 Nimbus synthesis，故本例未观察到旧 synthesis → 新 synthesis 的 `edited` 闭环。
- **明确的模型混淆**：Relation 54，`14 --supersedes--> 15`，把独立实验原报告置为转载报告的语义后继。
  转载来自原报告，并不是被原报告后续替代的旧版本。这种原始来源与派生传播关系应保留 provenance，不能作为
  supersession authority。第一轮已经有 `14 --duplicates assertion--> 15`（Relation 33）。
- **错误继续传播**：Block 38 写成 routing change caused checkout errors，仍指向只给出时间线的 Block 10；
  Block 39 引用了首轮派生 Block 24，继续带入其来源增强的解释。保留 attribution 并没有充分限制这种传播。
- **可见的自我纠正机会**：Block 44 明确指出 Block 33 丢失数据库团队的不确定语气，并生成 `11 --candidate for-->
  rumination descriptor`（Relation 63）。这说明模型能识别前序结果的问题，但本轮没有完成错误派生信息的修复。
- **有价值的综合**：Block 42 明确保留“仅测过 migrated tenants、未测 legacy tenants”，并指出 newsletter 是
  derivative communication，不能增加独立佐证。该结果满足本样本的 scope 与 count-once 解释要求；然而 Block 30 的
  无条件限制综合仍保留，没有获得明确纠正关系。
- Anchoring 新增 `revision 2` / `revision 1` 指称片段及对应路径，可用于版本来源定位；也仍存在把整条派生 claim
  当成 referring fragment 的混用，尚不能据样本证明该行为稳定满足最小指称语义。

正常 HTTP lexical retrieval 的结果见 [preview-100-use-reads.json](preview-100-use-reads.json)：
`migration` 能召回 Block 4（以及 7/8）；`Nimbus` 和 `retry` 能召回原始与首轮派生信息。
这些查询发生在第二轮期间、完成第二次 maintenance 后；没有给 Organization 传入未来 query。
它们证明关键限制可由现有检索取得，不能替代 semantic retrieval、`read_lineage` 或 connected-component
专用接口的运行证据。本轮未通过这些专用读取接口验证其算法正确性。

实际 Agent、model 和 config 形状见 [preview-100-deployment.json](preview-100-deployment.json)。该文件保留部署
SOP 与 Tool identities，不包含 provider 密钥。

## 清理与最终判断

全部 Job 终止后，清理并再次读取确认：63 Relations、44 Blocks、16 Jobs（含两次维护）、7 Agents、1 model、
1 provider 和 7 个行为 configs 已删除，新增对象残留 ID 均为空。与 provider 相关的远端临时凭据也随 provider
记录删除。语料和图结果保存在本目录，可用于复核，远端数据不能通过应用恢复。

**本轮验收已执行完毕；建议不通过整组语义验收。** 原因是已经观察到错误 supersession、scope 条件遗漏和
来源语气增强，并非因为要求每种行为穷尽成功。两轮内部分有价值结果不能抵消这些会误导后续使用的 authority。
最终 Human disposition 由 Sir 复核本报告。

后续修复应维持已接受的模型边界：

1. 按实际请求/Tool 错误和预算消耗定位预算耗尽原因；实现候选局部失败隔离与可观察诊断。仅提高预算不足以说明修复。
2. 在 behavior SOP/部署 definition 中明确查找限制/例外、语义后继与来源传播的区别，以及事实/推断/不确定语气的保持。
   本轮没有读取 chain-of-thought，因此不臆测这些错误具体发生在哪一步。
3. 重新运行完整信息世界，观察错误是否减少、旧结果是否能通过正常 organization 得到纠正；不只重跑已知成功 pair。

未覆盖：每个 Job 仅 3 个自动 seeds；单一模型和英文语料；没有 embedding retrieval；尚未观察到既有 synthesis
的完整版本更新；Extension 自有 behavior、外部 pointer 静默变化与长期运行。自动 candidate 的随机性和同轮并发
也属于本轮条件，不能从两轮统计推算可靠性。
