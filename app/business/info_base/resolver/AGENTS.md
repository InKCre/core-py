# resolver/ Local Guide

本文件只描述 `app/business/info_base/resolver/` 的局部事实与高风险边界。更上层的 ingestion mechanics 看 [app/business/info_base/AGENTS.md](../AGENTS.md)；跨模块结构看 [docs/30-unit-tdd/business-pipeline-and-authority.md](../../../../docs/30-unit-tdd/business-pipeline-and-authority.md)。

## 何时阅读

在以下情况进入本目录前先读这里：

- 修改 `ResolverManager` 或 `Resolver`
- 新增 / 删除 resolver
- 修改 raw-content / solved-content 路径
- 修改 block 去重与 resolver identity 规则

## 局部执行规则

- 不要 override `Resolver.__init__()`；resolver 子类应使用 `__post_init__()` 和 `_get_solved_content()`。
- 不要在 module level import `app.business.info_base.block` / `BlockManager`；这里和 `block.py` 存在循环依赖风险，必要时 lazy import。
- 如果改动会改变 `get_existing()` 的 identity 语义，先把影响面当成 info-base 级别变更处理，不要只在本目录悄悄改掉。

## 关键文件

- `app/business/info_base/resolver/main.py`: `ResolverManager`、`Resolver` 基类
- `app/business/info_base/resolver/text.py`: text resolver
- `app/business/info_base/resolver/image.py`: image resolver
- `app/business/info_base/resolver/html.py`: html resolver
- `app/business/info_base/resolver/video.py`: video resolver

## 当前稳定事实

### Registry Side Effect

- `Resolver.__init_subclass__()` 会把 resolver 注册到 `ResolverManager.RESOLVER_CLS`。
- 所以 resolver 可用性依赖 import-time side effect；模块没被 import，就不会被注册。
- 对 extension resolvers 来说，真正的注册触发点通常在 extension startup 的 `_init_resolvers()`。

### Raw vs Solved Content

- `raw content` 是 resolver 真正取到的原始内容。
- 当 `block.storage is None` 时，raw content 默认直接来自 `block.content`。
- 当 `block.storage` 存在时，resolver 会通过 `StorageManager.get_storage(...).get_raw_content(...)` 取数。
- `solved content` 是 resolver 解释后的内部表示，不等于原始存储内容。

### Identity and Dedup

- 默认 `Resolver.get_existing()` 以 `block.resolver + block.content` 查重。
- 这不是普适真理，而是当前默认实现。
- 一旦改变它，影响的是 block identity / dedup，不只是某个 resolver 的局部行为。

## 局部风险

- 在 resolver 里硬编码 storage 实现细节，通常会把 `resolver` 和 `storage` 的边界污染掉。
- 若 resolver 需要特殊 raw-content 预处理，优先先判断那是不是应该落在 storage 层。
- 若为了图省事在 module level 引入 `BlockManager`，大概率会重新引入循环 import。

## 编辑指引

- 新增 resolver 时，先确认模块 import 路径会在 runtime 被触发，否则注册不会发生。
- 需要缓存初始化结果时，用 `__post_init__()` 和 `set_solved_content()`，不要重写构造路径。
- 若改动只影响单个 resolver 的解释逻辑，尽量留在对应文件或这里；若改动上升到 dedup / ownership contract，再回到 `info_base/` guide 或 unit-tdd。
