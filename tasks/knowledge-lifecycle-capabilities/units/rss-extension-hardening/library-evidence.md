# RSS Extension Library Evidence

> Research snapshot for `rss-extension-hardening` Product/Technical discovery。It records evidence and
> recommendations，not durable dependency authority；the frozen implementation plan and lockfile own the
> selected exact versions after approval。

## Feed parser

### Recommended：Universal Feed Parser (`feedparser`)

- official repository：[kurtmckee/feedparser](https://github.com/kurtmckee/feedparser)
- selected release：`6.0.14`，published 2026-07-30；the earlier research snapshot saw `6.0.12` before the newer
  release reached the package index
- official package metadata：[feedparser on PyPI](https://pypi.org/project/feedparser/)
- official capability docs：[Advanced Features](https://feedparser.readthedocs.io/en/latest/advanced/)
- relevant evidence：
  - RSS and Atom normalization across multiple generations；
  - namespace handling and non-standard prefixes；
  - character encoding and date parsing；
  - HTML sanitization and content type/detail fields；
  - relative-link resolution；
  - enclosure/link/category/source projections；
  - feed-version detection and malformed-feed `bozo` signal。

`feedparser` should receive response bytes from InKCre's HTTP boundary。Its normalized mapping is adapter
input，not CanonicalFeedItem authority；known ambiguity such as RSS content-type guessing must remain visible
in product/adapter decisions rather than being treated as truth merely because the library produced it。

### Not selected as owner：`reader`

- official docs：[reader](https://reader.readthedocs.io/en/stable/)
- evidence：it deliberately provides a “fat model” with feed/entry storage、read/important state、tags、search、
  update scheduling、OPML and plugins。

Those capabilities are mature，but adopting the whole model would create competing feed persistence、source
state and application/search authority。It may be behavior research，not an InKCre runtime/domain dependency。

### Not selected：`atoma`

- latest researched PyPI release is `0.0.16` from 2018。
- It offers typed RSS/Atom parsing，but its maintenance/compatibility evidence is materially weaker than
  `feedparser` for this unit's tolerant real-world feed goal。

## Full-text extraction

### Recommended if admitted：Trafilatura

- official repository：[adbar/trafilatura](https://github.com/adbar/trafilatura)
- official API：[Core functions](https://trafilatura.readthedocs.io/en/latest/corefunctions.html)
- selected release：`2.2.0`，published 2026-07-31；the earlier research snapshot saw documentation/release `2.1.0`
- official package metadata：[Trafilatura on PyPI](https://pypi.org/project/trafilatura/)
- relevant evidence：main-text extraction、precision/recall modes、plain-text/Markdown/HTML/JSON output and
  optional metadata extraction。

InKCre should provide already-downloaded HTML plus effective URL and consume only extraction output。Do not
delegate fetching、retry、identity、storage or graph ownership to Trafilatura。

## Boundary Summary

```text
InKCre HTTP client
  -> bytes + effective URL + headers
  -> feedparser
  -> normalized third-party parse result
  -> InKCre RSS/Atom adapter
  -> CanonicalFeed / CanonicalFeedItem commands
  -> InKCre graph + resolver + source state

optional item-link HTTP
  -> Trafilatura extraction
  -> independent full-text enrichment component
```

The libraries remove protocol/parser reinvention。They do not decide source identity、canonical facts、graph
shape、reconciliation、job success、state advance、partial effects or use-facing authority。
