# Preflight：实施前结论

状态：2026-09-20，关键源码调查与隔离实验已完成，可以进入 Impact Handshake；新功能尚未实现或验收。
D-629–D-631 的修正已补充源码与文档核对：保留普通 Tool controller，注册机制无需扩展；移动后的
冷启动验证和文档 authority 纠正已纳入 P1/P4。其它运行证据保持有效。
执行次序来自 [实现计划](implementation-plan.md)，验收问题来自 [acceptance](acceptance.md)。
具体命令、结果与证据局限见 [实测记录](preflight-evidence.md)，真实材料与问题依据见 [corpus](corpus.md)。

| 检查面 | Preflight 结论 | 实施与验收需保持的边界 |
| --- | --- | --- |
| 动态 REST/schema | 两实例挂载、独立撤下、重启、schema 刷新实验通过；当前 FastAPI 保存 router 包装对象 | 保存实际注册对象并按 identity 移除；CLI 查具体实例路径；静态 OpenAPI 不伪造实例 |
| 读取工具 owner | 六工具的输入、helper、导入点与 OrganizationError 偶然依赖已枚举 | exact IDs 不变，显式 bootstrap；旧 Organization 运行需要回归 |
| Job 结果闭合 | 真实 Thread 的六条取消、超时、最后轮次与无提交路径通过 | 未闭合 batch 可丢失结果；新 handler 的数据库收尾仍须端到端核验 |
| 启停与 claim | 已复现启动未完成时禁用却留下运行实例；同实例管理操作串行可消除该交错 | Manager 内局部修正，不锁运行 Job，不增加分布式协调或恢复框架 |
| catalogs/readiness | 新 Job 可由现有 builtin profile + db init 收敛；Sink type 走既有启动同步 | 不增加表、列或 schema migration，不自动创建实例/Agent |
| 内容体量 | SQLite 正文投影 12,002 字符；真实模型接受全部六个读取工具 schema | 不静默截断，不承诺任意长材料均可容纳；preview 核验真实轨迹 |
| 环境与模型 | dev 已收敛到当前基线且 ready；真实 Alibaba dialect 工具调用闭合通过 | production 目前无 AIModel，验收需配置；未对 production 写入 |
| 语义 corpus | SQLite、InKCre 检索文档与 NASA 真实媒体已固定材料/摘要和问题依据 | 不用固定产品 ID 或测试专用行为；实际建图与索引留到验收环境 |
| 发布 | main 基线、Core/CLI release projects 与 fragment roots 已核对，静态基线检查通过 | 新功能尚无 PR/preview；按 D-628 验证实际发布，不借用旧成功记录 |

源码调查还表明 Agent/AI can_execute 是静态本地判断，不探测远端 Provider；不把远端在线作为 claim
前提。缺少单个查询路径不能升级为整个 Job 不可领取。确有无法执行的声明能力时沿已有资格判断处理。

run.py 的 require_peer_jwt 在 core_router dependencies 上，不是全局 middleware。动态 route 需显式
复用同一依赖，不能假定挂入 api_app 后自动继承；此为正常 REST 接合检查，不新建认证方案或安全审计。
独立只读复核特别指出 CLI path key 与 Organization 冷启动注册是两个实际回归点，已纳入预演/验收。

预演不能以新增永久测试接口或产品分支换取方便。临时实验与结果放在 unit evidence 或忽略的工作目录，
保留命令与结论；新自动化测试需另有准入理由，不由这个列表自动产生。
