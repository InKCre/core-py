# Parallel Peer Roster

> Shared task control maintained by peer sessions。A row declares work placement，not implementation authorization or role
> hierarchy。

| Unit | Session | Branch / worktree | Base | Phase | Decision range | Declared overlap / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| `mcp-sink` | `01a04610-338e-7311-93df-847f9801c5af` | merged through PR #88；the current root worktree retains only local task-control state | protected `main` merge `459a6df` | Closed | D-381–D-420 | No active implementation ownership；MCP runtime、ChatGPT Tool acceptance and production delivery are complete |
| `telegram-extension` | `01a04685-aa31-7682-a4a2-824727eacce5` | core-py PR #89 / `.github` PR #28 | merged as core-py `42d8527` and `.github` `f7269b9` | Closed / merged | D-421–D-460 | Telegram、repository-wide Changie→Towncrier cutover and organization guidance are complete；Unit worktrees are retired and Release PR #90 is independently owned by the release lifecycle |

## Shared-worktree coordination

The Human permitted the two Units to share the root core-py worktree during preflight。MCP is now closed and Telegram has an
independent implementation worktree；task-control and operational state can still intersect：

- `mcp-sink` has no remaining implementation ownership。Its Core、Extension Runtime and production changes are authoritative
  on protected `main` at `459a6df`；the root worktree's remaining dirty state is task control，not unmerged MCP source。
- `telegram-extension` owns its Unit packet and future `extensions/telegram/**` implementation。Its scope now also owns the
  repository-wide Changie→Towncrier cutover: root PDM dependency/lock state, release fragments and changelogs, release-contract
  orchestration scripts and their CI/documentation consumers。It still does not own Core Source/Resolver/Extension framework。
- The former root `pyproject.toml` / `pdm.lock` overlap is resolved by PR #88's merge。Telegram's independent implementation
  must use protected `main` `459a6df` or a later integrated main commit as its address-sensitive baseline。
- `docs/openapi.json` is a possible generated-output intersection。Whichever Unit regenerates it must compare against the
  other Unit's live routes and preserve the complete current application contract；it is committed only with the Unit whose
  API change requires regeneration。
- Parent packet state、`collaboration/roster.md` and the decision index are shared peer integration surfaces。Telegram records
  decisions only in D-421–D-460 and may apply the narrow navigation/state changes implied by those decisions，while preserving
  other peers' rows、ranges and current work。
- The local environment、development database and repository-wide verification commands are shared operational state。
  Concurrent runs must not be interpreted as isolated evidence。When a reset or reconfiguration may affect another active
  Unit，pause and obtain Sir's direction before changing that shared state。
- Commits remain path-scoped by Unit despite the shared dirty baseline；neither Unit may use broad staging or cleanup that
  captures、restores or discards the other's work。

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
