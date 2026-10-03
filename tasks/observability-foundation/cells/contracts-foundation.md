# C-G1：共享契约基线

状态：2026-10-03 业务契约已返回 G1；D10 补齐默认关闭、本地显式 opt-in、PG 保留及 mixed Peer 语义；按信号出口与 carrier 形状保持。主 Agent 拥有契约设计与兼容判别；授权表面仅为任务内提案、只读调查和 disposable 数据库实验。未修改 Hub、共享挂载或运行源码。

## 返回

[共享契约形状](../design/shared-contract.md)已经确定身份/config、两列 carrier、512-byte 约束、SDK 超限 state 省略、PG 日志兼容与协调升级。[Hub patch](../design/hub-contract.patch)是四文件未应用差异，[评审说明](../design/hub-review.md)记录归属和交付边界。

标准 Python/JS propagator、真实旧 Python repository、TS JobManager/DBAPIClient 经 PostgREST 均有证据。缺少 carrier 的旧创建正常，已有 carrier 在 claim/close 后保留；模拟新 head 导致旧 readiness 拒绝，因此不宣称任意旧新版本滚动兼容。SDK 注入合法 tracestate 可超过 512 bytes，应用持久化政策与 W3C 上限明确区分。详见[实验报告](../experiments/convergence-20261003.md)。

## 下一消费方与不变量

C 的下一消费者是 Hub 发布和 core-py 数据库协议/各语言采集实现，具体顺序由[工作地图](../task-map.md)拥有，不另建控制入口。正式 migration、生成投影、初始化命令与跨 Peer 运行仍须实施验收；实验 DDL 不是正式发布物。

Job 领取、取消、timeout、终态和未知结果语义不由 Trace 决定；没有上下文的 Job 仍可执行。部署 ID 不提供权限、不从 secret 派生、不由各 Peer 随机各生成一份。发现共享 truth 冲突或新持久成员需求时返回主任务，不扩展成通用执行/遥测存储。

本单元完成不清理任务包；Q1/Q2 的生产内容与预算输入不阻挡已完成的契约基线，也没有因此被默认为已确认。
