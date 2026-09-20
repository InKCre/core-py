# Changelog

Core release notes start from the current `0.1.1` baseline. Earlier repository history remains available in Git.

<!-- towncrier release notes start -->

## 0.5.0 - 2026-09-20

### Added

- Add the asynchronous Agent Query Sink, owner-local Agent read tools, and Sink type discovery.

### Changed

- 生产发布摘要明确区分版本未变的空操作、完整发布与失败／取消，并记录源码版本、提交、候选镜像和 stable 更新结果；数据库边界检查复用 Ruff 的源码范围，避免旧构建产物导致误报。


## 0.4.0 - 2026-09-19

### Changed

- 数据库运行时操作使用原生异步 I/O 与显式 UoW 事务边界，覆盖 Graph、配置、AI/Agent、Peer、Source/Sink、Job/Cron、扩展采集、检索、Organization 和 MCP；批量写入 flat graph 与检索投影，数据库日志独立批量写入，关闭时排空任务后释放连接池。新增全 runtime 数据库边界检查和长期维护指南。 (#105)

### Removed

- Extension Host 数据库操作与配置／状态持久化接口改为异步，Host 合同推进到 0.2；旧同步 Extension wheel 必须先停用并升级至匹配的正式版本。
  删除运行时 SessionLocal、同步 BlockManager／RelationManager、可选 raw session 持久化及旧 Storage 写入接口；组合写入使用必需的 UoW，独立业务入口需要 await。 (#105)


## 0.3.0 - 2026-09-14

### Added

- 提供独立 CLI 使用的普通 REST 管理与检索接口、动态输入 schema 发现、原生二进制与 multipart 内容交付；Job 新增 best-effort 停止请求，显式 rumination 通过 Job 受理。减少已验证配置在内部传递时的重复校验。


## 0.2.0 - 2026-09-12

### Added

- Add extensible semantic Organization behaviors, bounded graph-use queries, and Human-reviewed
  acceptance fixtures, composable Agent read tools and opt-in development traces; also recognize schema-v3 SVC development
  database provider configuration. (#100)


## 0.1.5 - 2026-09-01

### Fixed

- Production delivery no longer waits for pull-request checks to reappear on a protected-main merge commit. (#production-main-verification)


## 0.1.4 - 2026-09-01

### Changed

- Protected-main releases now start directly from the admitted main push instead of rerunning pull-request CI first. (#main-release-orchestration)


## 0.1.3 - 2026-09-01

### Changed

- Release publishing now builds and validates its database schema from the exact protected-main source instead of consuming a CI artifact. (#org-repository-cleanup)


## 0.1.2 - 2026-08-30

### Changed

- Select normal Core production delivery through a prepared Core version instead of every checked main commit.
