# CLI Sink / inkcre-cli

- **阶段**：Implementation。2026-09-14 Sir 已批准 [Impact Handshake](impact-handshake.md) 并明确“开始”；基线为 D-603。
- **目标**：让 Agent 和命令行用户在工作上下文中，通过独立 CLI 取用信息并操作 Core。
- **边界**：同仓库 cli/ 独立 Python/PDM project，pip 包 inkcre-cli。仅 Core 普通 REST；不导入 Core、不直接访问数据库、不作为 Peer，不是未来 Rust single-binary Peer。
- **位置**：core-py feat/inkcre-cli，base b3ccb00ca2e235bfcc9b9f4f4cc17948c59ef54a；决策 D-571–D-610。
- **授权**：获批范围内的源码、文档与验证可以执行；设计/preflight 已提交为 a953676。2026-09-14 Sir 进一步授权自由提交、推送和创建 PR；明确禁止合并。正式发布仍必须经过各 owner 的 protected-main 流程。
- **当前事实**：P1–P5 源码/本地文档已落地，[本地候选验收](local-acceptance.md) 四条旅程及相关静态构建通过。runtime 0.1.3 本地已准备、未发布，Core pin 未提前改变。共享 DB 未 reset。
- **下一步**：按 owner 提交、推送并创建 PR，先 runtime 与 Hub，再 Core/client-web。runtime 正式发布后才更新 Core pin；Hub 合并后单独更新 refs。遵守禁止合并的授权边界，交付跟进见 [delivery.md](delivery.md)。
- **关闭条件**：[四条旅程](acceptance.md)、相关 runtime/Core/client-web 交付、CLI 正式 PyPI 安装复跑全部通过。preflight 不替代它们。

## 产品与命令

[产品边界](product-design.md)、[研究与现状](research.md)、[命令面](command-surface.md)、
[连接与访问](connection-access.md)、[输入与动态发现](input-discovery.md)。

Agent-friendly 的判断是能发现能力、正确构造输入、理解部分结果和后台工作，而不是强制 JSON 或堆叠命令。
默认人类可读，JSON 模式紧凑；本机 connection 与 deployment config 分开，动态能力由 Core 发现。
普通 REST 可以按 CLI 首个消费者需要重整，但既有 Peer protocol 消费路径独立保留。

## REST 与内容合同

[实体与 Resolver](entity-resolver-rest.md)、[检索与 Graph](retrieval-graph-rest.md)、
[内容传输](content-transport.md)、[内容交付](content-delivery.md)、[文件输出](file-output.md)、
[输出呈现](output-presentation.md)、[清单与部分失败](list-error-contract.md)、[各查询续读](query-continuation.md)。

[Job 控制](job-control.md)、[Job/Source/Cron REST](job-rest.md)、
[显式整理 Job 与实体修改](organization-write-rest.md)、[Agent/AI 管理](agent-management-rest.md)、
[deployment config](deployment-config-rest.md)、[Peer](peer-rest.md)、[Extension](extension-rest.md)。

get 批量取得实体记录，可选择原始或 hydrated content；solved content 属于 Resolver 方法。
显式 collection/organization 创建 Job，不以 Peer inbound 同步执行业务。停止是 best-effort，等待不是停止。

## 实施依据与证据

[独立项目与依赖](project-and-dependencies.md)、[版本与发布](release-and-distribution.md)、
[校验边界修正](validation-boundary-correction.md)、[完整预演总览](preflight.md)。

具体预演分为 [校验/取消调用链](preflight-call-sites.md)、[Mail runtime 实验](preflight-runtime.md)、
[REST 接合](preflight-rest.md)、[独立构建与发布工具链](preflight-toolchain.md)、
[真实环境与交付前置](preflight-environment.md)。不为同一事实创建另一份 control authority。

D-602/D-603：Pydantic 留在输入与必要的复杂类型恢复；已有 typed 值不重复验证，普通管理 GET 和 CLI
返回只转换。允许一次原生模型恢复的附带约束，不自建无验证 decoder。

## 文档 owner

CLI 用法/安装/发布归 cli/；普通 REST 与 Core 内部实现归本 Spoke。
共享 Job 合同和经证据确认的通用边界按 Hub-first 流程提升。具体 Extension capability 留在其 Spoke。
Organization 旧单元的 Hub reconciliation 保持独立，不因本次准备顺带清除或提交。
