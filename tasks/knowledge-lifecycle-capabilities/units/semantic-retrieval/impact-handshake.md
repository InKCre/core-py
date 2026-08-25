# Semantic Retrieval Implementation Impact Handshake

> **State**: approved for implementation on 2026-08-07。Sir requested a clean task-state commit before the first code、
> schema or client-web mutation；artifact publication、shared runtime reset and Hub promotion retain their later gates。

## Address And Object

### core-py

- `app/configuration/`、`app/schemas/configuration.py` and deployment-config routes：generic `ConfigContract` plus
  deployment-scoped `ConfigManager` mechanics。
- `app/schemas/info_base/**`、`app/business/info_base/**` and every repository-owned graph producer：database-state-free
  forms、StarsGraphForm/GraphForm、normalize/submit、Resolver text/labels and Relation projection。
- `app/schemas/ai.py`、`app/business/ai/**` and removal of `libs/ai.py`/legacy RAG/query paths：Provider/Model/Profile、
  OpenAI-compatible dialect and canonical embedding/chat contracts。
- `app/schemas/agent.py` and `app/business/agent/**`：persisted definitions、in-memory Thread persistence backend、async
  turn lifecycle and runtime Tool registry。
- `app/schemas/semantic_retrieval.py`、`app/business/semantic_retrieval/**`、routes and scheduler：records、explicit
  maintenance、local retrieval and capability codec/inbound。
- `app/business/organization/**` and organization routes：explicit focal-Block rumination using the configured Agent and
  Graph tools；no periodic organization runner。
- `app/schemas/peer/**`、`app/business/peer/**`、middleware、settings、composition root and database-contract machinery：
  technical Client→Peer hard cut、lease/discovery、HTTP outbound and three fixed business inbounds。
- exact built-in Resolver/producer surfaces under `extensions/{memos,rss,mail,github,telegram,twitter,learn_english}/`。
- `migrations/` and database-contract projection/readiness/profile surfaces：three append-only structural revisions，new
  clean shared-database target and a breaking peer runtime contract revision。
- `tests/`：domain-focused suites、real PostgreSQL integration、real RSS/Atom/Memos journeys and pinned SQLite Architecture
  corpus authority；generated graph/vector artifacts remain ignored。

### client-web

- `packages/core/src/{peer,extension,organization,semantic-retrieval,ai/info-base}` and generated database/runtime contract：
  Peer routing、removal of `Client.request()`、exact Extension management and typed rumination/retrieval facades。
- technical database/admin surfaces migrate Client→Peer；product/repository identity and ordinary user-facing copy keep
  “client”。
- the selected Block details surface receives one explicit Ruminate action with pending/success/error handling。
- final generated contract pin requires an exact core commit plus matching digest-pinned OCI artifact。

### Documentation And Runtime

- core-py Unit TDD、deployment/security/runtime docs and nearest AGENTS are reconciled with implemented evidence。
- shared PRD/Product TDD changes use the Hub workflow and a separate shared-doc/ref operation；`docs/_shared/**` is never
  edited directly in this Spoke change。
- canonical production and the data-free preview baseline are rebuilt only at the later delivery gate under D-195；there
  is no active staging target。

## State Diff

```text
legacy split AI/RAG + one embedding row per entity
  -> Provider/Model/Profile + profile-scoped records + explicit maintain/retrieve

embedding-specific Resolver strings + isolated Relation content
  -> one general Block text projection + Block-local endpoint labels
  -> directed subject/property/value Relation projection

SubGraphForm over persisted models
  -> StarsGraphForm producer authoring + signed-ID flat GraphForm command

one-call reasoning helpers
  -> persisted reusable AgentDefinition + async in-memory Thread runtime + typed Tools

unused organization hooks
  -> explicit focal-Block rumination that may submit an ordinary graph or complete with no write

Client endpoint shortcuts
  -> Peer capability advertisement + lease + exact HTTP protocol + local-or-delegate domain facades
```

The peer runtime wire hard cut includes technical profile/database names and JWT issuer
`inkcre-client -> inkcre-peer`。Audience `inkcre-api`、shared-secret trust model、maximum token lifetime and user-facing
client product terminology remain unchanged。

## Operation And Expected Side Effects

- Add new deep domain modules and tables，hard-delete superseded internal mechanisms and rename technical Client symbols。
- Append structural Alembic revisions；do not create Resolver-row、Mail-edge or legacy vector compatibility migrations。
- Regenerate the language-neutral database contract and client-web TypeScript projections from one exact core artifact。
- After verified delivery artifacts exist，make one recoverable destructive rebuild of canonical production application
  schemas and advance/sanitize preview-base。The dump、digest and Neon recovery branch precede reset；archived staging
  lineage is untouched。
- Promote proven durable truth only after Acceptance；do not mix Hub edits/shared-ref bumps with Spoke implementation
  commits。

## Blast Radius Forecast

- **Very high inside core-py**: schema imports、composition/bootstrap、Resolver abstract methods、all graph producers、AI
  calls、scheduler and route assembly must move coherently across implementation increments。
- **High protocol impact**: PostgREST relation names/types、JWT issuer、peer runtime profile and client-web generated
  contracts break together。There is intentionally no compatibility interval because shared databases are rebuilt。
- **Bounded product impact**: new direct retrieval/rumination capability and one Block action；no Chat InKCre product、
  automatic organization、generic capability console or new release unit。
- **No source/storage authority change**: collected information remains Blocks/Relations；Storage owns bytes/pointers and
  Resolver owns interpretation。

## Invariants Check

- Blocks/Relations remain info-base authority；embedding rows、capability snapshots and corpus aliases are derived/support
  state，never new information entities。
- Organization may materialize ordinary graph improvements but retrieval/indexing remains use-owned。`retrieve()` never
  repairs candidate embeddings implicitly。
- AIManager stays graph-blind；Resolver stays model/profile-blind；PeerManager stays business-capability-blind。
- No generic `/capabilities/{id}/invoke`、generic delegation job、readiness advertisement or automatic replay after
  outcome-unknown dispatch。
- Agent runtime validates Tool input once through the registered Pydantic schema；InfoBase write relies on database FK for
  positive references and adds no duplicate existence layer。
- `get_label()` is deterministic and Block-local；Relation freshness depends exactly on Profile、Relation and two endpoint
  Blocks。
- Technical/database/domain names use Peer；marketing、landing、external-app and product/repository “client” vocabulary is
  not mechanically renamed。
- No S3 storage、persistent Agent threads、graph-reading Agent Tools、automatic rumination trigger、pagination or HNSW is
  introduced。

## Verification

1. Static/lint/type checks plus structural retired-symbol/ID searches after each coherent increment。
2. Deterministic fake dialect/Agent/Peer protocol state-machine tests for lifecycle、validation、parallel Tools、failover、
   exact-target routing and outcome-unknown behavior。
3. Disposable PostgreSQL base→head and empty current-head→new-head migrations；ACL、sequence、trigger、PostgREST binary、
   config and generated protocol checks。
4. Black-box Memos、RSS/Atom、graph producer、Resolver/Relation projection and explicit rumination journeys through real
   domain boundaries。
5. Real provider credentialed embedding quality and tool-calling Acceptance over entity judgments，including SQLite
   Architecture rumination；provider responses/scores are not committed authority。
6. Two real ASGI/HTTP Peer runtimes prove local bypass、delegation、non-execution failover、target constraint、JWT/envelope
   and all three fixed capability inbounds。Standards evidence replaces an unnecessary real reverse-proxy smoke test。
7. client-web generated contract check、package tests/build and BlockDetailsPanel behavior after exact artifact sync。
8. Before shared reset，verify dump digest/recovery branch/targets；after reset，readiness and production discovery must
   report the same new contract revision/head before the operation is considered complete。

## Uncertainty And Execution-Time Checks

- Exact generated DDL、index names、PostgREST grants/sequences and Alembic split are inspected after target SQLModel schema
  exists；generation before implementation would be fictitious。The three ownership boundaries remain review-visible even
  if autogenerate requires regrouping。
- Provider semantic quality varies；deterministic lifecycle tests own CI，while a named credentialed provider owns the
  empirical Acceptance run。Failure leads to retrieval/projection diagnosis，not test-shaped production code。
- client-web final pin cannot close before a matching digest-pinned core OCI artifact exists。Publication is separately
  authorization-gated after a core commit；local-core generation supports implementation beforehand。
- canonical production currently disagrees with its checked-in profile（v1/d9 versus v2/d0）。The clean rebuild closes the
  discrepancy only after target runtime evidence；this unit does not mutate production during ordinary implementation。
- The worktree already contains task-packet/local-doc changes from prior units。Implementation preserves them and stages or
  commits only explicitly authorized scope。

## Execution Order

Follow [implementation-plan.md](implementation-plan.md) I0→I8，with I1 Graph forms and I3 Agent runtime allowed to proceed
independently after I0/I2 prerequisites and joining at I5 rumination。Each increment must satisfy its local verification
before the next dependency consumes it。Cross-repository artifact publication、shared database reset and Hub promotion are
later explicit gates，not hidden side effects of beginning core implementation。
