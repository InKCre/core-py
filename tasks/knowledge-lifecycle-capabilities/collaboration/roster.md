# Parallel Peer Roster

> Shared task control maintained by peer sessions。A row declares work placement，not implementation authorization or role
> hierarchy。

| Unit | Session | Branch / worktree | Base | Phase | Decision range | Declared overlap / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| `mcp-sink` | `01a04610-338e-7311-93df-847f9801c5af` | merged through PR #88；the current root worktree retains only local task-control state | protected `main` merge `459a6df` | Closed | D-381–D-420 | No active implementation ownership；MCP runtime、ChatGPT Tool acceptance and production delivery are complete |
| `telegram-extension` | `01a04685-aa31-7682-a4a2-824727eacce5` | core-py PR #89 / `.github` PR #28 | merged as core-py `42d8527` and `.github` `f7269b9` | Closed / merged | D-421–D-460 | Telegram、repository-wide Changie→Towncrier cutover and organization guidance are complete；Unit worktrees are retired and Release PR #90 is independently owned by the release lifecycle |
| `organization-nowledge-study` | current session | PR #100 / #101 merged；root worktree on main retains local task-control records | protected `main` `b3ccb00` | Closed / production delivered | D-461–D-570 | Core 0.2.0、production probes and stable admission complete；no active implementation ownership |
| `cli-sink` | 当前 CLI session | `feat/inkcre-cli` / root core-py worktree | `b3ccb00`，已核对 origin/main | 完整 Preflight 已完成，等待 Impact Handshake 后实施 | D-571–D-610 | cli/ 独立 PDM 项目；Core REST/Job/校验边界，Mail 取消清理，client-web worker 配套；ext-reg runtime 和 Core pin。预演发现的 production wheel finalize 缺口纳入 P5。跨仓库 feature 工作位置在实施时建立；当前没有业务源码改动 |

## Shared-worktree coordination

MCP、Telegram 和 Organization 均已关闭；root worktree 保留 parent 生命周期内的本地 task-control 记录，
现已切到 CLI feature branch，没有本轮待交付的源码。CLI 保留上一单元的本地收尾和未跟踪 skill，不将其视为
本 unit 的修改。没有其他已登记的 active unit，也不进行 cross-session 通信。Historical task-control and operational state can still intersect：

- `mcp-sink` has no remaining implementation ownership。Its Core、Extension Runtime and production changes are authoritative
  on protected `main` at `459a6df`；the root worktree's remaining dirty state is task control，not unmerged MCP source。
- `telegram-extension` 和 `organization-nowledge-study` 的源码责任已交付到 main。历史清单说明改动来源，不代表
  这些关闭的 session 继续占有 `pyproject.toml`、Agent runtime、Resolver、Job 或其它源码。后续 unit 按当前真实压力
  重新登记范围并遵守 durable owner；不需要向已关闭 session 申请修改许可。
- `docs/openapi.json` is a possible generated-output intersection。Whichever Unit regenerates it must compare against the
  other Unit's live routes and preserve the complete current application contract；it is committed only with the Unit whose
  API change requires regeneration。
- Parent packet、roster 与 decision index 是共享 task-control。各 session 只写自己的保留区段，并作必要的导航/状态
  更新；已保留的历史区段及其空号不回收给新 unit。
- The local environment、development database and repository-wide verification commands are shared operational state。
  Concurrent runs must not be interpreted as isolated evidence。When a reset or reconfiguration may affect another active
  Unit，pause and obtain Sir's direction before changing that shared state。
- Commits remain path-scoped by Unit despite the shared dirty baseline；neither Unit may use broad staging or cleanup that
  captures、restores or discards the other's work。
- 新 worktree 只继承提交，不继承 root 的本地收尾记录。切换前核对 parent packet 与实际工作树；需要转交时只带
  必要 task-control，不把未跟踪的 `.agents/skills/python-backend-code/` 或本机配置混进交付。

## Adding a Peer Unit

Before writing decisions or implementation，the new peer records its own row with：

- exact Unit objective and non-goals；
- thread/session、branch、worktree and base commit；
- current phase and relevant accepted decisions；
- reserved decision range；
- expected repositories、schema/migration/shared-runtime surfaces；
- dependencies on active or unmerged work。

The session checks that its range/surfaces do not collide，then uses the [bootstrap](session-bootstrap.md) and returns its
restored model before beginning design。On collision，it pauses the intersecting work and reports the concrete conflict to Sir；
sessions do not coordinate directly。
