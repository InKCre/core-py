## Agent domain

This module owns reusable persisted Agent definitions, exact code-owned Tool bindings, and the canonical Thread/Turn
runtime. It depends on the graph-blind `AIManager` for model calls but must not acquire organization, Resolver, graph, or
transport policy.

- `AgentManager.run(agent_id, initial_message)` loads one definition snapshot, binds every exact Tool ID, creates an
  in-memory-persisted Thread, starts its first Turn, and returns the active Thread without awaiting completion.
- The Thread persistence backend owns whole snapshots. MVP implements only the in-memory backend; do not split Turn,
  ToolCall, ToolResult, or Message into independent persistence entities.
- A Turn is the single history writer. Tool calls execute concurrently and return values only. Persist an Assistant
  ToolCall message together with its complete ToolResult message in one backend append.
- Runtime validates Tool inputs once with the bound Pydantic model. Use Pydantic's validation detail directly. Tool return
  shape is a static type-checking contract, not a second runtime schema.
- Tool registration is decorator-owned. Exact persisted Tool IDs have set semantics and are bound once per new Thread;
  later registry changes do not rewrite existing Thread schemas or handlers.
- Cancellation owns no rollback, retry, shielding, or compensation. Completed Tool effects remain.
