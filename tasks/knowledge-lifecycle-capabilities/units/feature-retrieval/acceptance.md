# Lexical Retrieval Acceptance（Preflight-refined Review Contract）

## Authority

Acceptance uses graph state created through ordinary real producer paths，not rows shaped to satisfy the search
implementation。Readable aliases live only in the harness and resolve to actual Block IDs after collection。The corpus reuses
the proven Memos API、RSS/Atom HTTP protocol harness、Mail IMAP harness、PostgreSQL binary storage and the pinned public-domain
SQLite Architecture article where useful。

J6 uses one coherent real engineering-media authority rather than hand-authored OCR/ASR strings：NASA asset
`GSFC_20140121_GPM_m11457_Dave_McComas`，“GPM: Meet the Team: Dave McComas”。NASA's asset service supplies the real MP4 and
authored VTT discussing flight-software requirements、implementation、tests、simulation and spacecraft integration。The explicit
acceptance harness pins the origin ID/URLs + observed ETags，creates a bounded clip，extracts its real audio and an on-screen-text
frame，and remuxes the authored VTT into a standard subtitle stream。Derived local files remain ignored acceptance artifacts；
production code sees only ordinary stored bytes/Resolvers and never the corpus ID、aliases or expected phrases。NASA's official
media-usage guidance is the provenance/license authority。

AI is absent from J1–J5/J7 and required only by J6's real textualization/interpretation paths。Deterministic unit tests may
verify ranking mechanics，but they do not replace the following black-box journeys。

## J1 — Exact Technical Identifier

Collect a real technical article containing a distinctive identifier and a semantically related distractor that lacks the
identifier。Query the exact identifier through the public lexical capability。

- the target existing Block is returned before the distractor；
- evidence names literal/term matching and contains a bounded plain excerpt；
- no answer or transient entity is generated。

## J2 — Chinese Fragment Without Tokenization Assumption

Create a Memo through the real Memos endpoint containing a distinctive Chinese phrase and another conceptually related Memo
without that phrase。Query a contiguous fragment without spaces。

- the literal-bearing Memo Block is returned；
- the semantic-only distractor is not promoted merely for conceptual similarity；
- the journey does not depend on a Chinese-specific PostgreSQL dictionary。

## J3 — Media Metadata Before Materialization

Collect a Mail message with an attachment metadata Block whose filename/description/media type is distinctive，while leaving
the attachment bytes unmaterialized。Query that lexical feature。

- the MIME-part metadata Block is returned without unnecessary byte download or semantic content child creation，even though
  the maintenance call permits missing materialization；
- the result label/excerpt explains the match；
- opening the result can continue through existing graph/Resolver behavior independently。

## J4 — Maintenance、Update And Deletion

Create and index a Block，change the authoritative Block so its lexical projection changes，then run bounded maintenance；also
delete another indexed Block。

- stale records are excluded before maintenance；
- maintenance makes the new projection searchable and the old clue non-matching；
- Block deletion removes its derived lexical record through FK cascade；
- repeated/concurrent maintenance converges without duplicate records。
- direct and Cron-created exact lexical maintain/rebuild Jobs use the same Handler path and expose bounded reports in Job state；
- semantic maintain/rebuild uses its exact typed Jobs after the peer-local interval scheduler is removed，without changing
  retrieval results or profile selection semantics。

An additional controlled Resolver case proves that when lexical text is genuinely absent and an exact materializer is
available，maintenance may create the derived graph and then index its text。The assertion is on the ordinary graph/Resolver
effect，not a lexical-manager-owned OCR implementation。

## J5 — PDF Body Recall Without Metadata Substitution

Store a real PDF with a text layer through ordinary Storage/Resolver paths。Give its body one distinctive phrase that is absent
from title、author、filename and other metadata，then run lexical maintenance and query that phrase。

- an existing Block carrying the PDF body evidence is returned，whether that is the root projection or a materialized semantic-
  content child；
- the result does not succeed merely because the phrase was copied into fixture metadata；
- when a semantic-content child owns the body，the PDF root record does not recursively index the same body and produce a
  mechanical parent/child duplicate；
- metadata-only、encrypted and scanned-without-OCR branches report their actual capability boundary rather than claiming body
  completeness。

## J6 — Multimodal Textualization Recall

Through ordinary PostgreSQL binary Storage and exact core Resolvers，persist one image carrying visible text，one audio recording
carrying spoken text and one video carrying subtitle/spoken/on-screen text。Run credentialed lexical maintenance with exact
configured multimodal models/extractors，then query one distinctive phrase from each medium。

- each query returns the materialized existing text Block，not a transient OCR/transcript object or the parent copied body；
- each child remains connected to its media Block through the exact `text`、`transcript` or `subtitle` role；a video with
  distinct signals keeps distinct children rather than one aggregate text；
- the parent and child do not mechanically duplicate the complete derived text in their lexical records；
- rerunning maintain reuses an existing derivation under `materialize_missing` semantics；
- image/audio/video exact Resolver configs select their role-scoped Models，and the same Model may be reused across fields；
- an absent/dangling/disabled/incapable Model makes only its exact derivation unavailable，without preventing source-native or
  other-role children from being created and indexed。

For the same real media corpus，run the system-driven Organization command with a configured multimodal model/Agent，then query
a distinctive concept present only in its submitted description/summary rather than OCR/transcript text。

- the system selects the media candidate without a per-Block user request and persists an additive `interpretation` graph；
- the selected Agent is the deployment's independent media-interpretation Agent，not the rumination Agent by implicit fallback；
- image、audio and video candidates route through their exact configured Agent references，with one deliberately unusable slot
  proving it does not block another modality；
- the Agent receives actual media through the canonical UserMessage content part，while the real provider request proves dialect-
  local image/audio/video wire translation and joint modality + Tool-calling support；
- lexical maintenance indexes the resulting text Block and the concept query returns that Block；
- no Resolver `materialize_missing` call authors or replaces the interpretation；
- faithful text and interpretation remain distinguishable graph facts rather than one ambiguous combined projection；
- a second automatic Job skips the now-present interpretation without claiming freshness，while one controlled failed/no-output
  candidate does not block another missing candidate。

## J7 — Browser Recall Journey

From a built client-web runtime，submit a lexical query in the first real InfoBaseListView，observe the bounded result list，
select a target and return with browser Back。

- the browser delegates the exact capability through a live eligible Peer；
- result ordering/evidence survives transport validation；
- selection uses `InfoBaseRouter` and opens the target Block Inspector in the List view's destination outlet，without navigating
  away to GraphSurface；
- opening solved content remains in the same List host and closing either popup uses browser Back；
- Back restores the query/results rather than turning the lexical result view into a second history authority。

## Quality Gate

- every exact unique clue must return its target in the first position；
- a full literal phrase match must outrank a terms-only distractor；
- every returned row must be an existing fresh Block lexical record and an existing Block；
- no journey may depend on direct `Block.content` parsing、fixture-only production rows、AI answer quality or graph test labels
  leaking into production implementation。

No million-row performance gate or large-file corpus is added without measured product pressure。Schema verification confirms
the GIN indexes exist；the black-box journeys prove behavior rather than asserting one planner implementation。

## Delivery Closure Gate

Local J1–J7 and static checks are necessary but insufficient because this increment changes PostgreSQL extensions、schema、
migrations、generated peer projections and two independently deployed Spokes。After Sir separately authorizes commits and
pushes：

- the core-py PR's exact-head CI and preview delivery must pass against its fresh Neon preview branch，including database init、
  migration/readiness verification and deployed `/readyz` probe；
- the client-web PR's exact-head CI and Cloudflare preview must pass；
- J7 must exercise that built client against the matching core-py PR preview。A client CI run against the stable core release is
  useful regression evidence but cannot substitute for this cross-branch integration proof。

The lexical increment is marked accepted only after these gates are green；a pushed commit or locally migrated database alone
does not close the Unit。

## Local Execution Evidence（2026-08-13）

- J1–J5/J7 deterministic producer、Resolver、record、Job、Peer and UI contracts pass in their owning suites。
- J6 passed against real PostgreSQL binary Storage、the pinned NASA asset and real
  `qwen3.5-omni-flash` through `core.alibaba-model-studio.v1`。Observed outputs include image-frame OCR
  `GPM / nasa.gov/gpm`，audio/video transcript facts about flight software、requirements、testing、simulation and
  Tanegashima，then an actual Agent ToolCall submitted an interpretation graph that became lexically recallable。
- the harness pins the MP4/VTT origin URLs、ETags and SHA-256 values；derived frame/audio/subtitle/video files stay under the
  ignored `tests/lexical_retrieval/acceptance/.assets/` boundary。
- a fresh disposable Neon branch migrated from empty state to `1e4c7a9b2d5f`。The complete database-enabled non-migration suite
  passed 414 tests with 5 skips；upgrade/downgrade acceptance passed separately，and RSS real HTTP-double journeys passed after
  Job catalog isolation was corrected。
- the exact PDM 2.27.0 hermetic core contract passes after the `origin/main` extension-registry integration with 445 tests、41
  explicitly external skips and zero lint/type diagnostics；a fresh PostgreSQL database also passes migration、init and
  development readiness against the merge revision。
- client-web's complete test/lint/type/build contract passes with the new facade and InfoBaseListView。Generated cross-repo
  database/OpenAPI artifacts remain pending an immutable pushed core source rather than being fabricated from a dirty worktree。
- Render service/API behavior is covered by a mocked official-wire controller test and actionlint。The required private GitHub
  secrets and public variables are now configured；real service creation、Free cold wake and deployed probes remain pending and
  do not substitute for the final PR preview gates。
