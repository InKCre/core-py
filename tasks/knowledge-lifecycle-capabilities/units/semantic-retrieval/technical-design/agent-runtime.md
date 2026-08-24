# Agent Definition、Thread And Runtime

> [Technical design index](index.md)

AgentManager owns FastAPI-like typed Tool input validation。The decorator derives the LLM-visible JSON schema from the
handler's Pydantic input annotation and runtime parses call arguments before invoking the function。Invalid input becomes a
tool-result message by serializing Pydantic's own `ValidationError`，with only a thin transport wrapper if necessary；do not
invent another error schema。Tool return annotations are enforced by static checking only。AgentManager does not perform
runtime output validation or publish an output schema；serialization failure is an implementation failure。

## T-019 Agent Definition、Thread And Runtime Tool Binding（approved through D-172）

```text
persisted Agent definition
  id + name + system_prompt + tools + nullable tool_choice
  model + max_model_calls_per_turn
                |
                | AgentManager.run(agent_id, initial_message)
                v
SystemMessage(agent.system_prompt)
                |
                v
Thread.from_agent_definition(definition, messages=[SystemMessage])
  snapshots model + tools + tool_choice + max_model_calls_per_turn
  stores canonical Messages through thread persistence backend
                |
                v
start_turn(input) -> asyncio.Task[TurnTermination]
  appends UserMessage and runs model/tool loop

peer-local AgentManager tool registry
  exact tool ID -> code-owned input-contract binder + handler
```

### Agent creation and per-turn bound

Agent definition owns required positive `max_model_calls_per_turn`。Each `start_turn()` resets that budget，and every
attempted `AIManager.chat()` consumes one unit；ToolCalls、tool executions and Messages do not。An AssistantMessage without
ToolCalls ends the turn naturally even when it has no text。When AssistantMessage has ToolCalls，execute that complete batch
and make another model call only when budget remains。

`AgentManager.run(agent_id, initial_message)` loads one AgentDefinitionModel，materializes
`SystemMessage(agent.system_prompt)` before entering Thread，constructs Thread from the complete definition model and starts
the first turn。It returns the active Thread immediately rather than awaiting that turn。

Per-turn outcome is owned by the Task：

```text
asyncio.Task[TurnTermination]
  completed | max_model_calls
  cancelled Task = caller abort
```

`completed` means an AssistantMessage returned without ToolCalls。When another model call would exceed the budget，return
`max_model_calls` without an exception or cleanup call。Preserve completed Tool side effects；do not retry、roll back or
compensate。A cancelled Task represents abort。Thread is the history/result handle；there is no AgentRunResult or persisted
Turn entity。

One model turn may emit multiple ToolCalls。They form an order-independent execution batch correlated by call ID；their
presentation order is not an execution dependency。The Turn schedules one child Task per call and executes them
concurrently。Each call converts ordinary validation/handler failure into its own result，so siblings continue；Turn
cancellation propagates to unfinished calls。Do not `shield()`、retry or roll back the batch or its successful effects。
There is no redundant batch-level child Task：the Turn Task already owns the structured-concurrency scope and directly
awaits the complete batch。

After the execution barrier，construct exactly one `ToolResultMessage(results=[...])`。Its nested ToolResult call IDs are
unique and exactly cover the preceding AssistantMessage's ToolCalls；array order has no meaning。Tool execution never
writes history。The Turn runtime is the sole writer and asks the thread persistence backend to atomically append the
AssistantMessage + ToolResultMessage closed pair before any next model call。Abort before that commit persists neither
half；completed Tool side effects remain。ToolCalls stay nested in AssistantMessage and ToolResults stay nested in
ToolResultMessage，so neither becomes an independent persisted history entity。Dialect adapters own provider-specific
splitting/grouping。

ToolResult has no common error DTO beyond `is_error` and JSON `content`。Pydantic argument failure uses ValidationError's
native JSON value。A handler may raise thin `ToolExecutionError(content)` for Tool-owned actionable failure content。An
unexpected ordinary Exception becomes stable generic error content while its complete exception/traceback is logged；never
make provider-facing behavior depend on database/framework error strings。Successful content is the handler return value's
JSON serialization。All three failure paths remain per-call and do not stop the rest of the batch。

Thread snapshots nullable protocol-level `tool_choice` from AgentDefinitionModel and offers no per-turn override。`null`
means unspecified and causes the dialect to omit the provider control；a non-null unsupported value fails before the
provider request。The rumination system prompt owns the product instruction：use schema discovery/drafting only to construct
a potentially useful interpretation，call `submit_graph` only when that result is meaningful，and otherwise end honestly
without a graph write。No ToolCall remains a valid no-op and natural completion，not an error；discovery/draft calls followed
by no submit also leave the info-base unchanged。

When AssistantMessage has ToolCalls，execute the complete batch；text presence is irrelevant to that condition。Append the
complete ToolResultMessage first。Only after it is ready may a UserMessage be appended for an actual new-user-input need；
the ordinary loop inserts no synthetic UserMessage before its next model call。

Agent definition remains system-prompt authority。AgentManager.run converts it to the first SystemMessage before Thread
construction；Thread does not retain another system_prompt field。Rumination-owned focal/context data enters only through
the UserMessage passed to `start_turn()`，and AIManager has no separate prompt parameter。

- Agent definitions are reusable database facts。The exact persisted `agents` fields are database-generated bigint `id`、
  required descriptive `name`、required `system_prompt`、`tools: text[]`、nullable `tool_choice`、required `model`、required
  positive `max_model_calls_per_turn` and database-owned timestamps。Do not add enabled、description or generic config。
- `AgentManager.run()` takes only `agent_id` and one `initial_message: UserMessage`。Thread is an internal Agent module，so its constructor accepts
  the complete AgentDefinitionModel and owns the snapshot projection；external callers do not pass flattened model/tool/
  policy parameters。
- Thread snapshots model、tools、tool_choice and max_model_calls_per_turn。System prompt is not a snapshot field because run
  has already materialized it into the initial SystemMessage。
- The **thread persistence backend** is replaceable and owns whole Thread state。MVP provides only an in-memory
  implementation；do not add database Thread/Message persistence now。
- Thread exposes runtime-only `current_turn`。`start_turn(input)` schedules the whole turn coroutine as one asyncio Task，
  appends the UserMessage and returns the Task。Run starts the first Task and returns Thread immediately。One Thread rejects a
  second active turn until `current_turn.done()`。
- Before appending a new UserMessage，`start_turn()` may remove exactly one trailing AssistantMessage whose ToolCalls have
  no following ToolResultMessage。This is defensive persistence recovery，not normal loop state。Never erase only the
  ToolCalls or rewrite an older ambiguous history segment。
- Thread history supports atomic multi-Message append。AssistantMessage + ToolResultMessage is the minimum closed Tool
  interaction commit；individual Tool execution tasks return values and never become history writers。
- Tool IDs have set semantics。Persistence order is non-authoritative and duplicates are rejected。
- Canonically sort tool IDs before persistence so semantically identical sets do not create false row updates。
- Agent behavior includes prompt、tools、tool_choice、model and per-turn model-call budget。Existing Threads do not reread
  later Agent-definition changes。
- Schema and handler form one runtime Agent Tool contract。The callable remains code-owned；the persisted definition only
  references its exact ID。
- Most Tool binders simply derive one static input model/schema from the decorated handler annotation。A bounded Tool may
  instead materialize a code-owned Pydantic input contract from current domain-manager facts when the schema itself is a
  runtime projection。D-172's exact available Resolver-ID enum is the first pressure；this is not permission for arbitrary
  prompt-time schema mutation or a universal reflection registry。
- `AgentManager.run()` resolves the persisted Tool IDs and freezes their bound contracts for the new Thread。Later registry
  or extension changes do not rewrite that Thread's Tool schemas；a now-unavailable handler execution fails as an ordinary
  Tool call rather than silently selecting another Resolver。
- AgentManager owns a decorator for function-based Agent Tool registration。Other registry-owning Managers should converge
  on the same visible decorator pattern without creating a global Registry service or erasing their domain-specific rules。
- A future persistent **thread persistence backend** stores the AI-module-owned canonical Message union as part of Thread
  state，including nested tool calls/results；it does not create independent ToolCall、ToolResult or Turn persistence
  entities。
- No checkpoint/resume model is introduced or reserved。AgentManager offers no exactly-once promise；a handler owns any
  tool-specific idempotency/exactly-once mechanism。
- A run uses the loaded definition snapshot。A missing runtime binding for one persisted exact tool ID ends the run with one
  high-level Agent failure；there is no readiness、fallback or hidden tool substitution。
