# Memos Extension — Backend MVP Preflight

> Completed read-only preflight for the Execution baseline on 2026-08-01。This file records evidence and
> failure branches；D-039–D-048 own the approved decisions，and this file does not authorize code changes。

## Verdict

The unit topology is sound：`memos-extension` owns CanonicalMemo、graph mapping、resolver and protocol
adapters，while `memos-backend` is its first delivery scope。The MVP does **not** need a new extension
artifact registry、top-level protocol mount、resolver registry or parallel memo store。

The implementation plan does need five material corrections：

1. Memos 0.29.1 deliberately preserves attachment order，so this adapter is the source-defined exception
   allowed by D-013；order must live on relations。
2. MoeMemos can upload an attachment before a memo exists。A committed unattached attachment is a valid
   independent protocol state；more generally D-041 does not require failed commands to leave no partial
   graph。
3. `updateMask` is outside the HTTP body because the proto annotation declares `body: "memo"`；the
   explicit mask is an optional query parameter，while MoeMemos sends none。
4. client-web currently sends extension config to `/{extension_id}/config`，but core exposes
   `/extensions/{extension_id}/config`。A GUI-configurable PAT therefore requires a small client-web fix；
   the HTTP management API itself is sufficient for core-only acceptance。
5. Attachment bytes require a writable storage implementation and database blast radius。Treating schema
   work as merely conditional would defer the largest design choice until mid-implementation。
6. Extension `config_schema` is currently persisted only during `on_start()`。client-web uses it as an
   optional JSON-editor aid，but the editor works without it and the core API can import `config_cls` for
   authoritative validation。It is therefore not a disabled-extension lifecycle requirement。

## Evidence Anchors

| Surface | Pinned evidence | Consequence |
| --- | --- | --- |
| Memos protocol | tag `v0.29.1`，commit `5f194da` | exact generation authority；main/latest excluded |
| Acceptance client | MoeMemos Android tag `2.0.4`，commit `9bfc6517`，release APK SHA-256 `5043f14d…fe8fa` | real call graph and final E2E client |
| FastAPI | pinned `0.139.2` | included child routers are live/versioned；removal needs localized private invalidation |
| Extension runtime | `app/business/extension/main.py` | namespace already `/{extension_id}`；running-membership and close logic are defective |
| Auth | `app/middleware.py` + `run.py` | global peer-JWT middleware blocks extension-owned PAT before routing |
| Config | `app/routes/extension.py` + `ExtensionManager.save_config` | current PUT persists before validation；schema is optional UI metadata |
| Graph/resolver | block/relation managers + resolver base | caller-owned create is possible；mutable operations and relation reads have gaps |
| Storage | storage base/profile | read-only pointer → raw contract；no put/delete/raw serving |
| Database runtime | `svc dev status database --repo . --json` | worktree-scoped PostgreSQL runtime is healthy and migration head is known |
| client-web | `../client-web/packages/core/src/extension/base.ts` | generic config editor calls the wrong core route |

The FastAPI route assumption was also exercised in a disposable in-memory app：a retained included child
router accepted routes added after inclusion；clearing its route set plus `_mark_routes_changed()` removed
both dispatch and OpenAPI entries。There is no public symmetric removal API，so one runtime-host helper
must encapsulate this pinned-framework dependency and lifecycle tests must guard it。

## Capability Classification

| Capability | Verdict | Reason |
| --- | --- | --- |
| Checked-in extension discovery/catalog | Reuse | `extensions/<id>` + built-in profile already carries the artifact |
| `/{extension_id}` HTTP namespace | Reuse | MoeMemos Retrofit paths are relative and preserve `/memos/` base path |
| Exact-key resolver registration | Reuse with lifecycle correction | a versioned memo key fits；decoder must remain available for persisted blocks after API disable |
| Route auth composition | Minimal core evolution | peer auth moves to router dependencies；Memos composes public + PAT child routers |
| Hot enable/disable | Minimal core repair | one retained host route set，single writer，localized cache invalidation |
| Config update | Minimal generic repair | import `config_cls` while disabled；merge → validate → persist → live assign；remove stale config save on close |
| Mutable graph commands | Minimal generic primitives | caller-session edit/delete/relation operations；Memos traversal remains extension-owned |
| Memo query | Extension-owned query | no generic memo table/index；query canonical root blocks and graph predicates |
| Writable raw storage | New core capability | DB-backed put/get/delete is required by proven attachment journey |
| client-web config save | Cross-repo compatibility fix | current path mismatch blocks the existing JSON config editor |

## Exact MVP HTTP Surface

D-047 fixes the following bounded endpoint surface。Anything else remains unregistered and returns `404`；
it is not implemented as an empty success。

| Auth | Method and path under `/memos` | Required behavior |
| --- | --- | --- |
| public | `GET /api/v1/instance/profile` | version reports `0.29.1` |
| absent | `GET /api/v1/status` | `404` so MoeMemos selects v1 |
| PAT | `GET /api/v1/auth/me` | one stable deployment-scoped `users/inkcre` projection |
| PAT | `GET /api/v1/users/{id}/settings/GENERAL` | stable default visibility，initially PRIVATE |
| PAT | `GET /api/v1/memos` | NORMAL/ARCHIVED，exact creator filter，pageSize/pageToken，create-time-desc order；exclude comments |
| PAT | `POST /api/v1/memos` | create one independent memo root and attach referenced existing attachments |
| PAT | `PATCH /api/v1/memos/{id}` | explicit `updateMask` query semantics；otherwise D-034 body-key inference |
| PAT | `DELETE /api/v1/memos/{id}` | remove primary memo resource；owned cleanup follows D-046 |
| PAT | `GET /api/v1/attachments` | list attached and unattached resources visible in this deployment |
| PAT | `POST /api/v1/attachments` | streaming JSON/base64 upload；`memo` may be null |
| PAT | `DELETE /api/v1/attachments/{id}` | remove the primary attachment resource and attempt associated cleanup |
| PAT | `GET /file/attachments/{id}/{filename}` | authenticated raw bytes with content metadata；filename mismatch is `404` |
| PAT | `POST/GET /api/v1/memos/{id}/comments` | independent comment roots connected to parent |
| PAT | ordinary memo PATCH/DELETE | update/delete a comment by its memo resource name |

Protocol validation/auth/resource failures map to stable `400`/`401`/`404`；unexpected database、resolver
or storage failures return `500`。Memos routes should translate Pydantic request errors to protocol `400`；
the peer-authenticated core config endpoint keeps its ordinary `422` validation contract。

## Proposed Canonical and Graph Shape

D-042 confirms this exact CanonicalMemo v1 root content：

```json
{
  "body": "Markdown text",
  "created_at": "2026-08-01T12:00:00Z",
  "updated_at": "2026-08-01T12:00:00Z",
  "archived": false,
  "visibility": "private",
  "pinned": false
}
```

- `created_at` / `updated_at` remain nullable for the memo-family canonical contract，but backend-created
  memos always establish them；block timestamps remain info-base persistence time。
- `archived`、`visibility` and `pinned` are explicit memo facts needed for update/list/read round-trip。
  They have no independent identity，so the root is their only sensible authority。
- identity is `block.id`；generation is the resolver id，proposed
  `extensions.memos.memo.v1`；there is no content-level id/schema version。
- attachments、parent and references remain graph-only。Proposed predicates are root → attachment
  `attachment:<zero-based-order>`，comment → parent `parent` and memo → target `reference`。
- backend create uses explicit block creation，never resolver-content `fetchsert`：equal bodies are still
  different memos。

Attachment block content is a separate versioned memo-extension contract containing only stable metadata
and a storage pointer（for example blob id、filename、media type and decoded size）。Raw bytes do not enter
CanonicalMemo or attachment JSON。

## Writable Storage Decision

D-043 selects a generic PostgreSQL-backed binary storage：

- a small `storage_blobs`-like table owns only a generated pointer and `BYTEA` raw bytes；
- a built-in database-binary storage type/instance implements caller-session put/get/delete；
- the attachment block owns attachment identity and metadata，and points to that storage instance；
- one PostgreSQL transaction can cheaply cover raw bytes、block and relation where the implementation
  chooses；D-041 does not expose this as a completeness guarantee；
- decoded upload size is capped at 32 MiB for the MVP，matching the tagged server's fallback upload buffer
  when no instance-level limit is configured；the API streams base64 decoding rather than materializing
  multiple copies where practical。

This adds one table/migration but avoids the more expensive DB + filesystem compensation protocol。Inline
base64 would avoid a table only by bloating graph content and bypassing the storage abstraction，which is
the wrong owner boundary。The exact table name/columns remain implementation addresses for the Impact
Handshake。

## Main-Path and Failure-Branch Walkthrough

### Runtime and config

| Branch | Required outcome |
| --- | --- |
| extension import/config validation fails | no routes published；enable returns non-2xx；durable enabled state is compensated/converges disabled |
| route construction fails | retained host remains empty；no partial public/protected surface |
| enable called twice | second call is idempotent；no duplicate routes or resolver registrations |
| disable | unpublish exact route set first，then close runtime resources；all Memos routes become `404` |
| close fails after unpublish | remain fail-closed/unpublished；retain enough runtime state for idempotent cleanup retry，report non-2xx |
| re-enable | repopulate the same retained host once；decoder registry is not duplicated or retired |
| invalid config patch | schema validation before DB write；persisted/runtime values unchanged |
| config/update while disabled | import `config_cls` without publishing routes，validate/persist config，apply on next enable；persisting `config_schema` is optional UI work |
| DB config write fails | runtime value unchanged |
| process dies after config commit before assignment | restart reloads DB authority；the accepted narrow crash window is self-healing |
| extension closes | it must not persist its possibly stale runtime config over the DB authority |

Resolver decoders interpret durable blocks，so API disable must not unregister a decoder needed by existing
info-base content。Resolver artifact loading and live endpoint/source activation are separate lifecycle
concerns even if both remain coordinated by the extension package。

### Memo and query

| Branch | Required outcome |
| --- | --- |
| create same body twice | two root block ids；no content dedup |
| primary root mutation fails | non-2xx；D-041 permits residual component rows from attempted work |
| resolver unknown/invalid canonical JSON | explicit `500`/unsupported decoder failure；never fallback decode |
| list filter differs from exact deployment creator expression | `400`，not silently ignored |
| invalid/foreign page token | `400`；token binds version/filter/state and cursor |
| inserts occur between pages | opaque keyset cursor on `(created_at, block.id)` prevents shifting duplicates |
| comment exists | top-level memo list excludes roots with a `parent` relation；comment endpoint includes them |
| resolver relation read | incoming + outgoing uses OR/full star graph；direction cache cannot reuse an incomplete result |

No query projection/index is introduced in the MVP。For personal-scale data，resolver-key + canonical JSON
query and relation exclusion are sufficient；add an index only after measured pressure，because indexing is
an application/retrieval support concern rather than memo collection authority。

### PATCH, attachments and delete

| Branch | Required outcome |
| --- | --- |
| no `updateMask` | infer only from raw JSON keys；`false`、`""` and `[]` count as present |
| explicit `updateMask` | parse query value under 0.29.1 field-mask semantics；do not add inferred fields |
| empty/unknown/unupdatable mask | `400`，no mutation |
| attachment upload with `memo=null` | commit an independently addressable orphan attachment + raw bytes |
| later memo create fails | uploaded attachment remains valid/listable/deletable；do not call it partial memo graph |
| attach/reorder | request list is the complete set；rewrite positions with the simplest local DB operation |
| PATCH omits attachments | preserve current set；PATCH includes `attachments: []` deletes current owned attachments |
| raw write or graph mutation fails | return the exact non-2xx when the primary operation fails；orphan/raw/relation residue is permitted and diagnosable |
| attachment raw lookup missing/filename mismatched | `404` without altering graph |
| delete parent memo | root must disappear from memo list/read；attempt owned comment/attachment/raw cleanup；keep referenced memo targets |
| corrupted ownership cycle | visited-set traversal terminates and avoids over-deleting；cleanup residue is acceptable |
| repeated delete | `404`；no fabricated idempotent success unless exact upstream fixture proves otherwise |

An attachment has zero or one owning memo attachment relation in this MVP。Orphan is valid；multiple memo
owners are rejected。Reference relations do not imply ownership。

## Implementation Addresses and Blast Radius

### core-py

- `run.py` / `app/middleware.py`：peer auth dependency topology；public health/docs remain public。
- `app/business/extension/main.py`：retained route host、running map、disabled config validation、config
  update ordering、decoder/live lifecycle separation；private FastAPI invalidation localized here。
- `app/routes/extension.py`：generic patch-like config update behavior behind the existing management path。
- `app/database_contract/profile.py`：Memos artifact and database-binary storage catalog entries；remove
  duplicated built-in storage literals while touching that authority。
- `app/business/info_base/block.py` / `relation.py`：caller-session mutable primitives；relation OR/cache
  correctness。No Memos predicates in core managers。
- `app/business/info_base/storage/` + `app/schemas/info_base/`：writable database binary storage and raw
  bytes table/model。
- `extensions/memos/`：config、protocol DTO/adapter、service、canonical models、graph repository、resolver、
  query and attachment handling。
- `migrations/`：one storage migration；application-table manifest/readiness/migration tests updated。
- `tests/extensions/memos/` plus focused existing subsystem tests：pure、ASGI lifecycle and PostgreSQL
  integration evidence。

### client-web

- `packages/core/src/extension/base.ts`：send config updates to `/extensions/{id}/config` and test the
  request shape。This is a separate repo/change batch；it does not authorize shared-doc or core commits。
- a new SQL table also changes the generated database contract projection if client-web tracks the full
  application schema。

### durable/shared documentation

No durable doc is edited during this unit design。Accepted product/cross-unit/local/runtime truths continue
to accumulate in the program promotion packet and must later be applied by owner；Hub source edits、shared
ref bumps and Spoke implementation remain separate commits/workflows。

## Verification Readiness

- SVC 10.0.1 status is healthy；the worktree database target is ready，with a known profile and migration
  head。No environment mutation was needed for preflight。
- Existing pure pytest intentionally uses unreachable PostgreSQL and skips extension sync；new transaction
  tests must explicitly use the worktree-scoped PostgreSQL runtime or a disposable schema。
- Verification remains four distinct layers：pure contract tests、ASGI auth/lifecycle tests、PostgreSQL
  graph/storage/migration tests and the pinned MoeMemos APK evidence bundle。No layer substitutes another。

## Remaining Execution Gate

Technical、Acceptance and preflight are complete，but execution is not authorized yet：

1. Prepare/review the Impact Handshake for core-py、client-web、migration and later durable-doc state diff。
2. Sir explicitly says “开始”。

Any new evidence that changes owner、schema or observable behavior returns to its design gate；ordinary
symbol names and local implementation mechanics are resolved during the final Impact Handshake。
