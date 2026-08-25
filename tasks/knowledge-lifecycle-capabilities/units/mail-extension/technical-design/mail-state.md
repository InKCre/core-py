# Mail Occurrence and Remote State

- **Status**: D-262 best-effort canonical Email + plain MailFlag topology accepted；D-263–D-266 have since closed Email
  reconciliation/reference behavior。Canonical MailFlag content、normalization and synchronization remain the active edge。
- **Protocol evidence**: [Remote Mail State and Flag Facts](../evidence.md#remote-mail-state-and-flag-facts)。

## Accepted D-262 Topology

```text
Source --manages--> Mailbox
Mailbox --contains {type:"contains", uid_validity, uid}--> canonical Email
Mailbox --has--> MailFlag
MailFlag --tags--> canonical Email
```

- One Email Block is a best-effort canonical authored Email endpoint。Several exact remote occurrence locators may point
  to it across Mailboxes，but one Mailbox never points multiple live UIDs to the same Email Block。
- `contains` is the current membership fact and exact remote-access locator only。It does not own mutable flag fields。
- MailFlag is scoped by its owning Mailbox。A plain `tags` Relation therefore identifies one exact occurrence through the
  unique Mailbox/Email `contains` edge without repeating the locator。
- Removing one flag deletes only that `tags` Relation。Reliable EXPUNGE/removal deletes the occurrence's `contains`
  Relation and every plain tag between that Mailbox's MailFlags and the Email，while preserving collected Email content。
- The Mail Source maintains at most one live `contains` Relation for each `(Mailbox, Email)` pair。A second same-Mailbox UID
  creates another Email Block even when canonical evidence matches；generic InfoBase does not own this producer invariant。

## Unified Flag Boundary

- Persist IMAP `\Seen`、`\Answered`、`\Flagged`、`\Deleted`、`\Draft` and observed keywords through the same MailFlag
  Block + plain `tags` Relation topology。
- These flags have different use/action semantics，but they are all entries in IMAP's FLAGS message attribute and are all
  changed through STORE against a mailbox occurrence。UI meaning does not create a second persistence category。
- `\Deleted` is a flag meaning “marked for later removal”，not the absence of membership。Until EXPUNGE，both `contains` and
  the `\Deleted` tag exist。After reliable EXPUNGE evidence，neither occurrence fact remains；no deletion tombstone is added。
- Do not persist deprecated `\Recent`。It is session-derived rather than durable state and has no accepted use value。
- Canonical MailFlag content includes `name` plus nullable `description`。Description has independent resolver/retrieval/LLM
  value，but Base IMAP does not supply it；D-268 freezes provider-native → standards-backed → null adapter authority。Name
  normalization and mailbox-scoped identity are also frozen there；no flag enters Email root content or `contains` merely
  to simplify reading。

## Canonical MailFlag

- exact resolver ID：`extensions.mail.flag.v1`。
- exact content：`{"name":"\\Seen","description":"The message has been read."}`；`description` is nullable。
- `name` is ASCII case-insensitive identity inside one owning Mailbox。Known names use standards spelling；an unknown
  keyword retains first-observed spelling and later casing-only variants reuse it。
- Description selection is provider-native adapter metadata when actually available，otherwise stable non-localized
  standards-backed prose for known names，otherwise null。It is semantic canonical metadata rather than an IMAP wire fact。
- Do not persist `kind`/`is_system`（derivable from name）、`permanent`/`mutable`（operational mailbox/session capability）、
  scope references（owned by graph）or `description_source`（derivable from the owning adapter）。
- When one exact occurrence's complete FLAGS list is observed，replace its graph state：ensure present durable tags and
  remove absent ones。Do not treat a complete snapshot as an append-only event。

## Resolved Comparison — Locator-Qualified versus Plain `tags`

The Mailbox already scopes each MailFlag through `Mailbox --has--> MailFlag`。Therefore locator qualification does **not**
add precision across different Mailboxes；their flag Blocks are already distinct。It only distinguishes multiple current
UID occurrences that reconcile to the same canonical Email inside one Mailbox。

### Locator-qualified `tags {uid_validity, uid}`

- **Benefit**：preserves exact flags for arbitrary many `contains` Relations between one Mailbox/Email pair。Remote STORE
  and EXPUNGE cleanup can target the locator carried by the flag Relation without deriving it from another Relation。
- **Damage**：duplicates the occurrence locator into every flag edge and creates a cross-Relation invariant：each tag must
  match one `contains` edge。Flag add/remove、UIDVALIDITY reset and occurrence removal must update both representations
  coherently，while generic FK/schema cannot enforce the Mail-owned JSON reference。
- **Semantic damage**：Relation.content is the dynamic-property text consumed by generic graph projection and semantic
  retrieval。Embedding UID numbers and locator JSON with the predicate adds operational noise to an otherwise clear
  `MailFlag tags Email` fact，unless another protocol-specific interpretation layer is introduced。
- **Return boundary**：the added precision has value only when same-Mailbox duplicate occurrences share one Email endpoint
  and can hold divergent flags。

### Plain `MailFlag --tags--> Email`

- **Benefit**：one relation owns one semantic fact with no duplicated locator。Graph reading、Relation text projection、
  semantic retrieval and idempotent add/remove all use the ordinary generic Relation shape。
- **Derivable operation target**：the owning Mailbox is found through `Mailbox --has--> MailFlag`；its one live
  `Mailbox --contains--> Email` edge supplies UIDVALIDITY + UID。Remote action remains exact if that edge is unique。
- **Damage without an invariant**：if one Mailbox has two locators pointing to the same Email，plain `tags` cannot express
  divergent flag state or multiplicity。Removing one occurrence's flag can erase the other occurrence's state；a write may
  target the wrong UID。This is most harmful for `\Deleted` and any future remote mutation。
- **Low-cost safety condition**：Collection can maintain at most one live `contains` Relation per `(Mailbox, Email)` pair。
  When a second UID in the same Mailbox matches the same canonical evidence，it creates a separate Email Block instead of
  reconciling to that endpoint。Cross-Mailbox reconciliation—the common and high-value deduplication case—remains intact。

### Current ROI Reading

- The Enron directional sample observed zero strict duplicate-content groups inside the same owner/folder，while cross-folder
  duplicates were material。This is not a protocol guarantee，but it places the qualifier's protected case at the narrow
  edge and the cross-Mailbox canonicalization benefit in the common path。
- Under the one-live-contains-per-Mailbox/Email invariant，plain `tags` has the same operational precision for all accepted
  graph states and fails safely by declining same-Mailbox reconciliation rather than by collapsing mutable state。
- D-262 therefore supersedes D-261's locator-qualified tag content with plain `tags` plus that reconciliation invariant。
  Sir accepted the explicit loss：same authored Email duplicated inside one Mailbox becomes multiple best-effort canonical
  Email Blocks。

## Superseded D-260 Alternative

- D-260 made every exact locator create a separate Email Block，which avoided locator-qualified flag Relations but caused
  systematic duplicate semantic content across folders/providers。
- D-261 restored the canonical/occurrence split；D-262 removes locator qualification after proving Mailbox-scoped MailFlags
  plus the one-live-contains invariant retain exact mutable state。No MailOccurrence association Block is introduced。

## Empirical Duplicate-Risk Calibration

- Dataset：[CMU Enron Maildir](https://www.cs.cmu.edu/~enron/) through the
  [column-preserving mirror](https://huggingface.co/datasets/dpdl-benchmark/enron-maildir)，517,401 records preserving
  owner/folder structure。The mirror's Message-ID values are all unique and therefore unusable for measuring Message-ID
  reconciliation。A strict proxy signature over authored date、sender、To/Cc、subject and body was used instead。The corpus
  has no IMAP UID or flags and has known export/integrity transformations，so these are directional sample measurements，not
  universal mailbox probabilities。
- Same owner + same folder + same strict signature：0 observed。This supports treating same-Mailbox duplicate-occurrence
  flag ambiguity as uncommon，while D-262 removes the ambiguity by declining that exact reconciliation when it occurs。
- Same owner across folders，all folders：359,308 records belong to duplicate groups and 228,226/517,401 (44.1%) are excess
  copies relative to one canonical record。This upper bound is dominated by `all_documents` and `discussion_threads`
  aggregate folders。
- Excluding those two aggregate folders：85,713/330,689 (25.9%) records belong to duplicate groups，and 46,636/330,689
  (14.1%) are excess copies。Restricting to six common mailbox families gives 60,018/254,847 (23.5%) exposed and
  30,024/254,847 (11.8%) excess。
- Provider topology can be worse：[Gmail explicitly exposes labels as IMAP folders and provides X-GM-MSGID](https://developers.google.com/workspace/gmail/imap/imap-extensions)
  to identify one message across multiple folders。Collecting All Mail plus Inbox/labels without reconciliation can
  therefore duplicate a large share of one Source by construction。

## Active Question

The scheduled sync ladder and UIDVALIDITY's two distinct placements are frozen through D-270。Select the next Mail unit
edge from the remaining collection/action、MIME materialization、client rendering and Acceptance gaps；do not expand
checkpoint serialization without implementation evidence。
