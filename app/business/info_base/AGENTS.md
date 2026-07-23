# info_base/ Local Guide

本文件只描述 `app/business/info_base/` 的局部事实、术语和编辑边界。全局执行协议看仓库根 [AGENTS.md](../../../AGENTS.md)。

## 何时阅读

在以下情况进入本目录前先读这里：

- 修改 `InfoBaseManager`、`BlockManager`、`RelationManager`
- 修改 block / relation 持久化与去重语义
- 修改 resolver 与 storage 的职责分界
- 修改 ingestion 过程中 embedding 更新的责任边界

如果改动会影响跨模块契约，先读 [docs/_shared/20-product-tdd/](../../../docs/_shared/20-product-tdd/)；本仓库的 ingestion mechanics 以本文件为准。

## 局部执行规则

- 先区分 product/shared truth 与本地实现细节。`fetchsert`、resolver 调用顺序、storage 取数路径都先视为本地事实。
- 本地 AGENTS 只保留仍能被代码证明的事实。不要把将来想要的 ingestion 架构写成现状。
- 若改动会改变 block / relation 去重、subgraph 插入顺序、resolver-storage 分工，先核对 `main.py`、`block.py`、`relation.py`、`resolver/main.py`、`storage/main.py`。

## 关键文件

- `app/business/info_base/main.py`: `InfoBaseManager`，负责递归插入子图和 arc
- `app/business/info_base/block.py`: `BlockManager`，负责 block create / fetchsert / resolver 协调
- `app/business/info_base/relation.py`: `RelationManager`，负责 relation create / fetchsert
- `app/business/info_base/resolver/main.py`: resolver registry 与 raw/solved content 入口
- `app/business/info_base/storage/main.py`: storage registry 与 built-in storage setup
- `app/business/sink/embedding.py`: block embedding upsert/query，属于 sink 责任
- `app/schemas/info_base/`: block / relation / subgraph 表单与模型

## 术语与命名

### Domain vs Python Names

- `info-base`: 产品/领域概念
- `info_base`: Python package 与模块路径

不要把这两个层级混用。

### Content Terms

- `block content`: `BlockModel.content` 上持久化的字符串字段
- `raw content`: resolver 真正取到的原始内容；若 `block.storage is None`，通常直接来自 `block.content`
- `solved content`: resolver 解释后的内容表示，用于下游使用场景

### Graph Terms

- `block`: 一条持久化信息单元记录
- `relation`: 连接两个 block 的有向边
- `subgraph`: 一个 block 加上它的入边/出边表单结构，用于递归插入

## 当前稳定事实

### Persistence Ownership

- `InfoBaseManager` 负责递归把 `SubGraphForm` 展开进 session。
- sources / extensions 可以提出 graph form，但持久化写入由 info-base 协调。
- block 先经 `BlockManager.fetchsert()` 落地，relation 再经 `RelationManager.fetchsert()` 定形。
- relation identity 目前按 `from_ + to_ + content` 判定。

### Block Dedup And Resolver Coupling

- block 是否已存在，交给该 block 的 resolver 通过 `resolver.get_existing(...)` 判定。
- 当前默认行为不是 route 层去重，也不是 `InfoBaseManager` 自己决定去重规则。
- 若要改变 block identity，优先检查 resolver contract，而不是在调用方加特殊分支。

### Resolver vs Storage Boundary

- resolver 负责解释 block。
- storage 负责在 `block.storage` 存在时取回原始内容。
- block 可以直接携带 inline content，也可以只持有 storage pointer。
- 不要在 resolver 里硬编码 storage 实现细节，除非该 resolver 的代码锚点已经明确要求这样做。

### Embedding Ownership

- block 创建后触发 embedding upsert，但 embedding 仍属于 sink 责任，不属于 info-base 自身责任。
- `BlockManager.fetchsert()` 触发 embedding 更新，不等于 info-base 成为 embedding 的权威 owner。

## 编辑指引

- 若改动只影响某个 resolver 的局部行为，优先写到对应子目录 guide 或代码注释，不要把整个 `info_base/` guide 拉宽。
- 若新增 shared contract，先把本地 manager / resolver 细节从 shared 表述里剥离，再去 `InKCre/docs` 写抽象后的版本。
- 本文件已经是本地 ingestion mechanics 的主要承接点；不要再把相同内容回写成新的 mixed Product TDD。
