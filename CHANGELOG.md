# Changelog

Core release notes start from the current `0.1.1` baseline. Earlier repository history remains available in Git.

<!-- towncrier release notes start -->

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
