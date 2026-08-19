# Graph Navigation Retrieval Acceptance

## Status

- **Status**: accepted implementation baseline；reopen only when implementation evidence contradicts a public invariant。
- **Evidence principle**: black-box-first。Static checks prove types、migration/index shape and ownership boundaries；they do
  not substitute for manager/database or browser journeys。No pixel snapshot becomes visual authority。

## Evidence topology

```text
machine-readable topology corpus
  ├─> core-py public manager -> real PostgreSQL/SQLModel
  └─> @inkcre/core public manager -> real PostgREST
            |
            v
      semantic parity assertions

real producer corpus
  -> Memos / RSS / Atom / HTML / rumination / Mail graph
  -> neighborhood + relation + path operations
  -> client-web Graph navigation host
  -> Resolver preview / Inspector / Solved Content
```

The topology corpus owns graph shape and legal-result properties，not database IDs、row ordering beyond the public cursor
contract or one arbitrary equal-shortest path。Its durable authority is a machine-readable JSON contract adjacent to the Hub
Product TDD；both Spokes consume the same file through `docs/_shared` rather than duplicating independently drifting fixtures。

## A — Manager contract and parity

Run every scenario against a migrated disposable PostgreSQL database through the public Python manager and public TypeScript
manager。No repository helper or private query method is the assertion surface。

1. **Block neighborhood**
   - existing focal is returned with an endpoint-closed page of Relations/endpoints；
   - isolated focal succeeds with one Block and zero Relations；missing focal returns `None`/the peer contract equivalent；
   - `in`、`out` and `both` preserve persisted Relation direction；
   - exact `contents` selects only exact Relation content values；
   - default/explicit limits、Relation-ID-desc ordering and exclusive `next_cursor` produce no repeated Relation across pages。
2. **Relation neighborhood**
   - existing Relation returns itself and exactly both persisted endpoint Blocks；missing Relation returns no result；
   - direction/content are unchanged and Relation does not acquire Resolver or solved-content fields。
3. **Bounded path**
   - a unique shortest path returns `found` with endpoint-closed GraphModel and aligned ordered Block/Relation ID paths；
   - `from == to` returns one Block and zero Relations；cycles terminate；
   - an exhaustively disconnected graph returns `not_found`；hop or explored-graph exhaustion returns `limit_reached` when
     completeness has not been proved；
   - `in`/`out` and exact contents alter admissible traversal without rewriting stored Relation direction；
   - an equal-shortest graph accepts any valid shortest result and never exact-asserts an incidental tie-break。
4. **Concurrent authority changes**
   - a successful neighborhood response remains endpoint-closed if a Relation/endpoint disappears between its internal
     reads；the original continuation cursor remains the page cursor；
   - a path whose final persisted rows no longer validate fails as an ordinary retrieval/validation error，not fabricated
     `not_found`、`limit_reached` or hidden retry。
5. **Random Block primitive**
   - empty authority returns no Block；non-empty authority returns one existing Block without loading all IDs into the
     browser or asserting distribution quality from a tiny sample。

Parity compares status、entity sets、endpoint closure、direction、continuation and path validity。It does not require the two
implementations to choose the same member of an equal-shortest result set。

## B — Real graph vertical

Reuse the readable producer authority already accepted by Semantic Retrieval rather than inventing lorem-ipsum graph data：

- a Memos design-capture note and comment；
- real RSS/Atom protocol doubles with deep-module and Peer-discovery articles；
- the pinned public-domain SQLite Architecture document and its rumination-produced Pager interpretation；
- the Mail acceptance thread with parent/reply、participants、MIME parts and materialized semantic content。

Generated IDs and graph rows remain runtime results，not corpus authority。Acceptance aliases resolve only after real producers
write the graph and never enter production models/APIs。

Required journeys:

1. Navigate from each producer root to one direct semantically useful neighbor and confirm the returned Relation identity、
   content and direction match persisted producer authority。
2. Navigate the SQLite source → interpretation/semantic-content chain without using Resolver-local relation access as the
   graph-retrieval implementation。
3. Find one unique path inside the Mail thread/component graph and verify every path step can be independently followed as a
   neighborhood request。
4. Address one real Relation directly and recover both endpoints；then resolve their labels/previews outside the retrieval
   result，proving presentation-free authority。
5. Use an isolated real text Block to prove that “no Relations” is a successful graph fact，not a missing/failure state。

## C — Client-web navigation-host journeys

Execute against the real development/E2E database and real built/dev client，with browser runtime config injected by the
existing E2E harness rather than committed to the build。

1. **Initialization**: opening Graph with no focal chooses one existing random Block and realizes its standard bounded
   neighborhood。An empty database shows the application Recall/Search fallback through InkCre feedback presentation。
2. **Progressive focal navigation**: activating a neighboring Block or Relation updates role-named focal query state、replaces
   the bounded active scene and preserves shared entity positions；camera zoom alone issues no retrieval。
3. **Exploration scale**: compact/standard/broad admits bounded continuation around the same focal；decreasing scale hides
   surplus entities without deleting authority or requiring a total-count query。
4. **Direction emphasis**: all/incoming/outgoing changes opacity/emphasis only。Entity identity/count、layout、camera and
   retrieval requests remain unchanged，and dimmed entities remain interactive。
5. **Inspection**: explicit Inspect opens Block/Relation Inspector without a scrim。The Graph remains pointer-accessible；
   closing invokes browser/router back without undoing the already selected focal scene。
6. **Solved content**: Block Inspector opens Solved Content over the same scene。Closing returns to the Inspector；preview and
   full renderer consume the same solved-content authority，but Graph preview remains concise and interaction-free。
7. **Application Search**: `Ctrl/Meta+K` opens Recall/Search。Recall defaults to List outside an InfoBase View and hands `q`
   to the current Graph when it is active；Find path hands `path_from`/`path_to` to Graph，which realizes found/not-found/
   limit-reached without broadening or retrying the query。
8. **Relation route**: a direct Relation destination seeds relation + endpoints，supports focal navigation to either endpoint
   and opens only the Relation Inspector—never a fictional solved-content route。
9. **History/deep link**: refresh reconstructs focal/path/outlet state from the URL contract；camera、scale、layout、cursor and
   session cache remain non-authoritative runtime state。
10. **Responsive/accessibility**: keyboard focal/Inspect actions work；focus presentation is visible without color alone；
    reduced-motion removes spatial travel；narrow Solved Content can use the viewport while route/content semantics remain
    unchanged。

## Visual acceptance

Visual review runs in the actual InkCre shell at representative desktop and narrow widths。It judges the accepted state
hierarchy—restrained、cool、professional、sharp；existing palette；minimal chrome；legible focal/context/direction；intrinsic
previews；modeless outlets—rather than comparing pixels to a mock。The rejected visual spike is explicitly excluded。

## Proof allocation

- Schema、types、migration shape and ownership facts belong to static checks。Public-manager behavior first remains a
  manually executed real-PostgreSQL/PostgREST script or journey；automation requires a later，explicit promotion decision。
- High-value client journeys remain manual/scripted against the database/Core Peer chain；do not create component-helper
  tests for behavior already covered by type checking or the browser vertical。
- Visual calibration、camera feel、drag continuity and reduced-motion quality remain an explicit manual/scripted Acceptance
  checklist until repeated regressions prove that a narrower automated mechanism has positive ROI。
- No negative-path matrix is required merely for completeness；retain only failures that distinguish a public outcome or
  protect an accepted invariant。
