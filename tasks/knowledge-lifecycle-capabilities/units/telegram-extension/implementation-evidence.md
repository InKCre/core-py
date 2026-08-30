# Telegram Extension and Release Contract Implementation Evidence

## Placement

- Core/Telegram/release implementation：`.worktrees/core-py-telegram-integrated`，branch
  `feat/telegram-source-towncrier-integrated`，based on protected-main MCP PR #88 merge `459a6df`。The earlier
  `.worktrees/core-py-telegram-release` copy is a temporary uncommitted transfer backup，not the delivery branch。
- Organization guidance：`.worktrees/github-release-guidance`，branch `feat/release-lifecycle-guidance`，based on `.github`
  `origin/main` `6c7d802`。
- No commit、push、PR、publication or deployment has occurred。The original shared MCP worktree was not staged、reset、stopped
  or cleaned。

## Implemented surfaces

- Telegram：strict sender-bound Source config/state，bounded Bot API polling，semantic text/HTML persistence，metadata-first
  attachments，explicit/idempotent materialization，legacy message decoder，post-commit reaction/qualified replies，direct
  inbox documentation and Extension fragment intent。
- Release contract：PDM-managed exact Towncrier `25.8.0`，one monorepo config，Core plus Extension project discovery，impact
  classification，maturity-aware bumps，no-Git atomic preparation，feature/Release PR intent checks，minimal generated
  Release PR controller，Extension-only publication enumeration and Core-version production selection。
- Organization guidance：one tool-agnostic `RELEASING.md` and one governance link in the isolated `.github` worktree。

## Evidence so far

- PDM reused existing lock pins and added only Towncrier plus its missing development dependencies；`pdm run towncrier
  --version` reports `25.8.0`。
- Isolated preparation rendered Core `0.1.1 -> 0.1.2` and Telegram `0.1.0 -> 0.2.0`，consumed only their fragments，retained
  changelog history and left the caller Git index unchanged。
- Mixed project-impact probe classified one `app/**` plus `extensions/telegram/**` change as exactly Core + Telegram；the
  complete integrated feature diff and its generated Release PR both pass their respective intent modes。
- Telegram owned Ruff、Pyrefly、projection probes、route-schema probe and wheel/Distribution verification pass。
- The materialization route is Extension-lifecycle mounted and its isolated OpenAPI schema includes
  `/telegram/attachments/materialize`。The repository's import-only `docs/openapi.json` intentionally contains no dynamic
  Extension routes（Mail/RSS are absent for the same reason），so regenerating that Core-only artifact would not record this
  route and was not performed。
- Real production Source/Job paths against the shared migrated development database pinned bot ID `6708188051` and saved
  direct messages as ordinary semantic Blocks。Injected primary Block persistence failure rolled back and preserved the
  cursor。
- Real Job 8 consumed two new bound-private updates and finished with `saved=2`、no primary failure。It persisted plain text
  as `core.text.v1` and one captioned document as metadata-only `extensions.telegram.attachment.v1` plus an ordinary caption
  Block；the metadata had one Source provenance relation and no content child before explicit materialization。
- Explicit materialization downloaded 28,220 bytes，selected `core.image.v1` from detected content，created exactly one content
  relation and returned the same child ID on the second call。No Telegram message body、caption、attachment bytes or credential
  was emitted as evidence。
- Telegram rejected both explicit `ReactionTypeEmoji("✅")` acknowledgements with `Reaction_invalid` after durable commit。
  The Bot API's closed ordinary-emoji list does not contain `✅`，and the private chat reports no narrower reaction list。Sir
  selected supported `👍` as the replacement。The Job correctly retained the original failures as post-commit
  acknowledgement diagnostics without converting accepted content into a collection failure。
- After replacing the unsupported emoji with `👍`，real Job 9 consumed exactly one new private text update，finished with
  `saved=1`、all failure counters zero and empty diagnostics，advanced the cursor from `79632234` to `79632235` and created
  only one `core.text.v1` Block。The empty acknowledgement diagnostics prove the native reaction call completed。
- After restacking onto protected-main `459a6df`，lock、automation syntax、release contract、format、Ruff and Pyrefly pass。
  The disposable-PostgreSQL fixture now checks the actual `postgres` server binary in addition to `initdb` and `pg_ctl`，so a
  client-only Homebrew `libpq` installation follows the fixture's existing skip contract instead of producing setup errors。
  The complete `pdm run check` passes with `10 passed / 50 skipped`；real Telegram acceptance separately used the declared
  migrated Docker PostgreSQL on `wsl.win-ws.localhost` through its existing SSH tunnel。
- Final static review also parses the three changed workflow YAML files，passes `git diff --check`，and finds no stale
  `extension-version-pr` caller or runtime Changie dependency。The only remaining `.changie.yaml` reference is the explicit
  one-time migration classifier in `scripts/release.py`。
- The first PR preview exposed one release-caller regression：`build_extension_preview.py` used the new Core-plus-Extension
  discovery default and attempted to build the non-distribution Core project as an Extension wheel。The caller now requests
  `extensions_only=True`，preserving its existing producer boundary。Local discovery verifies that every selected producer is
  an Extension；the PR preview workflow owns the full build because it injects the sibling `inkcre-ext` CLI unavailable in the
  local worktree。

## Remaining verification

- None。Core-py PR #89 was squash merged as `42d8527` after required repository contract and portable database runtime
  checks passed；its accepted preview at head `624b9ef` returned HTTP 200 with database、migration、roles、privileges and
  catalog ready。Protected-main checks、Extension publication and immutable runtime artifact delivery then passed，and the
  new controller created independent Release PR #90。InKCre/.github PR #28 was squash merged as `f7269b9`。Preview resources
  and the three Unit delivery/transfer worktrees were retired；the distinct MCP peer worktree was preserved。
- The closure-only follow-up exposed that feature admission treated unchanged pending fragments already on main as if the
  current PR introduced them。`release.py check --base` now evaluates fragment intent from the current `base...HEAD` path set，
  while preparation continues to consume every pending fragment；a task-doc-only change passes with Telegram/Core fragments
  still pending in independent Release PR #90。

## Reusable execution guidance

- Future Extension acceptance that combines real external credentials、protocol behavior and production-shaped persistence
  should normally use preview after deterministic local checks。That avoids reconstructing deployment configuration and
  durable runtime access by hand while exercising the closer delivery topology。
- Repository `.env` content is dotenv input，not a sourceable shell program；URLs and credentials may contain shell
  metacharacters。Load it through application settings or a dotenv parser without emitting values。
- Shared development/preview databases are suitable for ordinary migrated integration acceptance，but not tests that create
  or destroy roles、schemas or databases；those tests retain a disposable-runtime boundary。
