# extension/ Local Guide

本目录实现唯一的 Core Extension Host。修改前同时核对 `main.py`、`state.py`、
`release.py`、`distribution.py`、`app/schemas/extension/main.py` 与 `run.py`。

## 稳定边界

- 一个 canonical `extensions` row 表示 deployment 安装的 exact Release；`installed`、
  `enabled[]`、`running` 不可混用。
- `ExtensionBase` 保持配置校验、`on_start`、`on_close` 与可逆 route/source/resolver publication。
- Extension wheel 直接 import Core 模块；Host 只接受标准 `inkcre.core.extensions` entry point。
- Registry Simple URL 必须与配置的 Registry 同源且路径精确匹配 Project。
- runtime 只能把普通 wheel 安装到当前 Core interpreter/site-packages；禁止 `pip --target`、
  per-Extension overlay、`sys.path` 或 `extensions.__path__` 改写。
- Core image 持有受支持的 dependency baseline。dependency preflight 只以下载的 Extension
  wheel 为候选源；缺依赖或版本不满足时拒绝该候选，不访问 dependency index，也不变更
  Core-owned Distribution。
- 任意 peer enabled 时拒绝 version change/rollback。已 import 的 Project 被替换后必须重启，
  当前进程不可热加载新 class。
- 新 install/upgrade 只接受 published；已安装 exact yanked Release 可 enable/cold restore 并告警。
- enable 先启动 runtime，再调用 atomic enabled RPC；返回 version 不一致时移除 peer 并停止旧 runtime。
- disable 先停止 runtime，再调用 RPC；RPC 失败时重启 exact prior runtime，durable intent 不变。
- cold restore 失败不得删除 `enabled[]`；bootstrap/readiness 明确报告 durable intent 尚未运行。
- `ExtensionBase` 向 Extension 提供 fresh validated config 读写与 typed deployment-wide state
  mutation；Extension 不接触 SQLModel，数据库行锁与并发语义仍由 Core store 实现。
- Extension-specific setup 通过 running Extension 发布的 typed Peer inbound 实现；Host 不提供
  generic setup/wizard protocol。公开 OAuth callback 必须是 lifecycle-bound exact route claim。
- Registry origin 每次 operation 按 executing Peer override、deployment config、process fallback
  解析一次，并由 exact Release 与 Distribution consumer 共用该 snapshot。

## 权限和持久化

`state.py` 是唯一 DB adapter。`extensions.state` 是 deployment-wide Extension-produced state；
`enabled[]` 只能通过
`inkcre.set_extension_peer_enabled(p_name text,p_peer_id uuid,p_enabled boolean)` 变更，禁止
read-modify-write。SQLModel 不应泄露成 Host 的稳定接口。

Extension authoring 与 wheel metadata 规则见 `extensions/AGENTS.md`。
