# Business Units

> Applies to `app/business/`; deeper guides own local hazards.

- Read `docs/30-unit-tdd/business-pipeline-and-authority.md` before a change crosses business subtrees.
- `info_base` owns graph persistence; sources and extensions propose commands but do not copy generic persistence.
- AI execution remains graph-blind. Agent and organization layers may compose it but must not move graph or resolver policy into AI.
- Semantic and lexical retrieval own separate derived records and ranking policy; neither owns graph facts or mutates the graph while reading.
- Global Job/Cron machinery owns durable execution occurrence and claim lifecycle; domain units retain typed payload and effect semantics.
- Peer owns identity, capability, lease, and delegation transport facts; typed business codecs remain with their business owner.
- Preserve caller-owned database sessions: a helper must not commit a session it did not create.
- Required check: run tests for every affected business owner and the repository import-boundary checks.
