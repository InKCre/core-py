# Memos Extension — Backend MVP Implementation Plan

## Control Surface

- **Maturity**: **Execution baseline**。The plan has approved Technical/Acceptance contracts plus verified
  addresses、versions、runtime assumptions and failure branches。
- **Delivery scope**: `memos-extension` ownership unit under the `memos-backend` MVP。
- **Objective**: make MoeMemos Android 2.0.4 use InKCre as a minimal Memos 0.29.1-compatible backend，with
  every successful native write committed as info-base graph/raw storage and every read reconstructed
  through the memo resolver。
- **Guardrails**: no parallel Memos store；no direct adapter reads of block/relation rows；no unproved API
  surface；no Memos semantics in generic graph managers；no durable/shared-doc mutation in implementation
  batches。
- **Execution entry**: the remaining Impact Handshake must bound the final code/client-web/migration/doc
  state diff，then Sir must explicitly say “开始”。

Verified evidence and branch traversal live in [preflight.md](preflight.md)。Addresses below are either
**existing**（already inspected）or **candidate**（the intended owner，final symbol name may change at the
Impact Handshake）。

## Slicing and Ordering Basis

The plan is vertically sliced by an observable behavior crossing protocol → canonical/graph command →
transaction → resolver → native response。Shared changes are extracted only when the next slice cannot be
implemented safely without them。

The dependency order is:

```text
runtime/auth/config safety
  → bootable Memos protocol
  → text CanonicalMemo round-trip
  → list/PATCH/pagination
  → writable storage + attachments
  → comments + owned deletion
  → compatibility hardening
  → pinned APK proof
```

This is not directory-by-directory work。Each increment has an observable exit proof and reruns the
previous increment's focused tests。

## Target Topology

```text
peer operator ── PUT /extensions/memos/config ──→ validated raw PAT config

MoeMemos 2.0.4
  → base URL https://<deployment>/memos/
  → retained extension route host /memos
  → public profile child router | PAT-protected protocol/file child routers
  → Memos 0.29.1 adapter
  → memo application service (coordinated PostgreSQL writes without a completeness guarantee)
  → CanonicalMemo root + attachment/comment blocks + typed relations + DB raw storage
  → versioned memo/attachment resolvers
  → Memos 0.29.1 DTO
```

Installed resolver decoders remain available for persisted blocks even when the extension's live API and
source surfaces are disabled。Protocol generation and canonical resolver generation remain orthogonal。

## Extension Seam for Future Products and Access Modes — D-048

Dependency direction is fixed now，without building empty flomo/collector frameworks：

```text
family semantics
  CanonicalMemo + graph mapping + commands + solved resolver model
        ↑ consumed by
product-generation adapter
  Memos 0.29.1 wire ↔ canonical/solved translation
        ↑ invoked by
access mode
  current backend routes/auth | future collector client/cursor/reconciliation
```

Candidate package ownership：

```text
extensions/memos/
  config.py
  family/
    schema.py
    graph.py
    service.py
    resolver.py
  products/
    memos/
      v0_29_1/
        wire.py
        adapter.py
        backend.py
  attachment.py
```

The exact folder names may be tightened during the Impact Handshake，but the dependency boundary may not
collapse：family modules never import Memos/flomo DTOs or backend/collector transports；product mapping does
not open DB sessions or own scheduling；access modes call the family application service and read solved
results。A future flomo generation adds a sibling under `products/`。A future collector adds transport/
cursor/reconciliation orchestration without forking CanonicalMemo or graph mapping。

Tests mirror the boundary：

```text
tests/extensions/memos/
  family/                         # reusable canonical/graph/resolver contract suite
  products/memos/v0_29_1/
    fixtures/                     # exact product-generation JSON/query/error cases
    test_adapter.py
  backend/                        # route/auth/lifecycle behavior
  integration/                    # PostgreSQL graph/storage behavior
```

Future product adapters run the same family contract suite against their mappings，while keeping their own
native fixtures。Backend and collector orchestration never share a test merely because both use the same
product API generation。

## Preflight Corrections Incorporated

1. Memos attachment order is real product semantics（D-040），not hypothetical order；D-044 fixes the exact
   relation grammar。
2. An attachment upload with `memo=null` is a valid standalone operation；D-041 more generally rejects
   “no partial graph” as an observable guarantee。
3. Explicit `updateMask` is a query parameter；missing-mask inference remains adapter-local D-034。
4. Writable storage is a required implementation slice。D-043 selects PostgreSQL BYTEA-backed
   storage，not an optional mid-flight schema choice。
5. Existing client-web config save is broken by a path mismatch；D-045 includes its repair as a separate
   sibling-repo batch。
6. FastAPI 0.139.2 live child-router mutation works，but route removal/cache invalidation relies on private
   framework behavior and must be encapsulated behind one tested runtime host helper。
7. Extension config schema is currently persisted only from `on_start()`，but this is not a disabled-config
   blocker：client-web uses it only as an optional editor aid，while core can import `config_cls` to validate。
8. Current relation retrieval uses AND for simultaneous incoming/outgoing lookup，and the resolver caches
   a direction-agnostic result；both would misresolve a memo star graph and need generic correctness fixes。
9. `BlockManager.fetchsert()` is forbidden for backend create because equal memo content is not identity and
   the path also mixes synchronous embedding work into the native transaction。

## Execution Increments

### I-00 — Freeze design and executable fixtures — completed

- **From → To**: reviewed design probe → approved Technical/Acceptance contracts and Execution baseline。
- **Completed evidence**: D-039–D-048、bounded API/fixture contract、pagination/relation/storage/delete
  semantics and preflight branch traversal。
- **Remaining preparation**: the Impact Handshake must enumerate the final core-py/client-web/migration/doc
  addresses before execution。

I-01 onward changes product code and remains blocked until Sir's explicit start。

### I-01 — Core route/auth/config/lifecycle safety

- **Observable slice**: existing core routes remain peer-JWT protected；a test extension can expose public
  and custom-auth child routers；enable → disable → re-enable changes availability without duplicates；
  config updates cannot persist invalid state。
- **Existing addresses**:
  - `run.py`，`app/middleware.py`；
  - `app/business/extension/main.py`，`app/routes/extension.py`；
  - focused extension/auth/runtime tests。
- **Work**:
  1. reuse peer JWT verification as a router dependency and attach it to the core protected tree；keep
     health/readiness/docs/openapi public；ordinary extensions default to the same peer dependency；
  2. add the one overridable dependency hook retained in D-036；do not add an auth enum、path exceptions、
     sub-app or middleware registry；
  3. centralize a retained extension host route set and FastAPI invalidation；fix `RUNNING_EXTENSIONS`
     membership、duplicate start and ineffective close；
  4. unpublish before close，retain fail-closed state on close failure，and make cleanup retry idempotent；
  5. separate installed decoder availability from live API/source activation；disable does not unregister a
     decoder needed by existing blocks；
  6. import `config_cls` for config updates while disabled without publishing routes；do not make persisted
     `config_schema` a lifecycle gate；
  7. implement current + shallow patch → `config_cls` validate → persist normalized JSON → assign live
     config；remove `on_close()` stale config persistence。
- **Failure branches**: construction/start failure publishes no routes；DB config failure changes no runtime
  value；a crash after config commit is healed from DB authority at restart；repeated toggles converge。
- **Exit proof**: peer/public/custom auth matrix、config rollback and route availability lifecycle tests；all
  existing core route-auth behavior remains covered。

### I-02 — Bootable namespaced Memos protocol

- **Observable slice**: MoeMemos can select v1 via public profile，authenticate with the configured PAT and
  read current profile/GENERAL settings；disabled extension returns `404`。
- **Existing addresses**: `app/database_contract/profile.py` and extension discovery/sync。
- **Candidate addresses**:
  - `extensions/memos/__init__.py`，`pyproject.toml`，`config.py`；
  - `extensions/memos/products/memos/v0_29_1/` adapter-owned wire/backend modules；
  - `tests/extensions/memos/test_route_mount.py`，`test_protocol_auth.py`。
- **Work**:
  - add checked-in Memos artifact/profile without redesigning artifact registry；
  - compose an auth-neutral root with public detection and PAT-protected protocol/file children；
  - compare the ordinary raw PAT using constant-time comparison；
  - expose only profile、auth/me and GENERAL settings for this slice；leave v0 status unregistered；
  - keep the minimal D-036 code-shaped dependency example in implementation/local technical docs later。
- **Failure branches**: malformed/missing/peer/old/revoked PAT → `401` + Bearer challenge；Memos PAT on core
  routes → `401`；malformed auth never blocks public profile；unconfigured extension exposes only profile。
- **Exit proof**: U-01、U-10、U-11 and U-12 startup/auth/config subsets。

#### Separate client-web batch

Fix `../client-web/packages/core/src/extension/base.ts` to call
`/extensions/{extension_id}/config` and cover the request。This is a separate repository/change batch；it
must not be folded into a core-py or shared-doc commit。Core HTTP acceptance can proceed without claiming
the GUI works，but productized operator setup cannot。

### I-03 — Text CanonicalMemo create and resolver read-back

- **Observable slice**: create a text-only top-level memo，commit one root block，resolve it and return the
  native response；two equal bodies create two identities。
- **Existing addresses**:
  - `app/schemas/info_base/block.py`；
  - `app/business/info_base/block.py`，`relation.py`，resolver base/manager。
- **Candidate Memos owners**:
  - `extensions/memos/family/schema.py` — CanonicalMemo v1 and solved memo；
  - `extensions/memos/family/resolver.py` — versioned decoder；
  - `extensions/memos/family/service.py` — application command coordinator；
  - `extensions/memos/family/graph.py` — mapping/repository；
  - reusable family canonical、round-trip and write tests。
- **Core work**: only caller-session block edit/delete and relation create/update/delete/query correctness；
  no Memos predicates or owned traversal in generic managers。
- **Memos work**: deterministic JSON，UTC RFC3339 serialization，explicit block create，resolver-mediated
  native projection and clear unknown-generation/invalid-content failures。
- **Failure branches**: invalid DTO/canonical → `400` before primary write；root failure → non-2xx but may
  leave attempted component residue under D-041；resolver failure → no fake success/fallback；embedding is
  not invoked inside the native write。
- **Exit proof**: U-03 text subset and U-07 root round-trip，including equal-body identities and diagnosed
  root-write failure behavior。

### I-04 — Sync, PATCH and pagination

- **Observable slice**: MoeMemos syncs NORMAL and ARCHIVED pages；PATCH changes only selected facts and
  returns resolver-derived native state。
- **Candidate address**: `extensions/memos/query.py` or memo-owned repository in `graph.py`，plus sync/mask
  tests。
- **Work**:
  - query memo resolver roots，exclude comments by parent relation，enforce the exact deployment creator
    filter and state；
  - default order by canonical `created_at DESC, block.id DESC`；use an opaque versioned keyset token bound
    to state/filter/cursor；
  - support client pageSize 200 and return `nextPageToken` including empty terminal value；
  - parse explicit query `updateMask` under 0.29.1 semantics；otherwise infer from raw body keys only；
  - keep state/visibility/pinned authority at the D-042 root location。
- **No initial projection/index**: personal-scale JSON/graph query is accepted until measurement proves a
  query projection；any future index is derived retrieval support，not a second memo authority。
- **Failure branches**: invalid creator filter/page token/mask → `400`；false/empty/list presence updates；
  concurrent inserts do not shift later pages；top-level list never leaks comments。
- **Exit proof**: U-02 and U-04 with at least two pages，NORMAL/ARCHIVED and explicit/missing-mask fixtures。

### I-05 — PostgreSQL writable storage and attachment graph

- **Observable slice**: upload unattached or memo-owned attachment → list → attach/reorder → authenticated
  raw download → delete，with resolver-only attachment reconstruction。
- **Existing addresses**:
  - `app/business/info_base/storage/`，`app/schemas/info_base/storage.py`；
  - `app/database_contract/profile.py`，schema discovery/application-table manifest；
  - `migrations/` and migration/readiness tests。
- **Candidate addresses**:
  - generic database-binary storage implementation and a `storage_blobs`-like SQLModel/table；
  - Memos attachment model/resolver/service/router；
  - attachment/storage/transaction tests。
- **Core work under D-043**:
  - add caller-session put/get/delete to the storage contract；
  - store only generated pointer + raw `BYTEA` in the raw table；
  - add one built-in database-binary storage profile/instance and make built-in storage setup consume the
    profile instead of duplicating literals；
  - add migration、metadata、manifest and generated client-web DB-contract pressure。
- **Memos work under D-044**:
  - attachment block owns filename/media type/size/storage pointer；raw bytes remain in storage；
  - allow zero-or-one owning memo relation；`memo=null` creates a valid orphan；
  - preserve request order in `attachment:<position>` relations；PATCH attachment lists have set semantics；
  - enforce decoded size limit、base64/filename/media validation and PAT raw download。
- **Failure branches**: raw or graph failure returns the exact result for the primary command and may leave
  diagnosable residue；memo create failure leaves an earlier successful orphan valid；missing bytes/filename
  mismatch is `404`；empty attachment list attempts to remove the owned set。
- **Exit proof**: U-03 attachment subset and U-06，plus migration/readiness and the selected 32 MiB
  MVP boundary。

### I-06 — Comments and owned deletion

- **Observable slice**: comment create/list/update/delete as independent memo roots；parent delete follows
  D-046 primary-success/best-effort cleanup and preserves referenced memo targets。
- **Candidate addresses**: reuse Memos service/graph repository and add comment/delete/transaction tests。
- **Work**:
  - comment → parent relation，top-level exclusion and resolver projection；
  - comment visibility follows the parent at creation/update according to exact fixture；
  - remove the root from subsequent list/read，then attempt parent/comment relations、exclusively-owned
    attachment blocks and raw cleanup；
  - reject multiple attachment owners and bound traversal with a visited set。
- **Failure branches**: shared reference target survives；corrupt cycles stop without over-delete；mid-delete
  residue is permitted；repeated unknown delete returns the approved `404` behavior。
- **Exit proof**: U-05 and U-08，including graph snapshots before/after and residue/over-delete fixtures。

### I-07 — Compatibility and lifecycle hardening

- **Observable slice**: all unsupported、auth、invalid filter/token/mask、unknown resolver、missing raw and
  hot lifecycle branches return exact non-2xx without false success；D-041 explicitly permits graph residue。
- **Work**: finish protocol `400` error translation，unsupported route assertions，OpenAPI/route-set
  invalidation proof，batch/list performance smoke and all previous regression suites。
- **Exit proof**: U-09 plus the full failure matrix；lint、typecheck、unit/integration and migration checks
  pass。

### I-08 — Pinned MoeMemos APK proof and promotion handoff

- **Observable slice**: official MoeMemos 2.0.4 APK logs in，syncs，creates，edits，archives/deletes and
  handles attachments against InKCre；comments remain a separate protocol fixture。
- **Runner boundary**: core-py has no Android/ADB harness，so a controlled external runner produces the
  evidence bundle；ASGI tests do not substitute for the APK。
- **Evidence**: APK tag/commit/digest、desensitized HTTP transcript、profile version、committed graph
  snapshot、resolver result and client-visible outcome。
- **Exit proof**: all accepted U-IDs pass；implementation facts are ready for a separately reviewed durable
  documentation promotion batch。

## Dependency and Review Shape

```text
D-036/D-038/D-039 ─→ I-01 ─→ I-02
D-042 ──────────────────────→ I-03 ─→ I-04
D-043 + D-040 + D-044 ─────────────────→ I-05
D-046 ───────────────────────────────────────→ I-06
I-01…06 ─→ I-07 ─→ I-08
```

All Technical/Acceptance decisions are closed by D-039–D-048，the Impact Handshake is approved，and Sir has
granted explicit start。Execution begins at I-01。If final address exploration reveals a new owner or observable
behavior，the plan returns to the relevant gate instead of silently expanding during execution。

## Change Batches and Commit Boundaries

These are review/verification batches，not authorization to commit：

1. core-py route auth + extension runtime/config safety；
2. core-py Memos artifact/startup surface；
3. client-web generic config-path fix（separate repo）；
4. core-py CanonicalMemo text graph + query/PATCH；
5. core-py writable storage schema/migration + attachments；
6. core-py comments/delete/hardening；
7. external APK evidence；
8. Hub/shared/local durable-doc promotion through owner-specific workflows and separate commits。

Hub source edits、shared-ref bumps、Spoke code/local docs and sibling client-web changes must never be
collapsed into one commit merely because they belong to one product unit。

## Shared-Surface Budget

| Surface | Allowed state diff |
| --- | --- |
| Artifact registry | add checked-in `memos` catalog entry only；no redesign |
| Extension runtime | route dependency hook、retained route host、correct hot lifecycle/config ordering |
| Resolver registry | reuse exact versioned keys；separate decoder availability from API activation |
| Info-base managers | caller-session mutation + relation query/cache correctness only |
| Storage | D-043 generic DB binary put/get/delete + one raw table/profile/instance |
| Database/query | storage migration required；no memo table/projection/index initially |
| Sink/embedding | no authority change；native writes avoid synchronous fetchsert embedding |
| Memos extension | all canonical、predicate、resolver、query、adapter and owned traversal semantics |
| client-web | generic extension config path and generated DB projection only |
| Durable docs | no implementation-batch edit；promotion later by owner |

## Verification Ladder

1. **Pure contract**: canonical serialization、DTO mapping、mask parsing、cursor、resolver and PAT compare。
2. **ASGI**: core/public/Memos auth matrix，route table，enable/disable/re-enable and config lifecycle。
3. **PostgreSQL integration**: graph/FK/JSONB/BYTEA behavior，pagination，storage and deletion；test actual
   local transaction choices without promoting them to a graph-completeness guarantee。
4. **Repository checks**: `pdm run lint`、`pdm run typecheck`、`pdm run test` plus migration commands when
   the new table lands。
5. **Runtime**: healthy SVC worktree database，migration/readiness/catalog reconciliation。
6. **APK E2E**: pinned released APK and retained evidence bundle。

Existing ordinary pytest deliberately avoids PostgreSQL and skips extension sync，so layers 2/3 require an
explicit harness。A green pure suite cannot be reported as graph transaction or hot-runtime proof。
