# Embedding Maintenance And Deployment Config

> [Technical design index](index.md)

## T-013 Embedding Maintenance Outcomes And Freshness（approved by D-104–D-111）

### Do not persist `dirty`

Record presence and freshness are derived facts，not another mutable state machine:

```text
missing = no (profile, entity) record
fresh   = record exists + D-101 timestamp dependencies satisfied + vector dimensions match
stale   = record exists but one of those predicates fails
```

Keeping an old stale record is harmless when every retrieval candidate query applies those predicates。Maintenance may
replace it after success；garbage collection is a storage concern，not required for correctness。A trigger-written
`dirty` flag would duplicate the same dependency facts，need endpoint cascades for Relation and create cross-peer update
ordering that timestamps deliberately avoid。

### Attempt outcomes are not EmbeddingRecords

One maintenance attempt over one entity/profile has three semantic outcomes:

| Outcome | Examples | Record effect |
| --- | --- | --- |
| `embedded` | projection available，AI response valid and dimensions match | upsert successful record |
| `unavailable` | exact Resolver lacks requested capability；supported projection returns `None`；this peer lacks the exact Resolver | leave missing/stale record unchanged |
| `failed` | corrupt content/storage read；provider disabled/unreachable；adapter/model error；dimension mismatch | leave missing/stale record unchanged and expose diagnostic |

`UnknownResolver` is executor-local availability，not a global property of the Block；another peer may implement the
same exact Resolver。Likewise a provider/network failure is temporal execution evidence。Persisting either as a shared
entity state could incorrectly suppress a capable peer or outlive the failure。

The current proposal therefore persists only successful EmbeddingRecords。`unavailable` / `failed` belong to the result
and diagnostics of the maintenance attempt that observed them。This does **not** yet decide whether that attempt is a
durable job or a synchronous/bounded command；if a durable job is justified，its item diagnostics remain execution facts
owned by that job，not status columns on embedding tables。

### Failure and replacement boundary

- projection and AI execution happen without holding one database transaction across network/storage work；
- success uses atomic upsert on `(profile, entity)` and receives database-owned record `updated_at`；
- unavailable/failure never deletes a previously successful record，but retrieval excludes that record when stale；
- concurrent executors may duplicate work；last successful compatible upsert wins。The already accepted late-write race
  remains；MVP does not add leases、revision fields or distributed locks solely to eliminate duplicate AI calls；
- `refresh` remains the established cache-snapshot option and is not reused to mean durable embedding regeneration。The
  operation vocabulary for ordinary stale/missing maintenance versus forced rebuilding of already-fresh records remains
  part of this review。

### Existing failure evidence

Current `EmbeddingManager._skipped_block_versions` is process-local，Block-only and cleared on restart。It conflates
unsupported projection with unknown local Resolver，while provider errors escape。The 60-second scanner selects only the
first ten missing rows；without its skip set，a stable unavailable prefix can starve all later entities。These are failure
samples，not a reason to persist a global unavailable state。

### Maintenance execution contract（approved）

Do not create an EmbeddingMaintenanceJob relation in MVP。A successful EmbeddingRecord is already an idempotent progress
marker；after interruption，the next ordinary scan naturally selects the remaining missing/stale entities。No separate
job cursor、claim state or item ledger is required to resume correctness。

```text
SemanticRetrievalManager.maintain(profile, bounded execution options)
  -> scan deterministic pages of candidate Blocks and Relations
  -> derive projection outcome for each entity
  -> continue past unavailable entities until an available batch is filled or scan ends
  -> AIManager.embed(model, ordered text batch, dimensions)
  -> validate count/order/dimensions
  -> short atomic upsert transaction per successful batch
  -> return attempt report (embedded / unavailable / failed counts + bounded diagnostics)
```

- the scheduled path and explicit maintenance command call the same manager operation；collection/organization never
  invoke provider-specific embedding code。The old eager `BlockManager.fetchsert()` call and old process-local skip set are
  removed。
- database page limit is not the success batch limit；the scan advances past unavailable rows so a low-ID unsupported
  prefix cannot starve later candidates。A cursor is local to one invocation，not durable authority。
- projection/storage reads and provider calls occur outside a database transaction。Only successful batch upsert holds a
  short transaction。Batch response cardinality/order and every vector dimension are validated before any row is written。
- ordinary `maintain` selects only missing/stale records。A separate administrative `rebuild` operation includes records
  that were fresh at operation start and uses that start timestamp as its cutoff，so its own writes are not selected again
  in the same run。`refresh` is not an alias for either operation。
- interruption after any committed batch is safe。Repeating ordinary maintenance does not repay completed work；
  repeating a full rebuild may regenerate some already rebuilt vectors，which is accepted low-harm duplicate work rather
  than a reason to add durable job identity。
- two peers may select the same entity and duplicate an AI call。The final valid upsert wins；MVP adds no lease/advisory
  lock/claim table solely to save that occasional call。

Automatic scheduling and batch/config ownership are closed below；they do not change the approved absence of a durable
job relation。

### Automatic maintenance scope（approved）

- SemanticRetrievalManager owns one nullable deployment-default EmbeddingProfile reference。A retrieve/maintain/rebuild
  request may explicitly select another Profile，but there is no implicit cross-profile execution or rank fusion。
- automatic maintenance processes only that default Profile。Scanning every defined Profile would spend provider calls
  on dormant evaluation/migration vector spaces merely because their definitions exist。When no default is configured，
  the scheduled operation is a no-op and defaulted retrieval reports configuration unavailable。
- switching the default does not delete the old Profile or records。The next scheduled pass begins maintaining the newly
  selected space；old records remain available for explicit evaluation/rollback and normal retention decisions。
- schedule participation/interval and maximum work per invocation are peer-local operational settings，not shared
  EmbeddingProfile fields。Equal peers need not all run a worker，and client-web does not acquire a background scheduler
  merely because core-py has one。
- SemanticRetrievalManager sends an ordered logical batch；AIManager/dialect adapter owns provider request translation and
  any provider-limit chunking while preserving one-output-per-input order。Database commit batch size is a local
  maintenance resource bound，not a vector-space contract or shared Profile setting。

The deployment-default reference is persisted through the approved deployment-scope config contract below；it is not
hidden on EmbeddingProfile as a generic `is_default` flag。

### Rejected singleton proposal

The proposed one-row `semantic_retrieval_configs` relation does not meet the independent identity/lifecycle test。A
deployment can own only one such value，and its whole lifecycle is the owner-shaped value at one deployment config key。
An ordinary FK would be useful，but that alone does not prove a dedicated singleton domain relation has sufficient value。

### Deployment-scope config direction（approved）

Use one simple shared deployment-scoped config relation，distinct from per-peer config currently stored on legacy
`clients` rows（future `peers.config`）:

```text
configs
  key: text primary key
  schema: exact schema-contract ID
  value: JSONB
  created_at / updated_at: database-owned

example
  key    = "semantic_retrieval"
  schema = "core.semantic_retrieval.config.v1"
  value  = {"default_profile": 42}
```

- `key` addresses one deployment-owned config value；`schema` selects its exact decoder/validator contract；`value`
  remains owner-shaped JSON rather than becoming a universal god-object schema。
- The concise table name `configs` is sufficient because this relation is the deployment-scoped shared config authority；
  the config on each Peer row remains explicitly peer-owned。
- core-py DeploymentConfigManager locally maps exact schema ID to a Pydantic model。Other equal peers register an equivalent local
  validator under the same ID；the durable schema value therefore cannot be a Python import path or class name。
- schema registration collision/unknown schema is explicit。Config reads and writes validate the complete value before
  exposing/persisting it；a schema-breaking change uses a new exact ID and an explicit value migration。
- `SemanticRetrievalConfig.default_profile` remains a typed Profile ID in that model。Config write/read validates only
  the complete JSON structure；it does not pass through SemanticRetrievalManager or query Profile existence。A JSON value
  cannot receive an ordinary PostgreSQL FK，so this preserves protocol/application typing but not referential integrity。
  SemanticRetrievalManager resolves the reference only when used and explicitly distinguishes dangling from unconfigured。
- DeploymentConfigManager owns exact schema-model registration/resolution and deployment config persistence；it uses the generic
  ConfigContract for value validation/normalization。SemanticRetrievalManager owns the config key's use semantics and
  behavioral consequences，not its write path。The deployment manager does not import EmbeddingProfile or scheduling
  policy。
- peer-local schedule interval/work limits remain outside deployment config。The semantic value initially needs only
  nullable `default_profile`。

### DeploymentConfigManager read/update contract（approved）

DeploymentConfigManager is the total manager for the shared `configs` relation and its local schema-model registry:

```text
register_schema(exact_schema_id, local_model)
get(key)              -> load row -> resolve schema -> validate complete value -> typed model
replace(key, schema, complete_value)
patch(key, partial_value)
```

- schema registration is idempotent for the same model and rejects a different model claiming the same exact ID。An
  unknown schema or persisted value that fails its registered model is explicit config failure，not a raw-dict fallback。
- `replace` is an upsert and validates one complete value under the supplied schema before the database changes。It is
  the only operation that may change a row's schema，so a schema migration and its new complete value are atomic。
- `patch` requires an existing row，keeps its schema，shallow-merges current object + patch，validates the complete next
  model，persists normalized JSON and then exposes success。This matches the already accepted extension-config update
  order without making DeploymentConfigManager own extension/source/storage row lifecycles。
- public HTTP semantics should name these honestly；`PUT /configs/{key}` performs complete replace/upsert and
  `PATCH /configs/{key}` performs partial update。The existing extension endpoint's PUT-as-patch behavior is historical
  evidence for a later correction，not the new generic contract。
- DeploymentConfigManager does not own semantic side effects or live caches。An owner reads the newly validated model when acting；
  if future config changes require a live callback，that pressure must define an owner-specific notification mechanism
  rather than a generic hook registry now。

### Generic configuration mechanics vs deployment-scope configs（approved）

The abstraction threshold is now met by real code:

- shared `configs` needs exact schema registry，replace/patch and typed JSON persistence；
- ExtensionManager already implements current + shallow patch → complete model validation → normalized persistence →
  owner-specific live apply；
- SourceBase and StorageBase separately retain config model/schema and validate persisted JSON on read/construction。

Do not collapse these pressures into one nominally "generic" business manager。They form two modules with different
owners:

```text
generic configuration mechanics（no deployment scope，no persistence）
  complete validation + normalized JSON
  shallow patch preparation
  JSON Schema projection when requested

deployment-scope configs domain
  configs relation / DeploymentConfig row
  exact schema ID -> local model registry
  CRUD for deployment-scoped configs table
  DeploymentConfigManager

owner managers
  ExtensionManager: ExtensionModel persistence + live apply
  SourceManager: SourceModel persistence + source consequences
  StorageManager: StorageModel persistence + storage consequences
  SemanticRetrievalManager: use-time default Profile resolution + scheduling
```

- generic configuration mechanics accept a model/contract directly。They do not know `configs`、deployment、keys、exact
  schema IDs、database sessions or owner lifecycles。Existing Extension/Source/Storage config therefore does not need an
  invented persisted exact schema ID merely to reuse validation logic。
- the deployment-scope configs module uses those mechanics but additionally owns exact schema registration/resolution and
  `configs` persistence。Only rows whose protocol stores `schema`—initially `configs`—require registry lookup。
- DeploymentConfigManager must not become a polymorphic updater for ExtensionModel、SourceModel and StorageModel。Their address，
  transaction，live replacement and failure semantics remain with their owner managers。
- implementation should move ExtensionManager's already-proven shallow-patch preparation onto the common primitive as the
  second executable consumer。Source/Storage adopt it only when their update operations actually exist；their current
  validation can reuse the complete-value primitive without adding speculative CRUD。
- no callback/hook bus is introduced。The common result is a validated model + normalized JSON；the owner decides what
  happens after persistence。

### Technical naming contract（approved by D-111）

Use names that expose the ownership split rather than two similarly named managers:

```text
generic mechanism
  module/package: app.configuration
  primary abstraction: ConfigContract[Model]

deployment-scope configs domain
  schema: DeploymentConfigModel -> table configs
  business: DeploymentConfigManager
  HTTP: /configs/{key}
```

- `ConfigContract` wraps one local Pydantic model's complete validation、normalized JSON、shallow patch preparation and
  JSON Schema projection。It has no registry、database、deployment key or live lifecycle。
- `DeploymentConfigManager` explicitly names the scope that the earlier `ConfigManager` placeholder obscured。It owns
  exact schema-ID registry and `configs` row CRUD，and calls ConfigContract for value mechanics。
- `SemanticRetrievalConfig` remains an owner-defined Pydantic config model registered under
  `core.semantic_retrieval.config.v1`；it is neither DeploymentConfigModel nor ConfigContract。
- the physical split follows current repository convention：generic support lives outside `app.business`；the persisted
  domain uses explicit `deployment_config` schema/business module names even though its table and HTTP resource remain the
  concise plural `configs`。Exact files remain an implementation-plan concern after the names are approved。
