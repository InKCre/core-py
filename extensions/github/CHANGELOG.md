# Changelog

This changelog records notable changes to this first-party Python Distribution
association. New entries are rendered from project-local fragments by [Towncrier](https://towncrier.readthedocs.io/).

<!-- towncrier release notes start -->

## 0.3.0 - 2026-09-19

### Added

- 为 GitHub Resolver 增加绑定事务的异步身份查询，继续按 node_id 协调已有 Block，并明确拒绝重复身份。 (#105)

### Removed

- 采用 Core Host 0.2 异步数据库合同，结束对旧同步 Host 窗口的兼容；发布为新的不可变 Extension 版本。 (#105)


## 0.2.0 - 2026-08-24
### Added
* Synchronize the authenticated account's Stars, Lists, memberships, and repository ownership as reusable graph facts.

## 0.1.0 - 2026-08-17

### Changed

- Recorded the existing published Python Distribution as the Changie baseline.
