# Info-Base Ingestion Contract

## Why This Doc Exists

The ingestion path crosses sources, resolvers, storage, info-base managers, and sink embedding updates. The core contract is easy to break without a shared design memory.

## Cross-Unit Truths

### 1. The database is the authority for persisted blocks and relations

- `BlockModel` and `RelationModel` are the persisted graph.
- A block row may contain inline content or a storage pointer.
- Raw content retrieval is a runtime concern handled through storage and resolver layers.

### 2. Sources and extensions propose graph data; info-base owns persistence

- Sources or extension helpers construct blocks, relations, or `SubGraphForm` values.
- `InfoBaseManager` owns recursive insertion of subgraphs and arcs.
- Persistence order matters: blocks are fetchserted before dependent relations are finalized.

### 3. Block deduplication is resolver-defined

- `BlockManager.fetchsert()` delegates duplicate detection to `resolver.get_existing(...)`.
- The default resolver behavior matches on `resolver + content`.
- If a resolver needs stronger identity semantics, that logic belongs in the resolver contract, not in route handlers or sources.

### 4. Relation deduplication is graph-edge-defined

- `RelationManager.fetchsert()` matches on `from_ + to_ + content`.
- Relation identity is separate from block identity.

### 5. Resolver and storage responsibilities must stay separated

- A resolver interprets a block.
- A storage backend retrieves raw content when `block.storage` is set.
- A resolver may use relations and the other side's resolver output as dynamic attributes.
- A resolver should not bypass storage-specific access patterns by directly assuming where raw content lives.

### 6. Embeddings are sink-owned, even when updated during ingestion

- The embedding layer is part of sink behavior.
- Block creation can trigger embedding upserts, but that does not make embedding a source or info-base responsibility.

## Authoritative Code Anchors

- `app/business/info_base/main.py`
- `app/business/info_base/block.py`
- `app/business/info_base/relation.py`
- `app/business/info_base/resolver/main.py`
- `app/business/info_base/storage/main.py`
- `app/business/sink/embedding.py`

## What Does Not Belong Here

- per-extension resolver quirks
- temporary migration plans
- feature ideas that are still under debate
