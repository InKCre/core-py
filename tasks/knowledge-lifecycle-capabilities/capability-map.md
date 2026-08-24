# Knowledge lifecycle capability map

## Decomposition

| Trunk | Goal | Remaining candidate units |
| --- | --- | --- |
| Collection | persist source-specific information as reusable graph facts | Twitter/GitHub/Telegram hardening；CalDAV；Nextcloud Files；Apple Notes；future Memos collectors/products |
| Organization | improve later use of information already in the info-base | breakdown/interpretation、merge、linking and later evidence-backed approaches |
| Application | recover or navigate useful information | perceptual feature retrieval、hybrid composition and later use surfaces |

This table is a queue，not a roadmap。The next unit is selected after each closure from current user value、newly exposed
dependencies and uncertainty。

## Implementable-unit boundary

A unit is vertical enough to explain and verify：

```text
user value / observable failure
  -> native input or use request
  -> authority and cross-boundary contracts
  -> graph / projection behavior
  -> public-boundary acceptance
  -> bounded implementation increments
```

Shared mechanisms are not a fourth trunk。A vertical unit may expose pressure on Block、Relation、Resolver、Storage、Source、
Extension、AI、Job/Cron or Peer contracts；promote a common mechanism only when the current unit cannot correctly proceed
without it or repeated units demonstrate a stable shared seam。

## Completed baseline

- **Memos extension**: Memos-compatible backend MVP and MoeMemos journey；collector/flomo scope remains future work。
- **RSS extension**: RSS/Atom collection、identity、content acquisition、media materialization and Resolver/Storage baseline。
- **Mail extension**: IMAP collection、Jobs/Crons、communication graph、materialization and generic InfoBase rendering。
- **Semantic retrieval**: AI provider/model/profile、embedding maintenance、local/Peer retrieval and focal rumination。
- **Feature retrieval**: Block-local lexical projection plus system-driven multimodal interpretation。
- **Graph navigation retrieval**: bounded neighborhoods、shortest-by-hop paths and progressive InfoBase Graph View。

Canonical behavior and technical contracts are owned by `docs/_shared/10-prd`、`docs/_shared/20-product-tdd` and the relevant
Spoke-local durable docs—not by this queue。
