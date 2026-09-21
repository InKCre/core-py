# Changelog

This changelog records notable changes to this first-party Python Distribution
association. New entries are rendered from project-local fragments by [Towncrier](https://towncrier.readthedocs.io/).

<!-- towncrier release notes start -->

## 0.2.1 - 2026-09-21

### Changed

- 声明兼容 Core Host SDK 0.3，保留 SDK 0.2 支持；不改变插件功能。


## 0.2.0 - 2026-09-19

### Removed

- 采用 Core Host 0.2 异步数据库合同，结束对旧同步 Host 窗口的兼容；发布为新的不可变 Extension 版本。 (#105)


## 0.1.1 - 2026-09-14

### Fixed

- 在采集路径复用已恢复的 typed config，避免重复转换和校验。


## 0.1.0 - 2026-08-17

### Changed

- Recorded the existing published Python Distribution as the Changie baseline.
