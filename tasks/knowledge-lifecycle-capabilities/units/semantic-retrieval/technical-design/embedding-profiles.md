# Embedding Profiles And Vector Records

> [Technical design index](index.md)

## Stable Vocabulary

```text
semantic representation of Block / Relation
  → EmbeddingProfile-compatible input
  → embedding
  → EmbeddingRecord(entity reference, profile, input snapshot, vector)
  → exact or ANN-accelerated vector retrieval
  → ranked Blocks / Relations
```

- **Embedding**: one vector produced from one profile-compatible input。
- **EmbeddingProfile**: the durable compatibility contract for one vector space；exact MVP shape is approved。
- **EmbeddingRecord**: one durable derived mapping from a graph entity/profile/input snapshot to an embedding；exact MVP
  shape is approved。
- **ANN index**: optional physical PostgreSQL acceleration，not domain identity or graph authority。

## Current Schema Failure

Current `block_embeddings` / `relation_embeddings` are keyed one-to-one by entity ID and store fixed `vector(1024)` plus
one timestamp。They cannot name model/provider/input contract、coexist across profiles、prove which semantic input was
embedded or distinguish stale/unavailable/error。They are migration evidence，not the new shape。

## T-001 — Profile Persistence And Mutable Freshness（D-083 persistence；immutability superseded by D-089）

### Current contract

- Persist EmbeddingProfile in the shared peer database protocol；an EmbeddingRecord is not interpretable without the
  profile that defines its vector space。
- Allow vector-contract fields to change in place。A database-owned Profile `updated_at` watermark makes older
  EmbeddingRecords candidates for rebuild；the accepted late-write race does not justify another version field。
- Allow multiple independently addressable Profiles and their records to coexist when consumers genuinely need distinct
  vector spaces、evaluation or migration；ordinary Profile edits do not require a new row。
- Keep active/default profile selection outside Profile definition，as mutable deployment/application configuration。
- Keep credentials outside the profile。A profile names a non-secret execution contract；each peer separately proves it
  has an executor/config capable of realizing it。

### Why persistence is proposed

- records remain explainable after runtime config changes；
- peers agree which vectors can be compared；
- rebuild/switch can be staged instead of corrupting one global vector space；
- profile deletion can be referentially restricted while records still depend on it。

EmbeddingProfile remains an independent typed relation but is mutable。A monotonic `version` would close the rare old-
execution/late-write race，but Sir explicitly judged its marginal harm too low to justify another field。Profile and
record database-owned timestamps therefore provide best-effort freshness rather than an exact execution proof。Global
config owns only use-specific selected/default profile references。

## T-002 — EmbeddingProfile Versus Retrieval Options（approved by D-084）

### Proposed ownership rule

EmbeddingProfile owns only selections and operations that determine the generated vector space：

- `ai_model`；
- dimensions；
- vector normalization。

AIModel owns intrinsic capability and modality declarations。EmbeddingProfile does not duplicate modalities merely to
describe which inputs its referenced model can accept。

MVP assumes a symmetric input contract and does not add candidate/query transformations。A future model with proven
asymmetric task/instruction/prefix requirements must evolve the profile contract explicitly。

Query-scoped `VectorRetrievalOptions` own how already-generated compatible vectors are searched：

- distance/similarity metric；
- top-k、maximum distance/minimum similarity and filters；
- exact versus approximate search；
- HNSW/IVFFlat query/build tuning；
- optional reranking/fusion strategy。

Metric therefore leaves EmbeddingProfile identity。MVP does not create a RetrievalPolicy table；runtime config may provide
defaults，and a request may supply admitted overrides。

## EmbeddingProfile Fields（approved by D-093/D-094）

| Field | Intended meaning | Current concern |
| --- | --- | --- |
| `id` | stable profile reference | database-generated bigint |
| `name` | optional descriptive label | UI falls back to model identity + dimensions |
| `ai_model` | stable shared executable-model reference | bigint FK；role name needs no `_id` suffix |
| `dimensions` | exact vector shape | required positive integer；adapter verifies every result length |
| `created_at` | ordinary row creation time | database-owned |
| `updated_at` | row mutation time and best-effort invalidation watermark | database-owned；rare late-write race accepted |

MVP omits `enabled` because use-owned references select active Profiles；omits normalization because no actual model/
acceptance pressure requires changing model output；and omits a generic config/options bag because dimensions is the only
proven profile parameter。

## EmbeddingRecord Shape（approved by D-101）

```text
block_embeddings:    (profile, block, embedding, timestamps...)
relation_embeddings: (profile, relation, embedding, timestamps...)
```

Composite profile/entity identity；real FK cascade on entity deletion；restrict profile deletion while either table has
records。Unavailable/error/job state is not automatically an EmbeddingRecord and remains a separate lifecycle question。
Freshness is derived from database-owned timestamps；MVP does not persist `input_digest`。

## PostgreSQL / pgvector Evidence

- pgvector performs exact nearest-neighbor search without a physical ANN index；HNSW/IVFFlat trade recall/resources for
  speed。
- a dimension-unspecified `vector` column can store different dimensions；ANN indexes must target rows of one dimension，
  for example through profile-filtered partial/expression indexes。
- therefore MVP record persistence need not prematurely choose one HNSW index per profile；quality/scale evidence can
  select physical acceleration after the logical contracts are stable。

## HNSW Cost Boundary

HNSW（Hierarchical Navigable Small World）builds a multi-layer proximity graph over vectors。A query navigates from
sparse upper layers toward denser neighbors instead of calculating distance against every record。It is approximate：
speed improves，but some true nearest neighbors may be missed。

For variable-dimension records and runtime-created profiles，a correct pgvector HNSW surface would require profile-
filtered、dimension-cast、metric-specific indexes on each record table，conceptually：

```sql
CREATE INDEX ... ON block_embeddings
USING hnsw ((embedding::vector(1024)) vector_cosine_ops)
WHERE profile_id = '<profile>';
```

and an equivalent relation index。Each dimension/metric/profile combination changes DDL。Ordinary peers currently own
data protocol operations，not migration-owner DDL，so automatic index creation for arbitrary runtime profiles would add a
privileged index-management lifecycle。

**Benefit**：lower query latency and fewer distance calculations at larger record counts。

**Costs**：build time、additional disk/memory、slower writes、vacuum/reindex maintenance、approximate recall、profile/
metric-specific DDL and tuning (`m`、`ef_construction`、`ef_search`)。Filtering by profile also interacts with ANN recall。

**Approved MVP**：use exact pgvector comparison。Add HNSW only when a representative corpus violates an accepted latency/
scale threshold；then compare ANN recall against exact search before selecting parameters。

## Review Order

1. profile persistence（approved；initial immutability superseded by D-089）；
2. profile-generation fields versus query retrieval options（approved）；
3. global AI provider/model/dialect topology and profile model reference（approved）；
4. AIModel capability/modality declarations and remaining Provider/Model fields（approved）；
5. dedicated mutable profile、consumer-owned selection and database timestamp invalidation（approved）；
6. AIDialect type / AIProvider instance shape（approved）；
7. AIModel exact fields and identity（approved）；
8. profile remaining exact fields and identity（approved）；
9. Block text representation ↔ profile input contract（approved）；
10. Relation representation and availability（approved）；
11. record entity-reference and source-snapshot shape（approved）；
12. Resolver-owned endpoint label and persistence boundary（approved）；
13. unavailable/error、derived freshness、maintenance/rebuild、config and concurrency（approved）；
14. AIManager capability implementation scope（approved）；
15. retrieval result/score/filter contract（approved）；
16. heterogeneous Peer capability delegation、API and migration（approved through D-136）；
17. minimum rumination/Agent approach required by retrieval quality（Product/Technical contract approved through D-182；
    Acceptance remains active）。
