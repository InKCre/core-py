# Solved-Content Rendering

- **Status**: R3 product/technical boundary frozen；exact implementation seams remain plan/preflight-owned。
- **Decision authority**: [D-220–D-238、D-312](../../../decisions/index.md)。
- **Problem**: rich focal Blocks require resolver-owned local graph interpretation，while client-web currently calls the
  resolver-selected component `contentComp`、renders it inline under `BlockDetailsPanel` and lets only the graph page own
  cross-Block selection/navigation。

## Current Evidence

```text
graph.vue
  owns selectedBlock + selectedBlockRelations
  └─ BlockDetailsPanel(current Block only)
       ├─ persistence facts: id / resolver / timestamps / storage
       ├─ BlockContent
       │    └─ resolverCls.contentComp(resolver, solvedContent)
       └─ current-Block rumination action
```

- `TweetResolver` already reads attachment Relations/Blocks before its component renders，so literal-content rendering is a
  false contract。
- `BlockDetailsPanel` does not own graph selection and currently emits only close/ruminated。Adding target-Block lookup or
  route behavior there would invert ownership。
- Vue component events do not automatically bubble through arbitrary component layers，so “renderer emits an event” is not
  by itself a complete topology。
- `contentComp` and its Resolver prop were introduced together；current simple renderers are not evidence against the prop。
  The historic Module Federation runtime problem was duplicate `@inkcre/core` instances/registries and was repaired by
  singleton sharing。The Resolver's dynamic Relation import addresses a separate model-module cycle。
- Built-in core Resolver renderers are assigned by the host so the shared core package does not import app components；an
  extension Resolver can import its co-owned renderer because both depend in the allowed direction on the shared singleton
  core package。
- `@inkcre/core/extension/module-federation` already defines the closest runtime-binding precedent：a contract owned by the
  shared package、one module-scoped nullable implementation、host `setMFImplementation()`、consumer
  `getMFImplementation()` and fail-fast access before bootstrap。Its exported `isMFInitialized()` has no repository caller。
- `@inkcre/ui-web` defines the closest contract/provider precedent：`InkRouter` is implemented by client-web's Vue Router
  adapter and injected under `INK_ROUTER_KEY`。That validates “shared contract，host implementation”，but its Vue component
  scope is intentionally different from the Module-Federation-singleton scope required here。
- `configStore.initializeMeta(adapter)` is not the same binding lifecycle：the Store owns reactive config state、loading、
  persistence and an unconfigured null-object adapter。It should not be forced through a generic implementation binding。

## Confirmed Invariants

1. `block.resolver` selects an exact behavior contract；client-web presents its semantic projection through the Resolver's
   `SolvedContentRenderer`。The earlier exact name `BlockRenderer` is withdrawn。
2. `BlockDetailsPanel` becomes `BlockInspector`：it owns generic persistence facts and current-Block commands，not semantic
   rendering or graph navigation。
3. “查看内容” means view solved content，not inspect literal `block.content` or a Storage pointer。
4. Graph surface exclusively owns current-Block selection、cross-Block navigation/focus and any route consequence。
5. BlockInspector acts only on its current focal Block and does not know/open another Block。Its unused `relations` prop and
   caller binding must be removed。
6. Hydrated content and solved content remain distinct；graph-aware solved content keeps canonical focal content at `.root`
   and relation-derived values as siblings。
7. BlockInspector、GraphSurface、solved-content viewing and cross-Block navigation are InfoBase-domain concerns。A generic
   render-context callback bag is not their owner。
8. `SolvedContentRendererProps<SolvedContentT, ResolverT>` carries both typed solved content and the complete exact Resolver。
9. InfoBaseRouter owns current InfoBase location/history operations；an InfoBase surface realizes routes。GraphSurface is the
   current realizer，not a route or permanent default；future ListSurface may realize the same locations。
10. Solved content is a first-class MVP destination realized by `SolvedContentPopup`，not an ambient callback、page or
    BlockInspector implementation detail。
11. MVP routes cover only overview、inspect-one-Block and view-one-Block's-solved-content。No arbitrary extension route
    registration or speculative Relation/surface-specific routes。
12. The exact surface-independent route vocabulary is `overview | block | solved-content`；both focal routes carry a
    `BlockRef` under `block`。
13. InfoBaseRouter does not own a second history stack or delegate to a separately meaningful `InfoBaseHistory` domain
    module；an internal replaceable history adapter maps its operations to the existing Vue Router/browser history authority。
14. `back` retains literal history traversal semantics and must not be simulated by pushing a guessed Block route。
15. InfoBaseRouter's MVP public interface is exactly read-only `current`、`push(route)` and literal `back()`；public
    `replace()` remains out of scope absent a real domain caller。
16. `current` is `InfoBaseRoute | null`；`null` exclusively means the current application location is outside any InfoBase
    surface，not another domain route or retained last-known location。
17. The accepted GraphSurface web mapping is `/info-base/graph`、`/info-base/graph/blocks/:block` and
    `/info-base/graph/blocks/:block/content` for `overview`、`block` and `solved-content` respectively；the surface prefix
    belongs to the application route，not `InfoBaseRoute`。
18. The adapter derives `current` from Vue Router and encodes `push` back into named Vue routes；it stores no mirrored
    location state。
19. InfoBaseRouter is a singleton client capability port，not a shared implementation of history/routing。`@inkcre/core`
    owns the fixed contract and one implementation binding；each client implements nullable `current + push + back` against
    its own navigation authority。
20. GraphSurface/ListSurface and renderers are Router consumers；surfaces realize the current domain route into UI state。
    The shared layer owns no navigation state、history stack or route registry。
21. The shared `InfoBaseRouterHistoryAdapter`、generic Location and `InfoBaseRouteCodec` candidates are withdrawn。Any such
    factoring remains private to a client implementation and requires its own evidence。
22. Singleton binding follows the existing `MFImplementation` pattern：one module-scoped nullable implementation、host
    set、consumer get and fail-fast before configuration。Do not extract a generic `createRuntimeBinding<T>()` or registry。
23. Malformed/unmapped client routes project `current = null` and belong to app-level not-found behavior；a syntactically
    valid route with a missing Block remains an InfoBase route，and its surface/view owns loading and missing-entity UI。
24. InfoBaseRouter never queries Block persistence to determine route validity。
25. GraphSurface keeps the graph as its surface for all three routes：`overview` has no focal popup，`block` adds
    `BlockInspectorPopup` and `solved-content` adds `SolvedContentPopup`。A first-class destination is not
    synonymous with a page or replacement body。
26. Each popup owns close and interprets it as literal `InfoBaseRouter.back()`；GraphSurface does not convert close into an
    explicit overview/Block push or guessed parent destination。
27. GraphSurface and future ListSurface are `InfoBaseView` navigation hosts with a `route destination outlet`；these terms do
    not require a shared base component/class。
28. Presentation-neutral content is normally wrapped by its parent container owner。A route destination exceptionally owns
    its shell only when the container lifecycle is part of the destination behavior contract，as with dismiss → back。
29. Exact shell-owning names are `BlockInspectorPopup` and `SolvedContentPopup`；`SolvedContentView` is withdrawn。
    `SolvedContentRenderer` remains presentation-neutral inside `SolvedContentPopup`。
30. `InfoBaseRouter.current` is GraphSurface's only focal-Block authority；delete local selected-Block identity。Both focal
    routes select/focus their referenced node，while overview clears focus。
31. GraphSurface correctly understands stable `InfoBaseRoute.name` semantics because an InfoBaseView is the route realizer；
    it does not understand Vue route names/paths and does not push while realizing an observed route。
32. `BlockInspectorPopup` and `SolvedContentPopup` accept only `BlockRef` and each owns `Block.get()` plus loading/missing/
    error lifecycle。SolvedContentPopup additionally owns Resolver acquisition、solving、refresh and disposal。
33. GraphSurface's graph projection may contain the same Block but is not a resource provider for route destinations；a
    future shared cache may remove proven duplicate-read cost without changing ownership。

## Candidate Responsibility Topology

```text
InfoBaseRouter ── current InfoBase location/history ──> selected InfoBase surface realizer
                                                      ├─ GraphSurface (current)
                                                      └─ ListSurface (future evidence example)
                                                               │
                            overview / focal destination <──────┘
                                  ├─ BlockInspector
                                  │    └─ “view content” command
                                  └─ SolvedContentPopup
                                       ├─ Resolver lifecycle
                                       └─ SolvedContentRenderer(resolver, solvedContent)
                                            └─ target-Block navigation command
```

This topology and the following domain route shape are accepted：

```ts
type InfoBaseRoute =
  | { name: 'overview' }
  | { name: 'block'; block: BlockRef }
  | { name: 'solved-content'; block: BlockRef }
```

InfoBaseRouter owns these domain locations and public navigation commands，while a router-internal replaceable history
adapter maps them onto the one existing Vue Router/browser history authority；there is no second InfoBase history stack or
independent `InfoBaseHistory` domain abstraction。The selected surface owns its
loading/arrangement/focus mechanics and realizes the location。
GraphSurface is the current realizer，not the route authority or `overview` synonym。The router may adapt to Vue Router/URL
state without exposing app paths to Module Federation renderers。This is materially different from a render context：the
router models stable InfoBase navigation state and makes `SolvedContentPopup` addressable rather than forwarding one callback。

The prior `SolvedContentRenderContext` proposal is withdrawn。Explicit event forwarding through BlockInspector and direct
extension access to the app's Vue Router/routes also remain disfavored。A router shared through the Module Federation singleton
`@inkcre/core` is a plausible mechanism，but its global-instance/test/multi-app consequences still require design。

The accepted renderer boundary is:

```ts
interface SolvedContentRendererProps<
  SolvedContentT,
  ResolverT extends Resolver<unknown, SolvedContentT>,
> {
  resolver: ResolverT
  solvedContent: SolvedContentT
}
```

Exact generic parameter ordering must follow the final Resolver declaration rather than copying this illustrative snippet
blindly。

## Derived Destination Lifecycle（R3 closure candidate）

The existing client confirms that route changes cannot rely on component construction：`BlockContent` creates one Resolver
from setup-time props，while GraphSurface owns a separate selected-Block object。The accepted Router topology therefore implies
the following explicit `SolvedContentPopup` lifecycle without another product choice：

1. `block: BlockRef` is watched immediately。Every route-ref change increments a local load generation，clears the previous
   destination state and best-effort disposes its Resolver before loading the new Block。
2. The Popup loads the current Block row，constructs the exact registered Resolver and calls solved-content retrieval。Only
   the latest generation may publish Block、Resolver、solved content or error state；a stale completion disposes any Resolver
   it created and otherwise has no UI effect。This prevents async route races without requiring every Resolver to implement
   cancellation。
3. Explicit refresh keeps the same InfoBase route but reruns the complete destination load from Block persistence，including
   Resolver selection，with the stable `{refresh:true}` cache-replacement semantic。It does not depend on mutating an old
   Resolver in place，component remount keys or a new navigation entry。
4. Popup unmount invalidates the current generation and best-effort disposes the live Resolver。Disposal failure is internal
   diagnostic residue；it does not block close/back or the next destination，and no retry/checkpoint lifecycle is added。
5. Loading、missing-Block、solve failure and refresh failure remain Popup states。The presentation-neutral
   `SolvedContentRenderer` receives only the successful exact Resolver plus typed solved content and owns none of this
   controller lifecycle。

The same lifecycle shape applies to `BlockInspectorPopup` without Resolver/solve/refresh：watch BlockRef，generation-guard
`Block.get()`，own loading/missing/error and invalidate stale completions。Whether `Block.get` gains a nullable lookup seam or
the Popup maps an existing not-found result is implementation-plan detail，not a second route contract。

## Solved Email Projection Direction（R3 closure candidate）

`SolvedEmail` remains a read projection of the accepted graph rather than a second canonical Email DTO。Its structural
families are：

- `.root`: canonical Email root content；
- body representations：body Block、MIME `part_id` and the child Resolver's solved content；
- participant occurrences：EmailAddress Block/content plus role、order and occurrence display name；
- mailbox memberships：Mailbox Block/content plus UIDVALIDITY/UID locator；
- mailbox-scoped flags：MailFlag Block/content and its owning Mailbox reference；
- reply/reference navigation targets：normalized relation role/direction、order and target Email BlockRef；
- MIME components：Email-relative role/`part_id`、metadata Block and read-only `SolvedMimePart`，whose semantic child remains
  nullable and does not trigger automatic attachment download。

The Resolver may use narrower exact helper types for these families during implementation。It must not copy graph-owned facts
back into `.root`，make the renderer parse Relation strings or expose loading/created/existing mechanics。

## Email HTML Presentation and Remote-Resource Boundary

The sender-authored HTML body remains raw collected authority in its body Block。Its transition from passive data into a
browser-renderable projection is the concrete security boundary；sanitizing during collection or Storage write would damage
authority while failing to place responsibility where execution capability is introduced。

`SolvedContentRenderer` applies the following frozen behavior：

1. Prefer an available HTML body for faithful Email reading；fall back to the plain-text body。This does not merge or rewrite
   the independently collected body Blocks。
2. Pass HTML through a mature maintained sanitizer such as DOMPurify，then render the result in a sandboxed iframe without
   scripts、forms or same-origin capability。The application does not implement its own parser/filter，and CSP is not the sole
   XSS defense。
3. Disable automatic external resource loading by default，including remote images and tracking pixels。Normalize and allow
   only user-initiated `http`/`https` link opening。
4. Rewrite CID references only to client-local object URLs backed by an already materialized semantic content child。If the
   inline MIME part is still remote-only，show metadata/placeholder and an explicit materialization action instead。
5. Opening an Email never implicitly materializes an attachment。Attachment and unresolved inline-part actions retain the
   accepted Resolver-owned explicit command boundary。

This is the baseline contract at an identified untrusted-HTML/browser boundary，not an open-ended hardening backlog。Exact
sanitizer configuration、iframe construction and object-URL cleanup belong to implementation plan/preflight，provided they
prove these effects and do not invent a second HTML authority。

## R3 Closure

The destination lifecycle、SolvedEmail projection、navigation actions、attachment action boundary and HTML presentation policy
are now product/technical-design complete through D-312。Repository preflight may select exact helpers and expose a concrete
blocker，but does not reopen this topology merely because another component factoring is possible。
