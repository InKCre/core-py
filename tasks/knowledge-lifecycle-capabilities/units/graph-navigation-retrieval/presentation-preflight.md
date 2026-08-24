# Graph Navigation Presentation Preflight

## Purpose

Record evidence from the actual client-web and `@inkcre/ui-web` owners before implementation。This is not a visual spec or
a replacement mock；it bounds the presentation state diff and prevents the rejected full-screen spike from becoming an
implicit implementation reference。

## Actual application evidence

- The real shell is `InkHeader` over one content region with an on-demand right-side `AppSidePanel`。Its visual character is
  already sparse、black/white、square-edged and content-led；Graph must not invent another rail、persistent status strip、
  debug vocabulary or explanatory chrome。
- The current empty Graph page confirms that the application shell itself does not need redesign。Its local italic
  `No blocks to display` copy is the defect；the existing `InkPlaceholder` already owns the correct generic empty/error
  treatment。
- Current Graph loads every Block/Relation，runs browser community detection，offers community/layout selectors and repeatedly
  schedules `fitView()`。This is a full-graph scene architecture，not a presentation layer that can be retained around the new
  bounded focal retrieval。
- Current Graph/Inspector styles mix `sys-var` with retired `--ink-*` fallbacks and literal colors、spacing、radius and type。
  `BlockNode` mostly uses current tokens but spends elevation、translation and border simultaneously for hover/selection；
  `RelationEdge` already has a usable token-based baseline but lacks focal/context/direction and parallel-lane states。
- The current Graph node reads/truncates persisted `Block.content` directly and displays exact Resolver IDs。This is both a
  semantic and presentation defect；the accepted Resolver preview contract replaces it rather than restyling it。

## Existing design authority

- The current token system already provides the required surface、text、border、brand、spacing、radius and restrained
  elevation vocabulary。No new color、shadow or graph-specific token is justified by current evidence。
- `InkButton` covers canvas commands；`InkPlaceholder` covers empty/error states；existing typography/spacing mixins cover
  Node、Relation and outlet composition。
- `InkPopup` always teleports a full-screen scrim。`closeOnScrim=false` only changes dismissal and does not preserve pointer
  access to the navigation host。A backward-compatible generic ability to omit the scrim is therefore a proven design-system
  gap；Block/Relation Inspector and desktop Solved Content consume it。
- A domain-neutral `InkSearchBar` remains a valid promotion。The existing List search is a raw local input，while the accepted
  application Recall/Search introduces another consumer with the same accessible query/submit/clear/loading presentation。
  Global shortcut、retrieval mode、result routing and InfoBase View selection remain application-owned。

## Narrow presentation contract

- Graph keeps the actual application shell。Its own persistent controls are limited to canvas navigation、exploration scale、
  soft direction emphasis and the contextual Inspect action；only controls justified by those states appear。
- Block preview is intrinsically sized within scene bounds and uses Resolver `previewRenderer` over the same solved-content
  authority as full rendering。It contains no business action、inline expansion、exact Resolver ID or debug state。
- Focal emphasis does not enlarge a Node。Use the minimum sufficient combination of a crisp border and reduced context
  contrast；a halo is optional and only retained if real implementation evidence shows the border alone is insufficient。
  Elevation and z-index are not default state signals。
- Relation presentation preserves direction、supports deterministic parallel lanes and exposes hover/focal/incident/
  inactive-direction states。Inactive direction remains legible and interactive rather than disabled。
- Inspector/Solved Content remain independent modeless route outlets over desktop InfoBase Views。They use no scrim，do not
  dismiss on outside click and close through `InfoBaseRouter.back()`。Narrow Solved Content may occupy the available viewport。
- Loading、empty、missing and error states use existing InkCre feedback primitives and concise product copy。No state explains
  architecture、query parameters or implementation vocabulary。

## Environment observation

- The client-web local runtime correctly attaches to the core-py-owned development database after the owner runtime reaches a
  converged descriptor。The committed/local Portless access projection currently reports an explicit `:1355` URL while the
  live Portless proxy serves the hostname on standard HTTPS；this did not change Graph design but must be accounted for in
  manual/browser Acceptance setup rather than mistaken for a product failure。
- A small development-only graph was inserted into the disposable development database for visual/runtime investigation。
  It is not an Acceptance fixture、does not shape implementation and may be removed by the ordinary development reset。

## Closed result

Presentation preflight is complete enough to design Acceptance and implementation sequencing。No replacement full-screen
visual spike is required before implementation；visual verification belongs to the actual client shell during the client-web
implementation loop。
