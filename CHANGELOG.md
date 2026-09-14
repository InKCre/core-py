# Changelog

Core release notes start from the current `0.1.1` baseline. Earlier repository history remains available in Git.

<!-- towncrier release notes start -->

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
