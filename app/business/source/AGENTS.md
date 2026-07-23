# source/ Local Guide

本文件只描述 `app/business/source/` 的局部事实、术语和变更风险。跨 `extension/source/info_base/sink` 的慢变量结构，先读 [docs/30-unit-tdd/business-pipeline-and-authority.md](../../../docs/30-unit-tdd/business-pipeline-and-authority.md)。

## 何时阅读

在以下情况进入本目录前先读这里：

- 修改 `SourceBase`、`SourceManager`、`SourceCollectJobManager`
- 修改 source 注册方式、采集状态持久化、任务调度逻辑
- 修改 source 与 info-base 的写入边界

如果改动会影响跨模块结构，再回头核对 [app/business/AGENTS.md](../AGENTS.md) 和 [docs/30-unit-tdd/business-pipeline-and-authority.md](../../../docs/30-unit-tdd/business-pipeline-and-authority.md)。

## 局部执行规则

- 区分三层对象：`source type`、`source instance`、`collect job`。不要把配置、状态、调度语义混写到一个层里。
- source 负责采集或记录外部输入，不负责定义 block / relation 的持久化规则；持久化协调仍归 info-base。
- `collect()` / `record()` 发生异常时，优先向上抛，不要在 source 内部静默吞掉并假装成功。
- 若要改变调度模型，先核对 `main.py` 与 `collect_job.py` 的双路径现状；这是本目录最大的变更风险。

## 关键文件

- `app/business/source/main.py`: `SourceBase`、`SourceManager`
- `app/business/source/collect_job.py`: `SourceCollectJobManager`
- `app/schemas/source/`: source / collect-job / source-type 模型
- `app/business/info_base/main.py`: public persistence entry

## 术语边界

- `source type`: 注册到 `sources_types` 的 source 类标识，当前通常长得像 import path
- `source instance`: `sources` 表中的一条配置记录
- `collect job`: `sources_collect_jobs` 中的一次执行记录

不要把这三个词混成一个层级。

## 当前稳定事实

### Registration Boundary

- `SourceBase.__init_subclass__()` 只把子类登记到 `SourceManager` 的内存 registry。
- `SourceManager.sync_source_types()` 在显式 runtime bootstrap 中把已登记类型回写到
  `sources_types`；import 本身不得连接数据库。
- source 注册仍依赖 import；如果模块从未被 import，对应 source type 就不会出现。
- extension 提供 source 时，真正的注册触发点是 extension startup 期间的 import。

### State Ownership

- `SourceModel.config` 是 source instance 的持久化配置。
- `SourceModel.state` 是 source instance 级别的长期游标或状态。
- `SourceCollectJobModel.state` 是单次 collect job 的运行态/错误态。
- 不要把“每次运行的进度”塞进 `SourceModel.state`，也不要把“长期游标”塞进 job state。

### Collection and Persistence Boundary

- source 可以采集原始数据，也可以组织出 `SubGraphForm`。
- 但 block / relation 的递归插入与去重规则不在 source 层定义，仍由 info-base 协调。
- 如果 source 想落库，应该通过 info-base 的公开入口，而不是自己复制持久化流程。

### Scheduling Hazard

- 当前代码同时存在两条调度路径：
  - `SourceManager.set_up_collect_jobs()` 直接把 `source.collect` 挂到 scheduler
  - `SourceCollectJobManager.check()` 会寻找 `PENDING` jobs 并调度 `run()`
- `main.py` 里还留着 “应该改成 collect job” 的 TODO，所以这里不是已经收敛完的架构。
- 因此，调度相关文档只能写“当前现状”，不要把未来想要的 job-only 模型写成既成事实。

## 编辑指引

- 新增 source 类型时，先保证 import 路径会在 runtime 被加载，否则注册表不会出现。
- 改 source state 结构时，同时检查调用点到底读的是 `SourceModel.state` 还是 `SourceCollectJobModel.state`。
- 若改动跨到 extension startup、info-base persistence、sink ownership，请同步核对 unit-tdd；不要只在本地 guide 里补一句话了事。
