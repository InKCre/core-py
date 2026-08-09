# extension/ Local Guide

本文件只描述 `app/business/extension/` 的局部事实与编辑边界。全局执行协议看仓库根 [AGENTS.md](../../../AGENTS.md)。

## 何时阅读

在以下情况进入本目录前先读这里：

- 修改 `ExtensionManager` 或 `ExtensionBase`
- 修改 extension 安装、同步、启停、配置持久化逻辑
- 修改 extension metadata 读取规则

如果改动会影响跨模块契约，先读 [docs/_shared/20-product-tdd/](../../../docs/_shared/20-product-tdd/)；本仓库的 runtime mechanics 以本文件为准。

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

- legacy extension ID 在一个 deployment 中只对应一个 `ExtensionModel` 记录。
- legacy 是否运行按 client 控制，状态仍存放在 `ExtensionModel.enabled` UUID 数组中。
- Registry 路径独立使用 namespaced `namespace/name` installation 和 exact peer binding；
  不迁移或重解释 legacy row。
- installed 不等于 enabled，也不等于 running。
- legacy runtime class 从 checked-in `extensions.<ext_id>` 加载。
- Registry runtime class 只能从 build-admitted `bundle.zip` 的 canonical
  `extensions.<ext_id>` 加载；Registry metadata 不能提供 Python import path。
- `extension config` 指持久化在 extension record 上的配置 payload，不等于运行中的 Python 对象状态。

### Lifecycle

- `ExtensionBase.on_start()` 会加载配置、回写 `config_schema`、注册 API router、初始化 source 和 resolver。
- `ExtensionBase.on_close()` 会把运行时配置保存回数据库。
- startup 会产生显式 publication handle；成功 close 后撤销动态 routes、source、resolver
  并清空 OpenAPI cache。close 失败不撤销 durable enablement，允许重试。
- `ExtensionManager.start_enabled()` 只启动当前 client 已启用的扩展。
- `RegistryExtensionManager.start_enabled()` 只恢复当前 peer 的 persisted exact binding，
  不访问 Registry；新 enable 才执行 Registry match 和本地 admission。
- start / close 不只是布尔状态切换；它们会修改当前 runtime 的 router、source、resolver 与配置状态。

### Registry admission boundary

- install 只验证并保存一个 exact published version，不创建 peer binding。
- 新 enable 使用 Runtime/API platform matcher 选择稳定 target；随后必须由本地 catalog
  精确匹配 coordinate/version/key/digest。
- catalog 的 manifest digest、bundle descriptor size/SHA-256、ZIP shape 和所有加载模块的
  zipimport origin 都必须通过验证，才能执行。
- runtime start 成功后才插 binding；disable 必须先 close/unpublish/unload，再删除当前 peer binding。
- 只要任意 peer binding 存在就不能改变共享 version；只要任意 binding 或本地 active runtime
  存在就不能 uninstall。
- 同一 extension ID 的 legacy runtime 与 Registry runtime 不共存；canonical module 已被 legacy
  runtime 占用时 Registry enable fail closed。

### Metadata sources

当前实现通过以下来源读取 extension metadata：

- `extensions/<extid>/pyproject.toml`
- `extensions/<extid>/*.dist-info/metadata.json`

这里读取的核心字段是 `nickname` 和 `version`。

### Install and sync behavior

- release artifact 使用固定的 checked-in extension profile，代码和依赖都在构建时锁定。
- `install(extid, version)` 只注册制品内已经存在的 `extensions/<extid>/`，不会下载代码。
- `sync()` 是从不可变制品到数据库的单向同步：
  - 本地有、数据库无：插入记录
  - 本地有、数据库有：更新 `nickname` 和 `version`
  - 数据库有、本地无：记录警告并忽略，不下载、不执行

第三方 extension 分发需要独立的受信构建流程，不能在运行中的 web 进程安装。
`sync()` 始终只维护 legacy `extensions`，绝不创建 Registry installation。

### State transition boundary

- `installed`、`enabled`、`running` 是三个不同层级的状态。
- `enable()` 处理当前 client 的允许运行状态，必要时才引发 runtime start。
- `disable()` 处理当前 client 的允许运行状态移除，并在需要时关闭 runtime。
- 若只想描述共享状态语义，写到 shared Product TDD；若涉及 `install()`、`enable()`、`disable()`、`start_enabled()` 的具体行为，留在这里。

## 编辑指引

- 改 metadata 结构或安装布局时，同时更新这里和 [extensions/AGENTS.md](../../../extensions/AGENTS.md)。
- 改 lifecycle 或 enablement 语义时，先判断 shared contract 是否变化；若是，先改 `InKCre/docs` 再 bump `docs/_shared`，本地 runtime 细节则直接更新这里。
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
