# Business Pipeline And Authority

## Purpose

本文件记录 `core-py` 内部一条慢变量结构：

`extension -> source/resolver -> info_base -> sink`

它不是局部目录 hazard，而是跨多个 business subtree 的 unit-local architecture。

## 何时阅读

在以下情况先读这里：

- 修改 `app/business/extension/`
- 修改 `app/business/source/`
- 修改 `app/business/info_base/`
- 修改 `app/business/sink/`
- 修改这些子树之间的 ownership / dependency / authority

## Structure

### 1. Extension Is The Runtime Expansion Entry

- extension 是 runtime 扩展入口。
- extension startup 会注册 API、初始化 source、初始化 resolver。
- extension 自己不拥有 core graph persistence，也不拥有 sink retrieval semantics。

### 2. Source And Resolver Extend The System Surface

- source 负责从外部世界采集或记录输入。
- resolver 负责把 block 解释成系统可消费的内容表示。
- 它们都通过 import-time registry 接入系统。
- extension 是 source / resolver 的常见装载入口，但 source / resolver 本身不是 persistence owner。

### 3. Info-Base Owns Graph Persistence

- `InfoBaseManager` 是 block / relation / subgraph 持久化协调者。
- producer 可以提出 `SubGraphForm`，但 recursive insert / block fetchsert / relation fetchsert 由 info-base 协调。
- resolver / storage 是 info-base 可依赖的解释与取数子系统，不反过来拥有 graph persistence。

### 4. Sink Owns Retrieval And Embedding Semantics

- sink 负责 retrieval、rerank、RAG 输出，以及 embedding lifecycle。
- info-base 当前可以在 block 写入时触发 embedding upsert。
- 但 “谁拥有 embedding” 这个问题，答案仍然是 sink，不是 info-base。

## Cross-Subtree Constraints

### Allowed Direction

当前允许的结构性方向可以理解为：

- extension 扩展 source / resolver
- source 把采集结果交给 info-base persistence
- info-base 通过 resolver / storage 解释内容
- sink 从 info-base / resolver 路径消费内容并维护 retrieval view

### Important Asymmetry

- `info_base/block.py` 调用 `sink/embedding.py` 做 upsert，是当前允许的结构性耦合。
- 这不表示 sink 可以反过来接管 persistence，也不表示 info-base 成为 embedding owner。
- 若要重构这条耦合，必须把它当成 unit-level architecture change，而不是某个目录的局部重排。

## Non-Goals

本文件不承接以下内容：

- source 调度实现细节
- resolver 的局部 raw/solved content 技巧
- storage 的 built-in ID 约定
- sink 某个 retrieve mode 的算法细节
- deployment / scheduler / runtime topology

这些要么属于 local `AGENTS.md`，要么属于 `docs/40-deployment/`。
