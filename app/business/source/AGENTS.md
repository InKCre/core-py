## source/ - Data Sources (数据输入)

数据采集模块，负责从外部数据源自动收集信息并存入 info-base。

### 核心概念

- **Source**: 数据源实例（RSS 订阅、邮箱、GitHub stars 等）
- **SourceBase**: Source 插件基类，定义 `collect()` 方法
- **SourceCollectJob**: 采集任务，包含配置、状态、调度信息
- **Collect → Organize**: 采集后自动组织成 Block + Relation 结构

### 模块结构

```
source/
├── main.py              # SourceManager - Source 类型注册和管理
├── collect_job.py       # SourceCollectJobManager - 采集任务调度
└── webpage.py           # 网页内容采集工具函数
```

### 核心流程

**Source 注册** (通过 Extension):
1. Extension 定义 Source 类，继承 `SourceBase`
2. 使用 `__init_subclass__` 自动注册到 `SourceManager`
3. 配置 schema 通过 `config_cls` 类型参数指定

**采集调度** (自动周期执行):
1. `SourceManager.set_up_collect_jobs()` 为每个 Source 创建采集任务
2. Scheduler 每 30s 调用 `SourceCollectJobManager.check()`
3. 发现 PENDING 任务 → 调度执行 `SourceBase.collect()`
4. 采集完成 → 调用 `organize()` 存入 info-base

**生命周期状态**:
- `PENDING`: 待执行
- `RUNNING`: 执行中
- `FINISHED`: 执行成功
- `FAILED`: 执行失败（错误存于 `state` 字段）

### 数据模型

见 [app/schemas/source/](../../schemas/source/) 目录：
- `SourceModel` - Source 表模型
- `SourceCollectJobModel` - 采集任务表模型
- `SourceTypesModel` - Source 类型注册信息（内存）

### 编码指引

**新增 Source 类型**（在 Extension 中）:
```python
class MySource(SourceBase, config_cls=MySourceConfig):
    async def collect(self, job: SourceCollectJobModel) -> None:
        # 1. 采集数据
        # 2. 创建 Block 和 Relation
        # 3. 通过 InfoBaseManager.insert_subgraph() 存储
        pass
    
    async def _organize(self, block_id: BlockID) -> None:
        # 组织 Block 的关系（可选）
        pass
```

- Job 状态通过 `job.state` 字段持久化（JSON）
- 异常会自动捕获并标记为 FAILED
- 使用 `webpage.py` 提供的工具函数采集网页内容
