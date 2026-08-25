# Mail Extension Acceptance

- **Status**: Acceptance frozen through D-314 and passed on 2026-08-11。
- **Purpose**: prove the Mail Extension's observable vertical behavior，not the incidental implementation of schemas、parser
  helpers or Adapter internals。

## Execution Evidence

- J1–J3 pass against a real ephemeral Dovecot 2.4.4 and disposable PostgreSQL database using
  `tests/extensions/mail/acceptance/test_mail_vertical.py`；the harness owns the `.eml` corpus and provisions source state
  only through production database/IMAP boundaries。
- J4 passes in `client-web/tests/e2e/mail-info-base.spec.ts` against the graph produced by J1–J3，built host/remote assets，
  PostgREST and a live core-py Peer。The journey dynamically locates its collected MIME part and does not depend on fixed
  production IDs。
- Core static/unit gate：Ruff clean，Pyrefly 0 diagnostics，`376 passed, 35 skipped`。Client gate：full `pnpm check` passed。
- No deferred negative-path suite or fake browser Mail Source handler was introduced。

## Evidence Authority

### Blocking real-IMAP harness

- Start an ephemeral Dovecot instance and interact with it exclusively through real IMAP sockets from outside the server。
- Install acceptance-owned `.eml` artifacts using IMAP `APPEND`。SMTP is outside this unit：the Mail Source's world begins with
  an existing mailbox，so `APPEND` establishes state without replacing any behavior under test。
- Run the production Mail extension、Source/Job、Resolver、InfoBase and Storage paths against that server。A protocol double or
  direct parser call cannot stand in for this gate。
- Corpus messages must be useful and readable technical material that Sir could reasonably keep，while still deliberately
  exercising the accepted MIME、participant、thread and HTML boundaries。Aliases、expected IDs and judgments belong only to
  Acceptance and are statically forbidden from production surfaces。

### Optional external-provider smoke

- Use explicit environment-supplied credentials for a dedicated external IMAP account；never embed secrets or depend on a
  personal mailbox's uncontrolled contents。
- Probe real TLS login、mailbox discovery、capability degradation、flags and lazy MIME materialization。
- Treat network/provider unavailability as unavailable diagnostic evidence rather than a product failure。Any repeatable
  standards-compatible discrepancy discovered here must become a Dovecot corpus/journey regression before it can block
  ordinary delivery。

### Browser journey

- Playwright opens client-web over the database produced by the real-IMAP collection path；it does not insert a hand-authored
  solved DTO to bypass Source/graph/Resolver behavior。
- Browser assertions cover route realization、focal loading、semantic rendering、navigation、explicit materialization and
  untrusted-HTML execution/network effects rather than CSS snapshots。

## Test Allocation

- Prefer static typing、Pydantic schema generation and lint for shape-only facts。
- Retain narrow unit tests only where a pure algorithm has meaningful branches that the vertical journeys cannot diagnose
  economically。
- Delete the PoC Mail tests that merely prove schema construction/serialization or isolated parser helpers；do not preserve
  them as a coverage target。

## Blocking Journeys

### J1 — Ordinary collection becomes a useful、incrementally maintained Mail graph

1. Before Source creation，the Dovecot mailbox contains one historical message。After Source creation，install a current
   reply whose referenced parent is not yet present，with realistic From/To/Cc occurrences、Message-ID/In-Reply-To/
   References、plain + HTML alternatives、mailbox flags and one excluded mailbox copy。
2. Execute `core.source.collect.v1` through the production Job Handler。The historical occurrence and excluded Mailbox are
   absent；current occurrences produce the accepted Source → Mailbox → Email provenance/membership graph、independent body
   Blocks、EmailAddress Relations、reply/reference anchors and mailbox-scoped MailFlag graph。
3. Assert that ordinary default `mark_as_seen` happens only after graph acceptance and is reflected both remotely and in the
   graph。Repeat collection and prove the same occurrences reconcile rather than duplicate。
4. Append the missing parent and mutate the existing occurrence's flags。A later ordinary Job completes the exact-one sparse
   reference anchor in place and，when the server advertises the corresponding capability，replaces the old occurrence's
   flag snapshot without scanning semantics leaking into Source state。

This journey proves initial horizon、ordinary checkpoint、canonical graph production、reference completion、flag authority、
remote seen action and repeatability together。Exact row counts are asserted only where the product owns uniqueness；the
test does not force Organization-clean graph multiplicity where the accepted model permits benign duplicates。

### J2 — Explicit backfill and collection policies remain separate from ordinary synchronization

1. Run `core.source.backfill.v1` over an exact `[since,before)` range containing the historical message from J1。It is
   collected without advancing/regressing the ordinary checkpoint and remains unseen under the default independent backfill
   policy。
2. Repeat the same range and prove reconciliation rather than a second collected occurrence。A valid empty range result is
   an ordinary finished no-op。
3. Materialize an inherited extension mailbox-exclusion default onto a Source，change the extension default and prove the
   Source remains unchanged；reset the Source field to null and prove the next validated Mail command materializes the new
   default once。Previously excluded graph/checkpoint state is neither deleted nor rewritten。
4. Exercise prospective remote-removal policy with two occurrences：a removal observed while synchronization is disabled
   remains in the graph；after enabling the policy，a newly and reliably observed removal deletes only that occurrence's
   membership/flags，not its canonical Email content。No retroactive scan is inferred from enabling the setting。

### J3 — MIME metadata is cheap to collect and explicit materialization adds semantic content

1. Collect a multipart Email containing plain/HTML bodies、a CID inline image and at least one typed attachment。Collection
   stores both text representations and MIME metadata/relations but creates no binary semantic child or Storage blob for
   non-text parts。
2. Resolve the Email and each MIME-part read-only。`SolvedEmail` exposes graph-aware bodies、participants、membership、flags、
   references and nullable component content without network materialization；opening/solving the Email does not fetch all
   remote parts。
3. Invoke explicit MIME materialization。The Resolver derives provenance/locator and the effective writable Storage，fetches
   the exact `part_id` through the production IMAP Adapter，classifies bytes through the accepted Mail evidence ladder and
   adds a semantic media/file Block plus `content` Relation。A second invocation returns usable solved content without
   requiring a created/existing status or exact-one graph promise。
4. After successful materialization，disable/remove remote access and prove the existing child still solves locally without
   traversing Source/Storage-routing policy。A different unmaterialized part reports materialization unavailable rather than
   guessing another occurrence。

### J4 — client-web realizes Mail through generic InfoBase destinations

1. Playwright opens the collected Email through the accepted GraphSurface Block route，observes graph focus and
   `BlockInspectorPopup`，then uses “view solved content” to reach `SolvedContentPopup` without a Mail-specific browsing page。
2. The Email renderer receives the complete exact Resolver + `SolvedEmail`，presents participants、bodies、mailbox/flags and
   MIME metadata，and navigates a reply/reference target through `InfoBaseRouter` so the graph focuses the target Block。
3. The HTML body is preferred，sanitized and rendered in the isolated iframe。A deliberate script cannot affect the host；a
   deliberate remote image/tracker causes no request。A normalized user-clicked HTTP(S) link may leave the app explicitly。
4. CID content is local only after explicit materialization；an unresolved inline part and attachment present metadata plus
   action instead of auto-fetch。The action traverses the same J3 Resolver command and updates the solved projection。
5. Popup close calls literal back and restores actual Vue/browser history；it does not push a guessed overview or parent
   Block route。Direct navigation to a syntactically valid missing Block remains an InfoBase destination with a local missing
   state。

## Deliberately Unproved Negative Paths

This unit does not build a focused failure-injection suite for partial Mailbox graph failure、checkpoint CAS loss、post-commit
Seen failure、access-binding mismatch、Cron/Job races、timeout recovery or optional OBJECTID negotiation。Their frozen design
semantics remain implementation constraints，not additional Acceptance gates。Likewise，do not create an acceptance-only
Source handler merely to make client-web claim a collect Job；the generic worker/registration surface remains in implementation
scope and receives static/build/code-path verification，while an unsupported browser IMAP Job is not claimed。

## External-Provider Smoke Horizon

The optional smoke runs a bounded subset of J1/J3 against one dedicated provider account：connect/login、discover Mailboxes、
collect one known occurrence、observe advertised capability behavior、round-trip one reversible flag mutation and materialize
one known MIME part。It does not delete personal mail、depend on uncontrolled mailbox ordering or assert provider-specific
folder names。A discovered provider discrepancy becomes blocking only after it is understood and reproduced as controlled
Acceptance evidence。
