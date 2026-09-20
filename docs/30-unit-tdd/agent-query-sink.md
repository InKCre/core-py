# Agent Query Sink

## Purpose And Topology

`core.agent-query.v1` lets an external caller ask one information need while an Agent composes existing info-base retrieval,
Resolver reads, and graph navigation. It is a Sink projection, not a new retrieval engine.

```text
POST /sinks/{id}/query
  -> core.sink.agent-query.v1 Job
  -> AgentQueryJobHandler
  -> enabled AgentQuerySink
  -> AgentManager.run(config.agent, query)
  -> owner-provided read Tools
  -> submit_query_result
  -> Job.state.result
```

The endpoint returns `202 Accepted`, the persisted Job, and its `Location`. It never waits for the model. The dynamic route
exists only while that Sink instance is enabled on the current Peer. Generic `/jobs` admission can create the same Job type;
creation does not promise that a locally capable Peer is running.

## Definition And Result Contract

Sink config contains only `{ "agent": <id> }`. The Agent definition remains the single authority for system prompt, AI model,
tool set, nullable tool choice, and per-turn model-call budget. Agent Query does not seed an Agent or duplicate its definition.

The recommended definition selects these exact tools:

- `retrieve`, `get_entities`, and `resolver` for recall and content interpretation;
- `get_entity_neighborhood`, `find_path`, and `get_connected_components` for bounded graph exploration;
- `submit_query_result` for the final answer and supporting Block/Relation references.

```json
{
  "name": "InKCre Agent Query",
  "system_prompt": "Answer the user's information need from InKCre. Explore the available retrieval, entity, resolver, and graph tools as needed. Do not claim evidence you did not read. Finish by calling submit_query_result with a concise answer and the Block or Relation references that support it. If the available evidence is insufficient, say so explicitly and submit the references you did find.",
  "model": 1,
  "tools": [
    "retrieve",
    "get_entities",
    "resolver",
    "get_entity_neighborhood",
    "find_path",
    "get_connected_components",
    "submit_query_result"
  ],
  "tool_choice": "auto",
  "max_model_calls_per_turn": 8
}
```

Replace `model` with an AI model ID available in the deployment. `tool_choice` may be `null` for a provider that cannot
represent it; the system prompt still defines result delivery. A successful result has non-empty `answer` and zero or more
`references`, each `{ "type": "block" | "relation", "id": <int> }`.

## Execution And Ownership

Claim eligibility requires the exact Sink instance to be running locally and its Agent/model/tools to be executable. The
handler then runs one in-memory Thread and awaits its current Turn. The last successful `submit_query_result` from a closed
Assistant/ToolResult pair becomes `Job.state.result`; ordinary termination is recorded separately. Normal completion without
a submission fails explicitly. A closed submission is retained best-effort if a later model call fails, the Job times out, or
execution is cancelled.

The generic read tools are controllers beside their semantic owners. They adapt Agent input/result shapes and call ordinary
domain services; they do not move retrieval, Resolver, or graph behavior into Agent Query. `submit_query_result` alone is
Sink-owned because delivery is the Sink's behavior.

The first version reads text/JSON and already-derived media text. It does not invoke raw multimodal interpretation, create a
second query/result store, persist Thread history, or add a new Peer capability.
