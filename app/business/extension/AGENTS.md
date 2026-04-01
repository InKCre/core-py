# extension/ Local Guide

本文件只描述 `app/business/extension/` 的局部事实与编辑边界。全局执行协议看仓库根 [AGENTS.md](../../../AGENTS.md)。

## 何时阅读

在以下情况进入本目录前先读这里：

- 修改 `ExtensionManager` 或 `ExtensionBase`
- 修改 extension 安装、同步、启停、配置持久化逻辑
- 修改 extension metadata 读取规则

如果改动会影响跨模块契约，再读 [docs/20-product-tdd/extension-runtime.md](../../../docs/20-product-tdd/extension-runtime.md)。

## 局部执行规则

- 模糊的插件市场、分发方式、安装来源、运行模型重构，先放进 `tasks/`，不要直接改 durable docs 或代码。
- 变更 discovery, sync, enable/disable, start/close 语义前，先核对 `app/business/extension/main.py`、`app/schemas/extension/main.py`、`run.py`，并同步更新 Product TDD。
- 本地 AGENTS 只保留仍能被代码证明的事实。不要把历史设计意图当现状写进来。

## 关键文件

- `app/business/extension/main.py`: extension runtime, install, sync, lifecycle
- `app/schemas/extension/main.py`: persisted extension state
- `app/routes/extension.py`: external API surface
- `extensions/`: local extension packages
- `extensions/AGENTS.md`: extension package layout and authoring guidance

## 当前稳定事实

### Extension identity and enablement

- 一个 extension ID 在一个 deployment 中只对应一个安装记录。
- 是否运行是按 client 控制的，状态存放在 `ExtensionModel.enabled` UUID 数组中。
- installed 不等于 enabled，也不等于 running。

### Lifecycle

- `ExtensionBase.on_start()` 会加载配置、回写 `config_schema`、注册 API router、初始化 source 和 resolver。
- `ExtensionBase.on_close()` 会把运行时配置保存回数据库。
- `ExtensionManager.start_enabled()` 只启动当前 client 已启用的扩展。

### Metadata sources

当前实现通过以下来源读取 extension metadata：

- `extensions/<extid>/pyproject.toml`
- `extensions/<extid>/*.dist-info/metadata.json`

这里读取的核心字段是 `nickname` 和 `version`。

### Install and sync behavior

- `install(extid, version)` 当前实现按 extension ID 从 PyPI 下载 wheel，再解包到本地 `extensions/<extid>/`。
- `download()` 会把 wheel 中的源码目录和 `.dist-info` 结构整理成仓库期望的扩展目录布局。
- `sync()` 是双向同步：
  - 本地有、数据库无：插入记录
  - 本地有、数据库有：更新 `nickname` 和 `version`
  - 数据库有、本地无：尝试按数据库记录重新下载

不要把“可从任意 URL 安装”写回文档，除非代码先支持。

## 编辑指引

- 改 metadata 结构或安装布局时，同时更新这里和 [extensions/AGENTS.md](../../../extensions/AGENTS.md)。
- 改 lifecycle 或 enablement 语义时，同时更新 [extension-runtime.md](../../../docs/20-product-tdd/extension-runtime.md)。
- 若新增行为只是局部实现细节，优先写测试或代码注释，不要扩大本文件。

## 创建新 Extension 时要满足的最小形状

```python
from app.business.extension import ExtensionBase


class Extension(ExtensionBase, ext_id="my_ext", config_cls=MyConfig):
  @classmethod
  def _register_apis(cls, router):
    ...

  @classmethod
  def _init_sources(cls):
    from .source import MySource

  @classmethod
  def _init_resolvers(cls):
    from .resolver import MyResolver
```

扩展包本身的目录结构和作者视角约束，以 [extensions/AGENTS.md](../../../extensions/AGENTS.md) 为准。
