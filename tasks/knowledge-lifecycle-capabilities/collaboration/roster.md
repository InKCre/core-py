# Parallel Unit Roster

> Coordinator-owned task control。A row declares work placement，not implementation authorization。

| Unit | Session | Branch / worktree | Base | Phase | Decision range | Declared overlap / dependency |
| --- | --- | --- | --- | --- | --- | --- |
| `mcp-sink` | `01a04610-338e-7311-93df-847f9801c5af` | planning on `feat/knowledge-lifecycle-task-packet-recovery` / current core-py worktree；dedicated execution branch pending clean coordination baseline | `6524cd5` | Technical | D-381–D-420 | Sink persistence/runtime；Extension type-publication correction first lands in ext-reg runtime，then core-py consumes it |

## Adding a Unit

Before creating a parallel unit session，the coordinator records：

- exact Unit objective and non-goals；
- thread/session、branch、worktree and base commit；
- current phase and relevant accepted decisions；
- reserved decision range；
- expected repositories、schema/migration/shared-runtime surfaces；
- dependencies on active or unmerged work。

The session then uses the [bootstrap](session-bootstrap.md) and returns its restored model before beginning design。
