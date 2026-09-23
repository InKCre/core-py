# Changelog

This changelog records notable changes to this first-party Python Distribution
association. New entries are rendered from project-local fragments by [Towncrier](https://towncrier.readthedocs.io/).

<!-- towncrier release notes start -->

## 0.3.2 - 2026-09-23

### Changed

- The Mail Source configuration schema now marks its password for password-style rendering without changing how it is read or saved.


## 0.3.1 - 2026-09-21

### Changed

- 声明兼容 Core Host SDK 0.3，保留 SDK 0.2 支持；不改变插件功能。


## 0.3.0 - 2026-09-19

### Removed

- 采用 Core Host 0.2 异步数据库合同，结束对旧同步 Host 窗口的兼容；发布为新的不可变 Extension 版本。 (#105)


## 0.2.1 - 2026-09-14

### Fixed

- 取消收集时等待同一次 IMAP 阻塞调用结束后再释放连接，避免取消提前释放锁或并行断连；使用有限的连接和读取超时，保留已恢复的 typed 配置。


## 0.2.0 - 2026-08-26
### Added
* Add the Python Distribution for the 0.2 Extension Release.

## 0.1.0 - 2026-08-17

### Changed

- Recorded the existing published Python Distribution as the Changie baseline.
