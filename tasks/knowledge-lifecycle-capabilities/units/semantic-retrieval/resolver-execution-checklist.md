# Resolver Execution Checklist

> **Status**: proposed implementation contract for final review。D-075、D-096、D-102、D-193 and D-194 own the
> underlying decisions；this matrix turns them into one execution surface。

## Shared Label Contract

`get_label()` returns a concise、stable、non-localized graph reference，not a type ontology、UI title or full semantic
projection。

```text
<resolver-owned kind> <identifier>

feed <Hacker News>
github user <octocat>
text <A bounded first-line excerpt…>
```

- Every concrete Resolver implements the method；it never raises unsupported-capability merely because an identifier is
  absent。`<resolver-owned kind>` alone is the valid fallback。
- Label evaluation is Block-local。It may hydrate/decode/inspect the focal Block but cannot traverse Relations、invoke AI
  or materialize another Block。A Resolver whose ordinary solved projection is graph-aware must provide a local label path。
- Optional identifiers normalize whitespace。Free text uses the first non-empty logical line，collapses internal
  whitespace and truncates after 96 Unicode code points with one `…`。Structured identifiers such as a repository full
  name、email address、source-native ID or filename are not truncated unless they exceed the same 96-code-point safety
  bound。
- Exact resolver IDs do not enter the label。The readable kind below is directly owned by each Resolver；there is no
  resolver-type table、friendly-name registry or localization layer。
- Changing a retained label format incompatibly advances the exact Resolver contract because Relation embedding freshness
  otherwise cannot observe the semantic-input change。

## Core Semantic Content

| Exact ID | `get_text()` | `get_label()` | Producer obligation |
| --- | --- | --- | --- |
| `core.text.v1` | hydrated Unicode text | `text <first-line excerpt>`；fallback `text` | StarsGraph root from text |
| `core.html.v1` | rendered document text | `html <title>`；fallback first heading，then `html` | StarsGraph storage-backed root |
| `core.image.v1` | unsupported | `image` | optional `alt:text` child |
| `core.audio.v1` | unsupported | `audio` | storage-backed root |
| `core.video.v1` | unsupported | `video` | storage-backed root |
| `core.pdf.v1` | unsupported | `PDF <metadata title>`；fallback `PDF` | storage-backed root |
| `core.epub.v1` | unsupported | `EPUB <package title>`；fallback `EPUB` | storage-backed root |
| `core.zip.v1` | unsupported | `ZIP` | storage-backed root |
| `core.file.v1` | unsupported | `file` | storage-backed root |

Unsupported text remains an explicit `UnsupportedResolverCapability`。Typed byte facts do not pretend to be extracted
document text；PDF/EPUB title metadata is useful for a concise label without claiming full-text capability。

## Memos

| Exact ID | `get_text()` | `get_label()` | Producer obligation |
| --- | --- | --- | --- |
| `extensions.memos.memo.v1` | memo body | `memo <body excerpt>`；fallback `memo` | StarsGraph root；parent/reference/attachment remain graph relations |
| `extensions.memos.attachment.v2` | filename only | `memo attachment <filename>` | metadata → `content` → semantic content |

Attachment MIME is intentionally absent from both general text and label。It remains canonical metadata/resolver-selection
evidence rather than an embedding-specific decoration。

## RSS / Atom

| Exact ID | `get_text()` | `get_label()` | Producer obligation |
| --- | --- | --- | --- |
| `extensions.rss.feed.v1` | title + description | `feed <title>`；fallback configured URL | feed root |
| `extensions.rss.feed_item.v1` | title + summary + full text or authored content | `feed item <title>`；fallback native ID、alternate URL or authored excerpt | item → feed/enclosure/full_text |
| `extensions.rss.enclosure.v1` | enclosure title or `None` | `feed enclosure <title>`；fallback URL | enclosure metadata → optional `content` |

FeedItem v1 is corrected in place before release。Its label decodes only `CanonicalFeedItem` from the focal Block and does
not call the graph-aware solved projection。

## Mail

| Exact ID | `get_text()` | `get_label()` | Producer obligation |
| --- | --- | --- | --- |
| `extensions.mail.email.v1` | subject + plain-text/HTML body | `email <subject>` | email → from/to/cc → address |
| `extensions.mail.newsletter.v1` | subject + body | `newsletter <subject>` | newsletter root |
| `extensions.mail.email_address.v1` | display name + address，or address | `email address <name / address>`，or address | address root with source-owned reuse |

Subject is part of the generally useful Email/Newsletter projection，not a model-specific augmentation。Mail sender
direction is corrected only in the producer because no retained malformed rows exist。

## GitHub

| Exact ID | `get_text()` | `get_label()` | Producer obligation |
| --- | --- | --- | --- |
| `extensions.github.repo.v1` | full name、description、language and topics when present | `github repository <full_name>` | user → `owns` → repository |
| `extensions.github.user.v1` | display name + login，or login | `github user <login>` | user root with source-owned reuse |

Language/topics are stable repository facts with general use value；they move into the single text projection rather than
surviving as an embedding-only hook。

## Other Built-in Extensions

| Exact ID | `get_text()` | `get_label()` | Producer obligation |
| --- | --- | --- | --- |
| `extensions.telegram.message.v1` | text/caption plus media kind when present | `telegram message <text/caption excerpt>`；fallback native message ID | message root |
| `extensions.twitter.tweet.v1` | tweet text | `tweet <text excerpt>`；fallback native tweet ID | tweet → attachment / URL entity；legacy `_organize()` is no-op |
| `extensions.learn_english.lexical.v1` | lexical text | `lexical item <text>` | lexical root |

## Structural Verification

- static registry table proves the exact ID set and rejects every retired ID；
- abstract-method/type checks prove every concrete Resolver implements `get_text()` and `get_label()` explicitly；
- focused black-box cases prove text、label and unsupported/null distinction from hydrated inline and storage-backed Blocks；
- graph-aware Resolvers receive direct Relations that would alter solved content，while label remains unchanged，proving
  Block-local evaluation；
- structural search proves `get_str_for_embedding()` has no declaration、implementation or consumer；
- producer parity runs every StarsGraphForm through `InfoBaseManager.normalize_graph()` and checks accepted relation
  direction/grammar。
