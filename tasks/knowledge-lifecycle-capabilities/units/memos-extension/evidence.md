# Memos Extension — Backend MVP Evidence

本文只记录 backend MVP 可复核的版本锚点、MoeMemos 实际最小调用、core fit 证据和已知的
`updateMask` 偏差。产品/技术草案见 [design.md](design.md)，控制状态见
[unit packet](packet.md)，决定 authority 仍是 [decision register](../../decisions.md)。

## Version anchors

- **Protocol target**：Memos `v0.29.1`，官方 tag 指向 commit `5f194da`；
  [release](https://github.com/usememos/memos/releases/tag/v0.29.1)、
  [tagged memo proto](https://github.com/usememos/memos/blob/v0.29.1/proto/api/v1/memo_service.proto)。
- **Acceptance client**：MoeMemosAndroid `2.0.4`，官方 tag 指向 commit
  `9bfc6517f981a05b67ffcac20fe1a908e659f815`；
  [release/tag](https://github.com/mudkipme/MoeMemosAndroid/releases/tag/2.0.4)。
  release APK 为 `moememos-v2.0.4.apk`，SHA-256
  `5043f14d27c4cc283cb1507a23a84f251e159ab8d3937da9842f2060bd7fe8fa`；
  [APK asset](https://github.com/mudkipme/MoeMemosAndroid/releases/download/2.0.4/moememos-v2.0.4.apk)。
- MoeMemos `2.0.4` 的 release note 明确声明支持 Memos `0.27.0`–`0.29.1`；本单元取其中
  `0.29.1` generation，不把更高 generation 的 wire shape 混入首版。

## Actual minimum wire calls

以下集合来自 MoeMemosAndroid `2.0.4` 的 v1 Retrofit interface、repository 和 account
version detection，而不是完整 upstream API 的猜测（[client API source](https://github.com/mudkipme/MoeMemosAndroid/blob/2.0.4/app/src/main/java/me/mudkip/moememos/data/api/MemosV1Api.kt)、
[repository source](https://github.com/mudkipme/MoeMemosAndroid/blob/2.0.4/app/src/main/java/me/mudkip/moememos/data/repository/MemosV1Repository.kt)）。

这些 Retrofit annotations 使用不以 `/` 开头的 relative paths；`Retrofit.Builder.baseUrl(host)`
直接消费登录页保留 path 的 host。attachment URI 也在该 host 后追加 `file/...`。因此用户配置
`https://<deployment>/memos/` 时，请求分别落到 `/memos/api/v1/*` 与 `/memos/file/*`，可以直接
复用现有 extension namespace；此前把 annotations 中的 `api/v1` 误读为必须占用 server root，
已经撤回。

| Journey phase | Calls and required shape |
| --- | --- |
| Detect generation | `GET /api/v1/status` may fail; client then falls through to `GET /api/v1/instance/profile`. The profile version must identify supported `0.29.1`, and is fetched again before sync. |
| Authenticate | User supplies a Bearer token; client sends `Authorization: Bearer <token>`. `GET /api/v1/auth/me` resolves the user, then `GET /api/v1/users/{user}/settings/GENERAL` supplies default visibility. |
| Sync | `GET /api/v1/memos` for `state=NORMAL` and `state=ARCHIVED`, `pageSize=200`, repeated `pageToken`, and `filter=creator == "users/{username}"`; continue until `nextPageToken` is empty. |
| Memo writes | `POST /api/v1/memos`, `PATCH /api/v1/memos/{id}`, and `DELETE /api/v1/memos/{id}`. Core journey does not call `GetMemo`; MoeMemos reads detail from its local database. |
| Attachments | relative `GET/POST/DELETE api/v1/attachments...`，plus authenticated raw download by appending `file/{attachment-name}/{filename}` to the configured host path。Upload is streaming JSON with base64 `content` and nullable `memo`；With `/memos/` base，raw names become `/memos/file/attachments/{id}/{filename}`. |
| Deliberately absent from core set | Explore/users, comments, relations and reactions are not called by the APK core sync. Comments remain a packet-level semantic fixture, covered outside the APK gate. |

### Authentication-specific findings

- MoeMemos generation detection is unauthenticated and ordered。It first calls v0
  `GET api/v1/status`；a successful version-bearing response selects the v0 repository。Only failure falls
  through to v1 `GET api/v1/instance/profile`。The Memos extension must therefore leave `/api/v1/status`
  unimplemented (`404`) and publicly serve only the v1 profile，rather than implementing both detection
  endpoints。
- Memos 0.29.1 PATs use `memos_pat_` plus 32 cryptographically random alphanumeric characters，persist
  only a SHA-256 hash and may have no expiry。This proves the compatible token shape and lifetime；its
  multi-user storage boundary does not override InKCre's existing ordinary-config trust boundary or
  require copying upstream's PAT list、expiry or management APIs。
- The selected MoeMemos client treats the token as an opaque Bearer value，validates it with
  `GET /api/v1/auth/me` and attaches it to same-origin attachment downloads。

Memos v0.29.1 本身提供 `GET/POST /api/v1/memos/{memo}/comments`；comment response 仍是 Memo，
后续 update/delete 复用普通 memo endpoints（[tagged proto](https://github.com/usememos/memos/blob/v0.29.1/proto/api/v1/memo_service.proto)）。
因此 comments 可以作为明确的 protocol fixture 实现，同时诚实地标记为 MoeMemos APK 不覆盖。

## Core fit evidence

- Current JWT authenticates InKCre peer deployments; request state has no Memos terminal-user
  principal or PAT owner ([JWT contract](../../../../app/middleware.py#L24-L64)、[middleware gate](../../../../app/middleware.py#L141-L181))。
  `ClientModel` is a peer deployment, not a Memos user ([model](../../../../app/schemas/client/main.py#L13-L18))。
- Blocks and relations have no owner/tenant field ([block](../../../../app/schemas/info_base/block.py#L18-L53)、
  [relation](../../../../app/schemas/info_base/relation.py#L10-L41))。Multi-user Memos therefore needs
  separate identity, token, ownership, visibility and ACL authority; adding endpoints alone is insufficient.
- Native Memos data must map to `CanonicalMemo` root content plus component blocks/relations;
  a parallel Memos memo object store would violate the graph authority boundary.
- Memo, attachment, comment and relation changes need one explicit application-service coordinator so
  convenience paths do not silently choose business order。D-041 does not require a single transaction or
  a no-partial-graph guarantee。

## Implementation-address audit

以下是为 implementation-plan probe 做的本仓只读核验；它们说明 plan pressure，不自动决定
最终方案：

### Extension host and authentication

- [`ExtensionBase.on_start`](../../../../app/business/extension/main.py) always creates
  `APIRouter(prefix=f"/{extid}")` and only then calls extension `_register_apis`。For ext id `memos`,
  this produces the intended `/memos/...` namespace；MoeMemos can select it through its pathful base
  URL, so no root-route exception is required。
- Extension routes are added only when an installed extension is enabled and runtime bootstrap starts
  it；current disable/close never removes them。Pinned FastAPI 0.139.2 keeps an included child
  `APIRouter` as a live route branch and versions its effective-route/OpenAPI caches。It has no public
  symmetric remove API，but a retained child router can be cleared/repopulated if the runtime host also
  performs the required version invalidation；this framework-specific operation must stay localized。
- A disposable FastAPI 0.139.2 in-memory probe confirmed this exact branch：a route added to a retained
  child after inclusion became dispatchable；clearing the child plus `_mark_routes_changed()` removed both
  dispatch and OpenAPI output。This is pinned-framework evidence，not a public API guarantee。
- `RUNNING_EXTENSIONS` is keyed by ext id, but current `start/close` membership checks use the
  extension class。This makes duplicate start and ineffective close a confirmed local defect, not a
  product-design alternative。
- [`JWTMiddleware`](../../../../app/middleware.py) runs before route handlers and accepts only canonical
  peer JWT claims。A Memos Bearer token cannot be implemented solely inside the extension handler；
  D-036 therefore replaces the catch-all gate with route-tree dependencies；D-039 defines the
  Memos PAT/config contract and exact public subset。
- Extension `config` and `config_schema` are JSONB and the ordinary extension endpoints return config。
  Existing configs already carry recoverable Twitter password/TOTP、Telegram bot token、IMAP password
  and GitHub token values；there is no current system-wide hidden-secret config boundary。
- client-web passes `config_schema` to its JSON editor，but the editor also works without a schema；core can
  import the extension `config_cls` when updating a disabled extension。Persisting schema before enable is
  therefore optional UI metadata，not a PAT lifecycle requirement。
- Current external config update passes the raw dict directly to `save_config()`，which persists before
  runtime validation；`ExtensionBase.on_close()` also uses the same persistence method。A config update
  therefore needs validation before commit。The existing extension `config_cls` is sufficient；the
  evidence justifies a shared update ordering，not Memos-specific transform/projection hooks。
- Current client-web reads extension rows/config directly from the database and its config update path is
  `/{extension_id}/config`，while core-py's management route is `/extensions/{extension_id}/config`。The
  Memos PAT can follow that same trusted-config boundary。The existing generic editor still cannot be
  claimed as a working Memos credential UI until its path and update behavior match the management
  contract。

### Graph, resolver and storage

- [`BlockManager.fetchsert`](../../../../app/business/info_base/block.py) uses resolver equality and then
  performs synchronous embedding work in the caller's session。Default resolver equality is
  `(resolver, content)`，which would merge two independently-created identical memos；backend create
  must not use content dedup as identity。
- `BlockManager.create` can flush in a caller session, but `edit_block` owns and commits a new session；
  `RelationManager.create` also commits independently, and no block/relation delete API exists。
  `InfoBaseManager.add_subgraph_to_session` proves caller-owned graph transactions are possible, but
  mutable memo commands need bounded session-aware primitives/application orchestration。
- `RelationManager.get` combines incoming/outgoing filters with `AND` when both are requested, and
  resolver relation results are cached without a direction-specific key。Memo resolver cannot assume
  two arbitrary direction calls reconstruct a complete graph without a query correction/explicit
  one-shot classification。
- Current [`Storage`](../../../../app/business/info_base/storage/main.py) contract only reads raw
  content；built-ins fetch remote URLs。There is no upload, raw file persistence, delete or file-serving
  contract, and no existing multipart/upload route。This is direct evidence behind D-043。
- Relation FK cascade removes relation rows when a block is deleted, but does not delete component
  blocks or backing raw content。Owned subtree cleanup therefore cannot be inferred from database FK
  behavior。

### Verification environment and blast radius

- Ordinary [`tests/conftest.py`](../../../../tests/conftest.py) uses an unreachable Postgres URL and
  `SKIP_EXTENSIONS_SYNC=1` so pure tests remain hermetic。Transaction/FK/JSONB/runtime route proof needs
  a disposable PostgreSQL integration fixture rather than SQLite or existing pure tests。
- Adding a new SQLModel table affects schema discovery, Alembic metadata/revision, the exact
  application-table manifest/readiness tests, and the client-web database contract projection。The
  D-043 PostgreSQL raw-storage decision therefore makes this a known blast radius，not an
  implementation-time surprise。
- No Android/Gradle/ADB/MoeMemos harness exists in core-py。APK compatibility must be executed in an
  external controlled runner and retained as an evidence bundle；ASGI `TestClient` remains necessary but
  is not sufficient。

## Known `updateMask` deviation

- Memos `v0.29.1` declares `update_mask` required in `UpdateMemoRequest` and the server rejects a
  nil or empty mask ([proto](https://github.com/usememos/memos/blob/v0.29.1/proto/api/v1/memo_service.proto#L2067-L2077)、
  [implementation](https://github.com/usememos/memos/blob/v0.29.1/server/router/api/v1/memo_service.go#L3005-L3018)).
- MoeMemos `2.0.4` serializes `UpdateMemoRequest` with only nullable memo fields and sends no
  `updateMask` ([request model](https://github.com/mudkipme/MoeMemosAndroid/blob/2.0.4/app/src/main/java/me/mudkip/moememos/data/api/MemosV1Api.kt#L97-L106)、
  [update call](https://github.com/mudkipme/MoeMemosAndroid/blob/2.0.4/app/src/main/java/me/mudkip/moememos/data/repository/MemosV1Repository.kt#L146-L164)).
- Strict upstream behavior therefore breaks the selected client's edit journey. The compatibility
  shim is therefore a deliberate deviation (D-034): infer paths from raw JSON key presence when the
  mask is absent, while accepting an explicit valid mask under upstream semantics. This shim is not
  strict Memos parity.
- The tagged HTTP annotation declares PATCH `body: "memo"` while `update_mask` is a sibling request
  field。Therefore an explicit REST mask belongs to the `updateMask` query parameter，not the JSON body。

## Attachment order and unattached lifecycle

- Tagged Memos 0.29.1 `setMemoAttachmentsInternal` treats the request attachment list as the complete set，
  deletes omitted owned attachments，reverses the normalized request and assigns increasing `updated_ts`。
  The store then lists attachments by `updated_ts DESC`。This deliberately reconstructs the original
  request order，so D-013's “preserve only when source-defined” condition is met for this adapter（D-040）。
- MoeMemos uploads resources before memo create/update。For a new memo its `remoteId` is null，so
  `POST /api/v1/attachments` carries `memo=null`；only after uploads succeed does `POST /api/v1/memos`
  carry attachment names。A successful upload is therefore an independently committed、listable、deletable
  resource even if the later memo create fails。
- In this protocol generation an attachment can be unattached or owned by one memo。PATCH attachment
  arrays are set semantics，not append semantics；`attachments: []` is observably different from omission。
- The tagged server uses a 32 MiB upload buffer as its fallback when no instance-level maximum is
  configured；the value is not a protocol-wide immutable limit。The MVP may select the same fixed cap
  because it intentionally excludes the administration/settings surface。
