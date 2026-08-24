# Relation Producer Audit

- **Purpose**: check repository-owned Relation writers against D-097's directed dynamic-property contract before their
  rows become semantic-retrieval candidates。
- **Invariant**: `from` is subject、`content` is property/behavior/role、`to` is value/object。Persisted direction is graph
  authority；SemanticRetrievalManager does not reinterpret or repair it。
- **Correction owner**: original collection/graph producer；a narrowly evidenced schema migration is added only when
  retained historical rows actually exist and can be identified exactly。Never organization、resolver read、retrieval
  query or a background repair loop。
- **Search evidence**: ast-grep inventory of `RelationModel(...)`、`RelationManager.create/update(...)` and
  `OutArcForm`/`InArcForm` calls，plus raw migration SQL search。Generic persistence APIs are separated from business
  producers below。

## Confirmed Business Producers

| Producer address | Persisted assertion | Verdict | Implementation consequence |
| --- | --- | --- | --- |
| `extensions/memos/family/graph.py` | comment memo → `parent` → parent memo | correct | none；parent is the comment's parent |
| `extensions/memos/family/attachment.py` | memo → `attachment:<order>` → attachment metadata | correct | none；slot content remains extension-owned grammar |
| `extensions/memos/family/attachment.py` | attachment metadata → `content` → semantic content | correct | none |
| Memos reference grammar | memo → `reference` → referenced block | correct grammar；no current product writer | preserve direction when a writer is added |
| `extensions/rss/repository.py` | feed item → `feed` → feed root | correct | none；feed is item's membership/identity scope |
| `extensions/rss/repository.py` | feed item → `enclosure` → enclosure metadata | correct | none |
| `extensions/rss/enrichment.py` | feed item → `full_text` → text block | correct | none |
| `extensions/rss/enrichment.py` | enclosure metadata → `content` → semantic content | correct | none |
| `app/business/info_base/resolver/image.py` | image → `alt:text` → text block | correct | none |
| `extensions/github/resolver.py` | GitHub user → `owns` → repository | correct direction | keep predicate wording；Relation projection is structured subject/property/value，not forced English possessive prose |
| `extensions/mail/resolver.py` | email address → `from` → email | **reversed** | producer must emit email → `from` → sender address；no retained production row exists to migrate |
| `extensions/mail/resolver.py` | email → `to` / `cc` → address | correct | none |
| `extensions/twitter/bookmark.py::tweet_to_graph` | tweet → attachment / URL role → media/HTML | correct | none |
| `extensions/twitter/bookmark.py::_organize` | tweet → `bookmarked for` → reply text | **wrong owner/vocabulary** | do not retain graph mutation in legacy organization hook；future note collection needs an explicit collection/command owner |

## Generic Writers

- `app/routes/relation.py` and `RelationManager.create/update()` persist explicit caller-authored from/to/content。They
  have no source semantics from which to infer reversal；validate referential/schema integrity only。
- `InfoBaseManager` maps `OutArcForm` and `InArcForm` exactly as declared。Its direction mechanics are correct；business
  producers own the chosen arc form。
- `Resolver.breakdown()` currently has no concrete Relation-producing implementation。Future organization breakdown
  must emit the same invariant，but this audit does not create a runtime admission/repair layer。

## Planned Corrections（not implemented）

### Mail sender

1. Change `EmailResolver.create_graph()` from sender `InArcForm` to sender `OutArcForm`。
2. Update its Mermaid/docstring and add graph-shape verification，not schema/helper-only tests。
3. Do not add a speculative data migration：the canonical production read-only sample contains no Mail Blocks and local
   development data is disposable。If another retained deployment is later evidenced，inspect it before choosing a
   migration rather than assuming the current zero-row fact applies globally。

### Twitter bookmark note legacy hook（approved）

`SourceBase._organize()` is documented as a legacy no-op hook and has no production caller；only a direct unit test invokes
this implementation。Hard-cut the graph-writing body back to an explicit no-op and remove the test that treats it as a
feature。Do not move reply fetching into organization or add a semantic-retrieval repair path。Whether a future Twitter
collector persists bookmark notes—and under which exact relation vocabulary—is owned by a later Twitter source design。

Historical `bookmarked for` rows cannot be safely renamed merely from the generic relation string。A migration may act
only if endpoint resolver evidence and the intended new Twitter note grammar are approved together；this unit currently
does not invent that future grammar。

## Verification Boundary

- static/structural inventory proves no repository-owned constructor path was omitted；
- focused graph tests prove exact from/content/to for corrected producers；
- black-box semantic retrieval later returns stored Relation identity/direction unchanged；it does not serve as the
  mechanism that repairs producer defects。
