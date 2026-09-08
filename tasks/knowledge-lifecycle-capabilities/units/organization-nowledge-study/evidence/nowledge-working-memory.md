# Evidence: Nowledge Working Memory / Daily Briefing

- **Question served**: Is Working Memory durable Organization output，or a near-term use-context projection over existing
  knowledge and activity？
- **Consumer**: [Working Memory Product shard](../product/working-memory.md)。
- **Evidence horizon**: Nowledge official documentation/API observed 2026-09-03。Recheck before version-sensitive Product or
  Technical claims。

## Official Evidence

- Daily Briefing runs each morning for every active space，reviews recent activity、generates insights、flags contradictions and
  writes a fresh Working Memory。New Memories also trigger a delayed refresh。Source：
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence)。
- Generation receives a pre-computed digest of the past week、yesterday's Working Memory、graph statistics and recent resolution
  patterns；context is capped and lower-priority sections are trimmed first。Source：
  [Background intelligence](https://mem.nowledge.co/docs/concepts/background-intelligence#context-injection)。
- Working Memory exposes active topics、unresolved flags、recent changes and priority items based on frequency/recency。Connected
  tools may load it at session start through MCP、native connector or another packaged path。Source：
  [Background Intelligence / Working Memory](https://mem.nowledge.co/docs/advanced-features#working-memory)。
- Today is returned by default；a date reads an archived day，and `space_id` scopes the read。Source：
  [Get Working Memory](https://mem.nowledge.co/docs/api/agent/working-memory/get)。
- The CLI describes it as an AI-generated daily briefing and supports read、history、whole-document edit and non-destructive
  section patching。Source：[Nowledge Mem CLI / Working Memory](https://mem.nowledge.co/docs/cli#working-memory-nmem-wm)。
- Context Bundle returns owner/profile/policy/space context for Agents and includes current Working Memory by default。Nowledge's
  Context page calls this a start card for a specific AI run and says Context does not replace durable Memories、Threads、Library
  or Skills。Sources：[Get Context Bundle](https://mem.nowledge.co/docs/api/context/bundle/get)、
  [Context](https://mem.nowledge.co/docs/ai-context)。

## Evidence Versus Inference

| Evidence / observation | Current inference | Missing evidence / confidence |
| --- | --- | --- |
| Working Memory is regenerated、space-scoped and delivered at Agent startup。 | Its primary purpose is near-term use-context assembly，not base-wide information classification。 | High。 |
| Inputs mix recent activity、graph statistics、prior briefing and resolution patterns。 | It is a derived selection/compression projection over several authorities。 | High；exact ranking/prompt is unknown。 |
| It may generate insights and flag contradictions。 | Generation can discover durable meaning，but that output should be separated from the briefing projection。 | Medium；Nowledge persistence routing is undocumented。 |
| Yesterday's result feeds today's generation。 | Derived-on-derived feedback can amplify stale summaries unless original authority remains recoverable and prior text has limited role。 | Product inference；Nowledge may have unreported safeguards。 |
| Users may edit/patch Working Memory。 | One mutable document can mix Human direction with generated projection；InKCre should not infer one authority from this packaging。 | High decomposition confidence。 |
| Archived days remain readable。 | History may support audit or continuity，but archival itself does not make prior projections source evidence。 | High conceptual confidence；storage semantics unknown。 |

## Product Disposition

D-486 confirms that Working Memory has no independent info-base Organization transfer。Its reusable learning is a downstream
Application boundary：before a concrete query exists，past activity and explicit Agent/space context may forecast a bounded
near-term working set and assemble it into an ephemeral use projection。

Any genuinely new reusable insight found during assembly must route to its owning Organization behavior and graph provenance；
the briefing then projects that authority。Generated focus/priority remains run-scoped。Human-authored direction remains an
explicit source/configuration input。A prior generated briefing may assist presentation continuity but must not silently become
evidence for its own repeated claims。

No daily scheduler、Working Memory file/Block、archive、context-bundle contract、ranking rule、token cap or edit UI is transferred。
The Nowledge Agent receiving this projection is a downstream consumer；it is not the internal Agentic execution instrument of an
InKCre Organization behavior。
