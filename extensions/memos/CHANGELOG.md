# Changelog

This changelog records notable changes to this first-party Python Distribution
association. New entries are rendered from project-local fragments by [Towncrier](https://towncrier.readthedocs.io/).

<!-- towncrier release notes start -->

## 0.3.0 - 2026-09-21

### Added

- 通过 Memos 自有的 Peer 能力提供客户端连接地址，使用 Core 公共 HTTP 地址入口。
  鉴权读取当前已保存配置，使其他 Peer 正常修改或撤销 PAT 后的后续请求无需重启即可生效。


## 0.2.0 - 2026-09-19

### Removed

- 采用 Core Host 0.2 异步数据库合同，结束对旧同步 Host 窗口的兼容；发布为新的不可变 Extension 版本。 (#105)


## 0.1.1 - 2026-08-17

### Fixed

- Made the Memos Python Distribution reproducibly buildable and publishable.
