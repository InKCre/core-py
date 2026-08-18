# Graph Navigation Retrieval Implementation Plan

## Status

- **Baseline**: Product / Technical contract and Acceptance are accepted for implementation planning.
- **Mutation state**: no governed source has been changed for this unit yet.
- **Execution shape**: owner-separated increments with public-contract evidence after each meaningful vertical；no large
  cross-repository atomic commit is attempted.

## Runtime topology

```text
caller
  -> GraphNavigationRetrievalManager
       -> peer-local Block / Relation query primitives
       -> endpoint-closure assembly
       -> bounded bidirectional BFS when path is requested
  -> GraphModel / operation-specific outcome

client-web InfoBase View
  -> @inkcre/core local manager over PostgREST
  -> scene merge + Resolver preview loading
  -> measured layout + camera realization
  -> modeless route outlets
```

The Python and TypeScript managers are equal implementations of one use-domain contract. Neither calls the other，uses Peer
delegation，or introduces an HTTP/database RPC. Retrieval never owns preview、layout、camera or route state.

## Increment G0 — shared read contract and query foundations

### Hub owner

- Add one Product-TDD contract projection for graph-navigation retrieval plus a machine-readable topology corpus adjacent to
  it. The JSON owns topology aliases、directed Relations、scenario inputs and semantic result assertions；it does not own row
  IDs or one arbitrary equal-shortest path.
- Apply through the shared-doc workflow；Spokes only consume the resulting shared ref in owner-separated commits.

### core-py owner

- Add read-only `GraphModel` and operation-specific neighborhood/path models under `app/schemas/`，separate from producer
  `GraphForm`.
- Add singular random Block access and bounded Relation query primitives. Remove `BlockManager.iterate_from_block()` rather
  than preserving it behind the new manager.
- Add endpoint indexes `(from_, id DESC)` and `(to_, id DESC)` through one Alembic migration. Do not add a content index until
  query evidence justifies it.

### client-web `@inkcre/core` owner

- Add matching Zod/TypeScript read models and peer-native query primitives over PostgREST.
- Add `Block.getRandom()` using count + stable-order random offset；never transfer all Block IDs to choose one.
- Keep existing broad Active Record methods only where current consumers still require them；the retrieval manager must not
  implement its contract by `getAll()`.

### Proof

- migration upgrade from current clean baseline；catalog inspection proves both endpoint indexes；static/schema checks prove
  write `GraphForm` and read `GraphModel` remain distinct.
- shared corpus loads unchanged in Python and TypeScript runners.

## Increment G1 — core-py public manager

- Create `app/business/graph_navigation_retrieval/` as the use-domain owner.
- Implement `get_block_neighborhood()` as direction-specific ordered Relation reads followed by a manager-owned ID-desc merge
  and batched endpoint lookup. `both` performs one bounded incoming and one bounded outgoing read，then returns the merged
  `limit + 1` page；this preserves the public incident-page abstraction while allowing each branch to use its endpoint index.
  Omit Relations whose endpoints no longer resolve so every successful result is endpoint-closed.
- Implement `get_relation_neighborhood()` as Relation + exact endpoints or no result.
- Implement bounded bidirectional BFS for `find_path()` with direction and exact-content pruning during traversal，not after
  materializing a broad graph. Assemble and revalidate persisted rows only after a candidate path is found.
- Use the accepted `PathFound | PathNotFound | PathLimitReached` public outcomes. Do not expose search frontiers、tie-breaks、
  retries or snapshot claims.

### Query sequence

```text
request
  -> locate focal/endpoints
  -> query bounded incoming/outgoing Relation branches
  -> merge by Relation ID and cut the public page
  -> query required endpoint Blocks in batches
  -> validate endpoint closure
  -> return public model/outcome
```

For path search，frontier Relation reads are batched by Block IDs and split into internal chunks when needed；the chunk size is
an implementation limit，not public API. Default/hard budgets remain `4/8` hops and `1000/10000` explored Blocks unless real
PostgreSQL evidence contradicts them.

### Proof

- automated public-manager integration against real PostgreSQL using the shared corpus；include cursor continuity、cycles、
  direction/content pruning、equal-shortest semantic validity and concurrent-authority endpoint closure.
- `EXPLAIN (ANALYZE, BUFFERS)` on a transaction-local sparse 50k topology confirms each direction-specific query chooses its
  `(endpoint, id DESC)` index；failure to choose an index on tiny fixtures alone is not treated as contrary evidence.

## Increment G2 — `@inkcre/core` public manager

- Add a presentation-free `graph-navigation-retrieval` domain module beside InfoBase models，not under `sink/graph`.
- Implement the same three public operations locally over PostgREST. Use separate ordered incoming/outgoing page queries and
  merge them inside the manager；use `.or(from_.in/to_.in)` only for bounded traversal frontiers，plus exact
  `.in(content)` and exclusive cursors. Do not add an RPC.
- Validate every returned row through existing Zod Active Record models and enforce endpoint closure before exposing results.
- Remove Vue Flow、MDS、community and layout ownership from `packages/core/src/sink/graph` once client consumers have moved；
  presentation algorithms belong to the app InfoBase View.

### Proof

- run the shared corpus through the public TypeScript manager against real PostgREST；compare outcome kind、entity sets、
  direction、cursor and path properties with the Python run，not private query counts or equal-path identity.

## Increment G3 — proven design-system gaps

- Extend `InkPopup` with a backward-compatible no-scrim/modeless option. Default behavior remains the current modal scrim；
  no-scrim does not install an invisible pointer-blocking overlay.
- Add domain-neutral `InkSearchBar` only after extracting the shared query/submit/clear/loading/accessibility presentation
  from its two real consumers. Retrieval mode、shortcut、routing and result ownership remain outside `@inkcre/ui-web`.
- Add focused component/story evidence and a Changeset；publish the design package before final client registry verification.

No Graph node、edge、toolbar、panel-header or route-outlet component is promoted into the design system in this increment.

## Increment G4 — Resolver preview contract

- Add required `previewRenderer` beside `solvedContentRenderer` on the Resolver registration contract. Both consume the same
  Resolver instance and solved-content authority；there is no preview projection or layout hint.
- Provide interaction-free bounded previews for every core Resolver and the in-scope Mail/Twitter extension Resolvers. Do not
  silently fall back to a full renderer because full rendering may materialize content or expose business actions.
- Split presentation components only where preview/full behavior is genuinely different；do not duplicate Resolver content
  acquisition.
- Coordinate core package、host and extension version/Changeset inputs so no published runtime loads an old Resolver contract
  as if it supported preview.

### Proof

- type/build checks cover every registered Resolver；targeted renderer checks prove both contracts receive the same solved
  content and preview contains no business actions. Extension host smoke proves Mail/Twitter remotes register successfully.

## Increment G5 — application router, Recall/Search and outlets

- Extend the application implementation of `InfoBaseRouter` and Vue Router mapping for Block/Relation focal destinations、
  entity-local inspectors and Block solved content. Keep router state authoritative in Vue/browser history；do not create a
  second history store.
- Normalize mutually exclusive reconstructive query shapes：`focal_block`、`focal_relation`、`path_from + path_to`、`q`.
  Scene scale/direction/camera/layout/cursor/cache remain runtime state.
- Add one application-owned Recall/Search singleton opened by `Ctrl/Meta+K`. Recall hands selected results to List by default
  or the active InfoBase View；Find path selects endpoints and hands path address state to Graph.
- Make Block/Relation Inspector entity-local. Desktop outlets use modeless `InkPopup`；closing calls router `back()` and does
  not rewrite that action as another forward route.

### Proof

- router normalization/unit evidence for deep links and conflicting query forms；browser evidence for shortcut、back/forward、
  relation inspection and solved-content return path.

## Increment G6 — Graph View behavior rewrite

- Replace full-graph loading/community/layout selection with random focal + bounded standard neighborhood. Hard-cut old focal
  community machinery rather than adapting it to partial scenes.
- Maintain a bounded session scene cache keyed by entity identity. Activating a canvas entity changes focal；Inspect is an
  explicit secondary action. Scale admits the accepted `8/20/50` Relation budgets without claiming totals.
- Retrieve one `both` neighborhood per focal/scale. Direction is soft presentation state：inactive Relations/endpoints remain
  visible and interactive，and changing direction triggers no query、layout or camera work.
- Render structural shells first；resolve focal preview first，then admitted neighbors through a small cancellable concurrency
  pool and shared Resolver cache with `materializeMissing=false`.
- Use Vue Flow's actual node dimensions and `nodesInitialized` event/composable. Layout is deterministic around intrinsic
  measured sizes；parallel Relations receive deterministic lanes. Existing positions survive shared-entity scene changes and
  user drag remains session-only.
- Drive camera only from explicit focal/path/refocus actions. After the relevant nodes are initialized，use Vue Flow's
  node-scoped `fitView`；remove delayed repeated fitting. Manual pan/zoom owns the camera until another explicit action.
- Reuse the current InkCre shell、palette、tokens and feedback components. Visual state stays restrained、cool、professional
  and sharp；focal is not enlarged，debug/query vocabulary is absent，and the rejected spike is not an implementation input.

### Proof

- focused browser journeys from Acceptance C for initialization、focal navigation、scale、direction、inspection、relation
  route、path and history；manual/scripted actual-shell review for camera feel、drag continuity、intrinsic preview layout、
  reduced motion and representative narrow width.

## Increment G7 — closure and promotion

- Run the real producer vertical across Memos、RSS/Atom/HTML、rumination/SQLite and Mail graphs；aliases remain harness-only.
- Run Python and TypeScript corpus parity against the same migrated PostgreSQL authority，then the built client browser
  journeys. Do not replace this with schema/helper tests or pixel snapshots.
- Promote stable product/technical truth to Hub and local implementation truth to Unit TDD only after the implementation has
  proved it. Update shared refs and owner repositories in separate commits.
- Verify design package publication/consumption、client extensions build/release inputs and preview deployment before closing
  the unit. Release boundaries follow repository owners；the implementable unit itself is not a release unit.

## Branch simulation and hazards

1. **A focal disappears**：manager returns no neighborhood；Graph keeps route authority and realizes missing/fallback state，
   never chooses an unrelated focal silently.
2. **A Relation disappears between reads**：successful response omits it unless both endpoints survive；cursor still derives
   from the ordered Relation page，not the filtered output.
3. **Equal shortest paths**：implementation may pick either；tests assert validity and minimal hop count only.
4. **Preview fails**：Node shell remains navigable and presents concise failure feedback；retrieval success is unchanged and
   no hidden retry/materialization occurs.
5. **Preview changes dimensions**：measurements are batched before layout；camera is fitted once for the explicit action，not
   once per completion.
6. **Old extension remote lacks preview**：coordinated contract/version release is required；full-renderer fallback is not
   introduced to hide the mismatch.
7. **PostgREST URL/frontier grows**：split private frontier batches；do not expose transport chunking or add database RPC.
8. **Scene shrinks from broad to compact**：surplus entities leave the active scene but may remain in bounded session cache；
   authority is neither deleted nor described as an undo.
9. **Manual camera gesture races loading**：manual movement cancels pending automatic camera ownership；preview/layout may
   settle without stealing the viewport.
10. **Design package source lane differs from registry release**：joint development may use the workspace/source lane，but
    final client verification consumes the published package exactly as deployment does.

## Deliberate exclusions

- graph-navigation Peer delegation/inbound，database RPC，generic N-hop or pattern language；
- full-graph/community analysis，durable layout/camera/scene state，manual node resizing，inline expansion；
- snapshot isolation、hidden retry、path ranking/tie-break API，negative-path matrices without invariant value；
- new Graph-specific design-system abstractions or a new application shell.
