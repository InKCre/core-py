# Memos Extension Backend MVP — Impact Handshake

> Prepared from the approved D-029–D-048 Execution baseline。This bounds implementation but does not
> authorize it；Sir must explicitly say “开始”。

## Address and Object

### core-py shared surfaces

- `run.py`、`app/middleware.py`：replace catch-all peer JWT enforcement with protected router-tree
  dependencies while retaining public health/readiness/docs surfaces。
- `app/business/extension/main.py`、`app/routes/extension.py`：default extension auth dependency hook，
  retained route-set hot publish/unpublish，running-state fixes and validated config update ordering。
- `app/database_contract/profile.py` and catalog/readiness tests：register the checked-in Memos artifact and
  PostgreSQL binary storage profile/instance without redesigning the artifact registry。
- `app/business/info_base/block.py`、`relation.py`、resolver internals：minimal caller-session mutation
  primitives，incoming/outgoing relation correctness and direction-safe resolver relation caching。
- `app/business/info_base/storage/`、`app/schemas/info_base/`：generic PostgreSQL binary storage and one
  raw `BYTEA` table/model。
- `migrations/`、metadata/application-table/readiness tests：one schema migration and exact catalog/schema
  projection updates。

### Memos extension owner

- new `extensions/memos/` checked-in artifact and metadata/config。
- family-owned CanonicalMemo、graph mapping/repository、application commands、versioned resolver and
  attachment handling。
- product-generation-owned Memos 0.29.1 wire models、mapping and backend routes。
- candidate dependency layout follows D-048 `family/` and `products/memos/v0_29_1/` boundaries；final
  filenames may tighten without changing ownership direction。

### Tests and external evidence

- new `tests/extensions/memos/family/` reusable canonical/graph/resolver contract tests。
- new `tests/extensions/memos/products/memos/v0_29_1/fixtures/` exact bounded wire/error fixtures and
  adapter tests。
- new `tests/extensions/memos/backend/` auth/route/config/lifecycle tests。
- new `tests/extensions/memos/integration/` PostgreSQL graph/storage/delete/residue tests。
- external pinned MoeMemos 2.0.4 APK runner/evidence bundle；no Android harness is invented inside core-py。

### client-web sibling repository

- `packages/core/src/extension/base.ts` and focused tests：change extension config save to
  `/extensions/{extension_id}/config`。
- generated database contract projection only if the accepted raw table is included in that repository's
  full application-schema type surface。

### Deferred documentation owners

- No Hub/shared/local durable documentation is edited in implementation batches。Approved task truth stays
  in the promotion queue until verified implementation evidence exists，then follows owner-specific Hub /
  shared-ref / Spoke-local workflows and separate commits。

## State Diff

1. **Auth**: global peer-JWT request gate → core/default-extension router dependencies + Memos public/PAT
   child-router composition。
2. **Extension runtime**: one-way/duplicating router inclusion and defective running membership → one
   retained route-set handle with idempotent hot enable/disable/re-enable and localized FastAPI cache
   invalidation。
3. **Extension config**: persist raw dict then validate → shallow merge、`config_cls` validation、normalized
   persistence、live assignment；disabled update imports the config class without publishing routes。
4. **Resolver lifetime**: decoder availability coupled to live API activation → installed decoder remains
   usable for persisted blocks after API disable。
5. **Graph primitives**: independently committing/incomplete mutation helpers → the minimum caller-session
   operations and correct full-star relation reads needed by the family service；no graph-completeness
   product guarantee is added。
6. **Storage**: read-only remote-pointer storage → generic PostgreSQL binary put/get/delete backed by one raw
   bytes table，while attachment identity/metadata remain in graph blocks。
7. **Product capability**: no memo backend → bounded Memos 0.29.1 backend for MoeMemos 2.0.4，including
   profile/auth/settings、list/create/PATCH/delete、attachments/raw download and comment fixtures。
8. **Client operator flow**: broken generic config request path → working peer-authenticated extension config
   save and hot apply through core API。

## Operation and Expected Side Effects

- Logic-altering refactor of auth routing and extension runtime lifecycle。
- New checked-in extension package and tests。
- Additive PostgreSQL schema migration and built-in storage catalog entry。
- Local correctness changes in relation retrieval/resolver caching and graph mutation APIs。
- Separate sibling-repo client-web request-path/test change。
- No commit、push、Hub edit、shared-ref bump or deployment mutation is implied by implementation start；each
  requires its normal scope/command discipline。

## Blast Radius Forecast

- Every core API route and ordinary extension route is sensitive to the auth topology move。
- All extensions are sensitive to default dependency、start/close and config-update changes。
- Existing resolvers are sensitive to relation query/cache corrections but should only gain the behavior
  their current interface already claims。
- Database schema/catalog/readiness and client-web generated types are sensitive to the raw table。
- Existing storages remain readable；only the new database-binary implementation is writable unless future
  pressure extends other storage classes。
- The new Memos semantics remain inside `extensions/memos`；flomo、collectors、organization、retrieval and
  complete Memos administration are outside the implementation blast radius。

## Invariants Check

- Core protected routes and ordinary extensions remain fail-closed under peer JWT；Memos PAT never authenticates
  them。
- Only Memos v1 instance profile is public；v0 status stays `404`；all other implemented Memos/file routes
  require the configured PAT。
- `/{extension_id}` remains the protocol namespace；no top-level mount or extension sub-app is added。
- No parallel Memos memo table/object store；CanonicalMemo remains root `block.content` and graph components
  remain relations/blocks/storage。
- Backend reads are resolver-mediated；product adapters do not interpret raw graph rows。
- Equal memo bodies remain distinct block identities；backend create does not use content fetchsert。
- Canonical generation is the resolver identity；payload has no local id/schema version/attachments/parent/
  references。
- D-041 remains explicit：success guarantees the primary mutation，not complete graph atomicity；residue is
  allowed and no compensation/replay subsystem is introduced。
- D-046 deletion never removes reference targets or components lacking proven exclusive ownership。
- D-048 seams leave room for flomo/collectors but no empty generic adapter registry、collector framework or
  speculative native DTOs are created。
- Indexing/query projections are not added to the memo collection authority。
- Existing unrelated worktree changes remain untouched。

## Verification

1. Pure family/product fixtures：D-042 serialization、D-044 graph mapping、resolver result、wire/error
   mapping、PATCH presence and cursor behavior。
2. ASGI：public/peer/PAT cross-auth matrix，OpenAPI/route availability，enable/disable/re-enable，config
   establish/read/replace/revoke/invalid update。
3. PostgreSQL：migration/catalog/readiness，BYTEA storage，graph/resolver queries，orphan attachments，
   ordered relations，best-effort deletion residue and no shared-target over-delete。
4. Repository：`pdm run lint`、`pdm run typecheck`、`pdm run test` and applicable migration checks。
5. client-web：focused request-path test and repository checks in the sibling repo。
6. External E2E：pinned APK tag/digest、desensitized HTTP transcript、committed graph snapshot、resolver
   output and client-visible login/sync/write/attachment behavior。

Each implementation increment reruns its focused tests plus earlier slice regressions；pure tests、ASGI、
PostgreSQL and APK evidence do not substitute for one another。

## Uncertainty

- FastAPI 0.139.2 route removal depends on private route-version invalidation；the helper is pinned and
  tested，but a future FastAPI upgrade must reopen it。
- Final raw-table/type/instance symbol names may change during implementation for local readability，without
  changing D-043 ownership or schema blast radius。
- The migration head may advance because of unrelated work before execution；generate against the then-current
  head rather than the preflight head。
- Existing extension behaviors may reveal an undocumented reliance on `on_close()` persisting mutated config；
  current search found no such writer。If found，return to design rather than silently discard it。
- client-web generated database types may be produced by an existing schema workflow instead of hand edits；
  follow that repository's local instructions during its separate batch。
- APK automation environment is external and still needs concrete runner setup；this does not change the
  bounded server contract。

## Entry Gate

- Product：approved。
- Technical：approved。
- Acceptance：approved as D-047 fixture contract。
- Execution baseline/preflight：complete。
- Impact Handshake：**approved by Sir**。
- Explicit start：**granted；Sir said “批准，开始”**。

Execution has entered I-01 under this approved state diff。Any newly discovered owner or observable behavior
outside this boundary must return to the corresponding design gate before implementation continues。
