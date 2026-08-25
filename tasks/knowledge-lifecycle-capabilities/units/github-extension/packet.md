# GitHub extension

## Control

- **State**: **Candidate to resume for correction closure**。The first implementation merged through core-py PR #80 after
  the independent ownership correction was removed from its diff；the batch persistence and PyGithub corrections below are
  still outstanding and the unit is not complete。
- **Program owner**: [knowledge lifecycle capabilities](../../packet.md) remains the only program control authority；this
  file is the GitHub unit's design、preflight、implementation and acceptance record。
- **Blocking predecessor**:
  [`extension-ownership-correction`](../../../extension-ownership-correction/packet.md) has merged through Hub PR #18 and
  core-py PR #82，but its exact-main production delivery is blocked by a manifest-verifier execution-boundary regression。
  Resume only after that delivery closes。
- **Resume point**: correct symmetric graph batch persistence and replace the handwritten GitHub transport with the retained
  PyGithub client，then repeat the real-account acceptance and close the existing PRs。

## Outcome and MVP boundary

Preserve the `github-extension` identity but treat its current implementation as requirements and failure evidence rather
than an incremental foundation。The MVP synchronizes one configured GitHub account's current Stars and GitHub Lists into
reusable info-base graph facts，including each List's Repository membership。

- One Source represents one configured GitHub access context。
- Source configuration contains the access token only；the API determines the authenticated account and visible data。
- Ordinary collect performs a complete current-snapshot reconciliation of Stars、Lists and List memberships。
- There is no `full` mode、backfill command、cursor or collected-item ledger。
- Token visibility is authority；the Source does not add an `include_private` policy。
- Blocks previously collected are preserved when remote membership disappears。The Source removes only graph facts that its
  complete current snapshot has denied。
- Specialized client-web presentation is out of the MVP unless preflight finds a concrete acceptance blocker。

## Canonical graph

`GitHubAccount` is the single canonical account/owner entity。Its `kind` distinguishes a user from an organization；the
authenticated viewer is a role expressed by provenance，not a second Block type。

```text
Source --collects--> GitHubAccount(kind=user)
GitHubAccount --stars--> GitHubRepository
GitHubAccount --owns--> GitHubList
GitHubList --contains--> GitHubRepository
GitHubAccount(kind=user|organization) --owns--> GitHubRepository
```

Canonical contents：

- `GitHubAccount`: `node_id`、`database_id`、`kind`、`login`、`name`、`url`、`avatar_url`。
- `GitHubRepository`: `node_id`、`database_id`、`name_with_owner`、`description`、`url`、`homepage_url`、
  `primary_language`、`topics`、`is_private`、`is_archived`。
- `GitHubList`: `node_id`、`name`、`description`、`slug`、`is_private`。

Membership、ownership and provenance exist only as Relations。Volatile counters、repository activity timestamps and
`starred_at` are excluded from the MVP。GraphQL `node_id` is exact identity；`database_id` is retained native metadata，not
an identity fallback。Proposed resolver IDs are：

- `extensions.github.account.v1`
- `extensions.github.repository.v1`
- `extensions.github.list.v1`

## Technical topology

```text
GitHub Source
  -> GitHubGraphQLAdapter.fetch_snapshot(token)
       -> authenticated viewer
       -> paginated starredRepositories
       -> paginated viewer.lists and each list.items
  -> GitHubGraphRepository.reconcile(source, complete snapshot)
       -> SourceManager.ensure_block(source)
       -> locate/create/update canonical Blocks by node_id
       -> reconcile current Relations
       -> remove snapshot-denied GitHub-owned Relations
```

- The Adapter owns GitHub GraphQL requests、pagination and conversion into canonical facts。It does not know Block、Relation
  or persistence。
- The Source owns collection orchestration and Job-visible diagnostics。
- `GitHubGraphRepository` owns GitHub graph grammar、exact identity reconciliation and relation-set replacement。
- Resolvers own canonical Block serialization、rooted graph drafting and use-time solved/text/label projections。The Repository
  calls their `create_block()` methods instead of duplicating content construction；Source-only snapshot deletion and
  reconciliation do not move into Resolver。
- Fetch the complete remote snapshot before persistence。Apply reconciliation in one database transaction so a failed page
  cannot be interpreted as an authoritative empty remainder。
- Reuse the Source anchor、Managers and caller-owned session patterns already established by Mail/RSS。
- `GraphForm` remains the arbitrary graph producer command，but is not forced onto locate/update/delete reconciliation；the
  repository uses the existing Block/Relation Managers within one session。
- Removing a remote List removes the viewer-to-List `owns` Relation and that List's `contains` Relations while preserving the
  List Block。

## Acceptance baseline

Use the configured real GitHub account as authority。Keep acceptance manual or script-driven unless repeated value later
justifies promotion to an automated test。

1. Query the live GitHub GraphQL API for the authenticated account's complete Stars、Lists and List memberships。
2. Dispatch an ordinary Source collect through the real Job boundary。
3. Compare persisted `node_id` sets and membership Relations with the live snapshot。
4. Collect again and verify that no duplicate canonical Blocks or Relations appear。
5. Make one explicitly authorized、reversible remote Star or List-membership change，collect again，and verify both addition
   and removal reconciliation。
6. Recover a sample path through graph navigation：`Source -> Account -> List -> Repository`。

Exact iteration order is not an acceptance contract。Acceptance must not introduce fixture-shaped implementation behavior。

## Preflight findings

### External contract and scale

- Live authenticated GraphQL inspection confirmed `viewer`、`starredRepositories`、`viewer.lists`、`UserList.items` and the
  accepted Account/Repository/List fields。The current acceptance account has hundreds of Stars、tens of Lists and hundreds
  of memberships；at least one List exceeds one 100-node page。
- Every connection therefore owns its own cursor。The Adapter must page Stars、Lists and oversized List items until
  `hasNextPage == false`；a partial page sequence never reaches reconciliation。
- GitHub GraphQL can return a response body containing `errors` and partial `data`。The Adapter treats any GraphQL error as a
  failed snapshot instead of interpreting omitted members as remote deletion。
- The expected request count and in-memory snapshot are small relative to the existing five-minute ordinary Source Job；no
  streaming persistence、sleep-based throttling or new retry lifecycle is justified。

### Reuse and ownership

- RSS confirms the desired split：Resolver owns canonical Block/StarsGraph construction and use projection；Repository owns
  transactional reconciliation。Twitter places the reusable rooted producer directly on its Resolver。GitHub will follow
  that seam rather than making its Repository a second serializer。
- `GitHubAccountResolver`、`GitHubRepositoryResolver` and `GitHubListResolver` each provide `create_block()`、a rooted
  `create_graph()` where meaningful、exact `node_id` lookup、solved content、text and resolver-qualified label。
- `GitHubGraphRepository` uses those Resolver forms but owns set replacement for `collects`、`stars`、List ownership/List
  membership and repository ownership。These source synchronization semantics are not promoted into generic Managers。
- `StarsGraphForm` is still useful for reusable rooted resolver output，but a complete snapshot is not forced into one tree：
  shared Repository nodes make that representation duplicate branches。The Repository coordinates the canonical shared graph
  through one caller-owned session。

### Runtime, release and persistence impact

- Preserve the public Source type identity `extensions.github.stars.Source`。Remove the extension-specific `/github/stars`
  convenience route；generic Source creation/configuration and the ordinary `core.source.collect.v1` Job are canonical。
- Retain the already-adopted PyGithub dependency and use its supported GraphQL requester。The Source may bridge its synchronous
  client through `asyncio.to_thread()`；InKCre continues to own queries、nested pagination orchestration、canonical mapping and
  snapshot completeness，but does not reimplement GitHub authentication、HTTP transport、retry or protocol error handling。
- The behavior rewrite is a new GitHub extension release，expected `0.2.0` with Changie release intent、generated changelog
  entry and wheel/distribution verification。
- Source config becomes `{github_token}` and collect config becomes the existing empty command model。The Extension runtime
  publishes these schemas from its Source class。The database contract must not describe this or any other Extension Source
  type as built-in；existing Extension entries in `BUILTIN_SOURCE_TYPES` are a pre-existing ownership defect to remove。
- Source state retains only the accepted authenticated Account `node_id` binding。Changing a token may refresh credentials for
  the same Account；a contradictory Account identity does not silently rebind the Source。
- Resolver IDs hard-cut to `.account.v1`、`.repository.v1` and `.list.v1`。Existing legacy `.user.v1`/`.repo.v1` Blocks are
  not migrated or treated as canonical matches。

### Failure-branch simulation

| Branch | Intended effect |
| --- | --- |
| HTTP、auth、GraphQL error or any incomplete pagination | Job fails；database graph and Source binding remain unchanged |
| Complete snapshot with removed Star | Delete the exact Account `stars` Repository Relation；preserve Repository Block |
| Complete snapshot with deleted List | Delete Account `owns` List and that List's `contains` Relations；preserve List/Repository Blocks |
| Repository metadata changes | Update canonical Repository content in place；Block timestamp invalidates derived retrieval records |
| Repository transfers owner | Replace the GitHub Account `owns` Repository fact；preserve Repository identity by `node_id` |
| Same Source token rotates but viewer is unchanged | Accept and reconcile normally |
| Same Source token resolves to another Account | Reject the collection before graph mutation；do not silently rebind |
| Repeated identical snapshot | Reuse Blocks/Relations and report unchanged results |
| Concurrent runs of the same Source | Serialize reconciliation by locking the Source row；the later complete snapshot converges |
| Multiple Sources resolve to different Accounts | Independent Source anchors and Account-owned fact sets |

### Planned source surfaces

- `extensions/github/schema.py`: canonical API facts and complete snapshot models。
- `extensions/github/adapter.py`: async GitHub GraphQL client and connection pagination。
- `extensions/github/resolver.py`: the three exact decoders、producer forms and use projections。
- `extensions/github/repository.py`: one-session exact identity and relation-family reconciliation。
- `extensions/github/stars.py`: thin Source orchestration、binding check and Job report。
- `extensions/github/__init__.py`: resolver/source publication；remove the obsolete convenience route。
- `extensions/github/{pyproject.toml,README.md,CHANGELOG.md}`、`.changes/github/**`: dependency、user contract and release
  intent。
- `app/database_contract/profile.py`: remove Extension-contributed Source types from the built-in catalog；Extension runtime
  publication remains the only schema owner。
- Root `pyproject.toml`/`pdm.lock` and the GitHub wheel retain PyGithub rather than introducing a handwritten GraphQL client。
- Extension-specific product and technical truth belongs in a local GitHub Extension Unit TDD/README。The proposed Hub GitHub
  capability/claim/reference integration is rejected；the wider pre-existing Memos/RSS/Mail Hub ownership needs a separate
  correction review rather than being expanded by this unit。

### Verification plan

- Static/repository gates：format、lint、typecheck、lock、extension release contract、GitHub wheel build and distribution
  verification，then the repository `pdm run check` gate。
- Script/manual black-box journey：real extension runtime + real GitHub GraphQL + ordinary Job + database graph comparison +
  replay + one authorized reversible remote delta + graph-navigation path。
- Do not add schema/helper/unit tests merely to mirror mappings or control flow。Promote no acceptance automation in this unit。

## Accepted duplicate-Source boundary

Two different Source instances can authenticate as the same GitHub Account while their token scopes expose different subsets。
The canonical graph currently has one Account and unqualified `stars`/`contains` facts，so a complete snapshot from either
Source cannot both own deletion independently。Adding Source IDs to Relation content would preserve observer provenance but
pollute canonical membership facts and produce duplicate graph edges；duplicating Account Blocks would abandon exact external
identity；enforcing one Source per Account adds a restriction and collision machinery。The accepted MVP deliberately adds no
special mechanism：the last successfully reconciled complete snapshot is the Account's current observed fact set，and the
acceptance journey uses one Source for the Account。

## Durable projection correction

- GitHub Stars/List behavior、canonical graph and acceptance evidence are GitHub Extension truth，not a Hub product capability
  merely because the Extension is first-party or important。They belong in a local Unit TDD/README。
- Hub retains only genuinely cross-unit product truth such as generic collection、info-base authority and Extension-based
  capability growth。Memos、RSS、Mail、GitHub and other concrete Extensions do not own Hub capability、claim or normative
  contracts；their names may appear only as explicitly non-normative implementation examples。
- Docs PR #18 and the core-py shared-ref commit must not merge in their current form。

## Accepted design reasoning

- Stars and Lists are current collections，not an event stream；complete snapshot reconciliation is therefore ordinary
  collection rather than `full` or backfill semantics。
- The info-base retains collected entities while Source-owned Relations express changing remote membership。
- A user that owns repositories must not become both a `GitHubAccount` and a `GitHubOwner` Block。One canonical account entity
  plus a `kind` field removes that duplicate identity；Relations express its roles。
- Fetch-before-apply makes completeness an Adapter/Source boundary and keeps partial remote observations from destructively
  shaping the graph。

## Implementation and acceptance evidence

- Implemented the three canonical Resolvers、an async GraphQL Adapter、a thin ordinary-collect Source and transactional
  current-snapshot reconciliation。The public Source identity remains `extensions.github.stars.Source`；the obsolete
  extension-specific route and PyGithub dependency are gone。
- Real-account preflight found that GitHub Lists are not necessarily a subset of Stars。The Adapter therefore resolves
  list-only Repository node IDs in bounded GraphQL batches instead of dropping memberships or embedding an oversized nested
  Repository query in each List page。
- Remote PostgreSQL acceptance exposed per-entity `flush + refresh` as an unacceptable persistence round-trip multiplier。
  `BlockManager.create_many()` and `RelationManager.create_many()` now provide caller-owned batch persistence while the
  GitHub Repository retains all identity and reconciliation semantics。
- A disposable Neon branch was migrated from the declared preview baseline to revision `50b2c08dd267` before running the
  real ordinary Job journey。The live authority contained 473 Stars、19 Lists、395 memberships and 474 unique Repositories。
- First collection created 942 GitHub canonical Blocks and 1,362 managed Relations。The replay reported zero created、updated
  or deleted Blocks/Relations。The journey also recovered `Source -> Account -> List -> Repository` through graph-navigation
  retrieval and exercised Repository label/text projections。
- The real reversible remote-delta step remains intentionally unperformed：the complete set and idempotent replay establish
  the implementation baseline without mutating the Human's GitHub account。It is a closure option，not hidden automated
  coverage。

## Review correction baseline

The first implementation passed its observed data journey but review rejected four design decisions。Passing acceptance does
not override an incorrect ownership or abstraction boundary。

1. **Batch graph persistence**：remote PostgreSQL proved that per-entity `flush + refresh` is too expensive，but adding
   leaf-level `create_many()` methods without routing existing graph insertion through them created an adjacent interface。
   Keep symmetric `BlockForm[]` / `RelationCreateForm[]` persistence primitives，make `InfoBaseManager.submit_graph()` consume
   them，and document why reconciliation cannot be represented as a pure-new `GraphForm` command。`StarsGraphForm` remains the
   resolver-rooted identity-aware path。
2. **Built-in versus Extension**：checked-in、first-party and enabled-by-default do not make an Extension contribution a core
   built-in。`BUILTIN_SOURCE_TYPES` currently contains GitHub、Mail、RSS、Telegram and Twitter Source types；the Extension
   runtime already publishes Source schemas and is their correct owner。Remove the whole incorrect category rather than only
   reverting GitHub's entry。
3. **Hub versus Extension-local truth**：importance and successful delivery are not promotion criteria。GitHub-specific PRD
   capability/claim and Product TDD reference integration were written to the wrong owner。Audit the same historical promotion
   for Memos、RSS and Mail，then retain their protocol/product contracts in Extension-local Unit TDDs。
4. **Protocol client ownership**：the preflight failed to inspect the already-installed PyGithub release。PyGithub 2.9.x
   supports GraphQL queries、mutations、GitHub error handling and pagination；a custom `httpx` GitHub GraphQL transport is
   unjustified。Use the mature dependency and keep only source-specific snapshot orchestration and mapping。

### Root cause and preventive guidelines

- The repeated failure is **promotion bias**：current vertical pressure was treated as permission to move behavior into a more
  public、durable or core-owned layer without proving its owner、consumers、lifecycle and reuse value。
- Before promotion，name four independent axes：delivery owner（core/Extension）、durable owner（Hub/Spoke）、interface layer
  （domain command/persistence mechanism）and external capability owner（existing dependency/InKCre）。A decision on one axis
  is not evidence for another。
- Before implementing an external protocol client，inspect current dependencies and primary documentation，then record the
  exact unsupported behavior that remains。Handwritten transport is allowed only after that gap is demonstrated。
- A vertical acceptance proves observable behavior；it cannot legitimize a wrong module or documentation owner。
- Ponytail's ordered ladder is now the default implementation check：need → existing code → stdlib → native platform →
  installed dependency → minimum new code。It shortens the solution only after end-to-end ownership is understood。

### Superseded paused delivery state

- Hub PR #18 was rewritten and merged as the independent ownership correction；core-py PR #80 was rebased onto core-py
  PR #82 and then merged with only the first GitHub implementation。
- Corrective source work still requires a newly frozen execution baseline and Sir's explicit “start”。

## Accepted correction execution baseline

### Durable ownership correction

1. Verify that each concrete Extension's local Unit TDD/README retains a readable normative home before removing duplicate Hub
   truth；add a local GitHub Extension Unit TDD for the accepted graph、snapshot and reconciliation contract。
2. Turn Hub PR #18 into an ownership-correction PR：remove concrete Memos、RSS、Mail and GitHub capability/claim/reference
   contracts from PRD/Product TDD。Concrete names may remain only where clearly marked as non-normative implementation examples。
3. Push the corrected Hub source first，then update core-py's `docs/_shared` ref in its own commit。Do not merge the current
   shared-ref commit unchanged。

### Runtime catalog correction

1. Remove every Extension Source profile from the core database contract，including GitHub、Mail、RSS、Telegram and Twitter。
2. Because no true core built-in Source type remains，delete rather than preserve an empty speculative catalog/fallback where
   callers prove it has no other consumer。Extension activation remains the only Source schema publication path and uses the
   Source class description/config/collect/backfill schemas。
3. Verify database init/readiness and Extension cold restore without requiring disabled or unavailable Extension Source rows。

### Graph insertion correction

1. Keep symmetric caller-session batch persistence primitives：`BlockForm[] -> BlockModel[]` and
   `RelationCreateForm[] -> RelationModel[]`，each with one flush and no per-row refresh。
2. Route `InfoBaseManager.submit_graph(GraphForm)` through those primitives：insert the new Blocks as one batch，resolve signed
   local IDs，then insert Relations as one batch。Single-item creation should reuse the same primitive where doing so shortens
   rather than duplicates persistence behavior。
3. Keep `add_stars_graph_to_session()` as resolver-rooted identity-aware fetchsert。GitHub snapshot reconciliation continues to
   use batch primitives directly because it locates、updates、preserves and deletes existing graph facts，while `GraphForm` is
   a producer command for inserting a caller-declared graph。
4. Record this distinction in the existing local `business-pipeline-and-authority.md` and the public method docstrings；do not
   create another graph abstraction or document。

### GitHub protocol correction

1. Restore the existing PyGithub dependency in the root and GitHub wheel。Use public `Github.requester.graphql_query()` for
   GitHub authentication、transport、retry and GraphQL error handling，bridged from the async Source through
   `asyncio.to_thread()`。
2. Retain only a source-specific snapshot adapter：queries、nested connection pagination、complete-snapshot checks、list-only
   Repository resolution and canonical fact mapping。It is not a general GitHub GraphQL client。
3. Remove the handwritten `httpx` execution/error layer and its dependency delta。Do not add githubkit/gql while the already
   installed PyGithub covers the demonstrated boundary。

### Verification and delivery

- Re-run static/lock/release/wheel gates and the real GitHub ordinary Job + exact graph comparison + idempotent replay journey。
- Add no helper/unit tests；the existing manual script remains non-durable acceptance tooling。
- Update the two existing PRs rather than opening replacement PRs。Keep Hub、core implementation and shared-ref commits
  separable for review。

### Correction Impact Handshake

- **Exact objects**：Hub PRD/Product TDD concrete Extension sections；local Extension Unit TDDs；Source database-contract
  profiles and runtime publication；InfoBase batch/GraphForm insertion；GitHub snapshot adapter/dependencies；PR #18/#80。
- **From -> To**：importance-based promotion -> owner-based placement；Extension schemas in core built-ins -> runtime
  Extension publication；adjacent batch APIs -> shared persistence primitives beneath existing graph commands；handwritten
  GraphQL client -> PyGithub-backed source adapter。
- **Side effects**：database initialization no longer seeds Extension Source types before activation；disabled Extensions do
  not leave their Source catalog as artifact-owned truth；Hub diff becomes a net deletion/normalization；GitHub collection
  remains behaviorally equivalent。
- **Blast radius**：core-py database init/readiness、all first-party Source Extensions、InfoBase graph producers、GitHub wheel
  and lock、Hub shared docs and shared ref。No client-web runtime or database schema migration is expected。
- **Invariants**：Extension activation publishes complete Source schemas；GraphForm signed references resolve exactly；snapshot
  errors never become deletion authority；canonical Blocks/Relations and accepted Job report remain unchanged；one durable
  owner per fact。
- **Verification**：repository gate、extension release/wheel verification、database reset/readiness、Extension activation
  catalog inspection、real-account GitHub journey、Hub/submodule checks and final PR diff review。
- **Uncertainty**：PyGithub raw GraphQL pagination still requires source-owned nested orchestration，but primary docs and the
  installed 2.9.x API prove transport/error support。Historical Hub removal may expose a missing local Extension contract；the
  pre-delete owner check resolves that without retaining duplicate Hub truth。
