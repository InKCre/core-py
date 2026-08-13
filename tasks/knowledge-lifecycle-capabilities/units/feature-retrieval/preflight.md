# Lexical Retrieval Preflight

## Observed Repository Facts

- core-py semantic retrieval already proves use-owned projection maintenance、derived rows、freshness filtering、bounded exact
  ranking、fixed Peer inbound and caller-local `route_to_peer`。
- Python Resolver has `get_text()` and `get_label()`；direct content fallback is explicitly forbidden。RelationManager owns one
  directed text projection。
- client-web still declares and implements `getStrForEmbedding()` even though D-095/D-096 and core-py hard-cut that contract。
- client-web can delegate semantic retrieval but has no retrieval UI；the start view contains only a console-log placeholder。
- client-web's app-bound `InfoBaseRouter` currently projects every Block destination into GraphSurface even though the shared
  InfoBase contract already defines future ListSurface as a peer navigation host。GraphSurface itself owns
  `BlockInspectorPopup` and `SolvedContentPopup`。Lexical results are therefore the first concrete pressure to implement
  InfoBaseListView and preserve the active host during route projection instead of navigating away from result context。
- client-web already runs the shared Job worker but has no local semantic/lexical Handler；capability-specific `can_handle`
  remains the correct eligibility boundary rather than disabling its global worker。
- GraphSurface currently loads all Blocks/Relations and can focus only after it receives a known Block reference。
- core media solved values already expose useful metadata，while their general `get_text()` correctly remains unsupported in the
  absence of content extraction。Mail MIME-part resolver already demonstrates a bounded metadata text projection。
- PostgreSQL supplies literal matching、`tsvector/tsquery`、cover-density ranking、headline extraction and preferred GIN text
  indexes。`pg_trgm` supplies indexed `LIKE/ILIKE` and similarity as separable operations。PostgREST supports FTS filtering but
  does not by itself own the required cross-signal ranking/evidence contract。

Primary references：

- PostgreSQL text parsing/ranking/headline：https://www.postgresql.org/docs/current/textsearch-controls.html
- PostgreSQL preferred GIN/GiST indexes：https://www.postgresql.org/docs/current/textsearch-indexes.html
- PostgreSQL text-search limits：https://www.postgresql.org/docs/current/textsearch-limitations.html
- PostgreSQL `simple` dictionary：https://www.postgresql.org/docs/current/textsearch-dictionaries.html#TEXTSEARCH-SIMPLE-DICTIONARY
- PostgreSQL `pg_trgm`：https://www.postgresql.org/docs/current/pgtrgm.html
- PostgREST FTS filters：https://docs.postgrest.org/en/v14/references/api/tables_views.html#full-text-search

The local SVC database provisioner was inspected but not repaired：its existing image build lacks
`release/database-contract/`。SVC cleaned the failed attempt。The installed `neonctl` shim is also broken by a missing global
module。Neither tool failure is evidence against the retrieval design，and neither side branch is expanded in this Unit。

The legacy local `.env` is not a current application runtime credential：it still names `DB_CONN_STRING` and the stored Neon
owner password now fails authentication，while current Settings require `DATABASE_URL` + `JWT_SECRET`。Implementation setup must
obtain/rebind a current development/preview database credential rather than silently treating this file as runtime truth。

The same file's DashScope key remains usable for a read-only OpenAI-compatible catalog probe。The current catalog exposes exact
candidates including `qwen-vl-ocr-latest`、`qwen-audio-3.0-asr-flash`、`qwen3-asr-flash-2026-02-10`、`qwen3-omni-flash`、
`qwen3.5-omni-flash` and `qwen3.5-omni-plus`。Catalog visibility proves naming/access only；real content-part + Tool-call
journeys remain Acceptance evidence and no model ID becomes a code/config default。

On 2026-08-12，minimal streaming text requests with `modalities=["text"]` completed successfully through the current workspace
for `qwen3.5-omni-plus`、`qwen3.5-omni-flash` and `qwen3-omni-flash`。The earlier HTTP 403 policy gate is therefore resolved。
Separate real image、audio and public-MP4 video calls with the accepted function Tool all returned a `submit_graph` ToolCall
through Alibaba's OpenAI Chat endpoint for each candidate Model。A generated valid H.264 MP4 sent as actual base64 bytes also
returned the ToolCall，so the production shape is not justified only by public-URL success。No Model ID becomes a code/config
default or automatic fallback。

The transport facts are now separated precisely。OpenAI's own Chat Completions contract defines `image_url` with URL/base64 data
and `input_audio` with base64 data + `wav|mp3`；it does not define `video_url`。Alibaba's OpenAI Chat surface adds `video`/
`video_url` and permits audio URL/Data URL，alongside function calling for the relevant Omni family。The current repository
adapter is exactly `core.openai-compatible.v1` and uses `openai.AsyncOpenAI.chat.completions`；the SDK is only a client，not
evidence that Alibaba extensions belong to the generic protocol。Under D-157/D-158's accepted cross-capability dialect topology，
the current proposal is `core.alibaba-model-studio.v1` rather than a new capability/endpoint-prefixed `core.openai-chat.v1`。
Native DashScope remains dominated until the documented Chat surface fails a required behavior。

The bytes spike exposed one real product bound：the 16,242,564-byte NASA MP4 expands past the endpoint's 20 MiB data-URI item
limit，whereas a bounded valid H.264 clip succeeds。Alibaba recommends small original inputs for base64 and provides temporary
upload URLs only for development/testing with region、model and lifetime constraints。The review proposal is therefore a
conservative 7 MiB original-byte maximum per inline media part in this MVP。A larger part may use an optional Storage-owned
origin transfer URL when the exact dialect supports it；otherwise its exact derivation/interpretation is unavailable。Adding
Alibaba temporary upload or OSS staging here would add a provider-specific media lifecycle and contradict the earlier decision
to defer S3/object storage until real storage pressure。

The multimodal corpus is now concrete：NASA's official asset API returns MP4 + authored VTT for
`GSFC_20140121_GPM_m11457_Dave_McComas`；the small MP4 was observed as `video/mp4` with ETag
`6a03adc2cf2e56872d639459541c7533-2`，and its captions contain meaningful flight-software requirements/test language。A bounded
acceptance setup can derive audio/frame and remux subtitles outside production code。NASA's current media guideline says its
content is generally available for educational/informational use while protecting insignia/logotype/identifiers；the acceptance
bundle retains provenance and does not present NASA endorsement。

Current branch delivery is not a clean implementation baseline。After fetching latest heads on 2026-08-12，core-py's
`feat/synchronized-client-v3-restacked` is 6 commits behind / 17 ahead of `origin/main`，and client-web's
`feat/synchronized-core-v3` is 14 behind / 6 ahead。A merge-tree preview exposes overlapping changes in both repos，so I0 must
reconcile the branches before implementation instead of leaving conflict resolution to preview delivery。

The current core PR #45 preview failure is an orchestration precondition failure，not a migration failure：`preview-verify`
waited for required exact-head checks that never became green and delivery never reached database initialization。The checked-in
preview workflow later creates/resolves a data-free Neon branch，runs `db init --environment preview` and database-contract
verification，deploys exact-head images and probes `/readyz`。That makes a green core preview an appropriate final proof for the
large migration。client-web PR #50 builds its own static Cloudflare preview but CI normally resolves a stable core release，so
the final cross-repo J7 must explicitly bind the built client to PR #45's live core preview。

Primary protocol references：

- Alibaba OpenAI Chat：https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-openai-chat-completions
- Alibaba Responses：https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-openai-responses
- Alibaba API interface comparison：https://www.alibabacloud.com/help/en/model-studio/qwen-api-reference/
- Alibaba temporary upload：https://www.alibabacloud.com/help/en/model-studio/get-temporary-file-url
- Alibaba error/data-size guidance：https://www.alibabacloud.com/help/en/model-studio/error-code
- OpenAI Chat Completions create contract：https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create
- OpenAI image input guide：https://developers.openai.com/api/docs/guides/images-vision
- OpenAI audio input guide：https://developers.openai.com/api/docs/guides/audio

## Alternatives Rejected Before Human Review

| Alternative | Why dominated |
| --- | --- |
| Search `blocks.content` directly | treats storage pointers/source JSON as content，bypasses Resolver，misses solved metadata |
| Resolve every Block during each query | O(N) hydration/network/CPU per read，no scalable entry path，evidence changes during ranking |
| Put ranking in a PostgREST RPC/computed business function | moves domain behavior into the database and repeats the rejected semantic-retrieval topology |
| External Tantivy/Elasticsearch service | adds operational authority、peer-local persistence and synchronization before PostgreSQL is insufficient |
| One universal Feature table/profile/manager for lexical and perceptual | no shared representation or matching lifecycle has been proved；would become a god abstraction |
| Language stemmer/profile table in V1 | multiple selectable profiles lack current identity/reuse value；stemming damages identifiers and does not solve CJK |
| Trigram fuzzy search by default | introduces a second approximate semantics and opaque threshold when literal+terms already solve the target job |
| Generic solved-content scalar serialization | leaks Resolver schemas、indexes bytes/noise and removes Resolver's judgment over meaningful features |
| Index Relations in lexical V1 | overlaps graph-navigation ownership，creates endpoint-label result floods and lacks a clean current UI destination |

## Failure-Branch Preview

| Branch | Proposed behavior |
| --- | --- |
| empty/whitespace query | Pydantic/Zod validation failure |
| punctuation-only query | literal path remains valid；empty `tsquery` is simply omitted |
| Chinese/no-space fragment | escaped literal substring path；no claim of linguistic segmentation |
| unknown Resolver | maintenance diagnostic；other Blocks continue |
| unsupported default text but available lexical metadata | lexical context produces a record without unnecessary materialization |
| lexical text requires an absent derivation | maintenance permits Resolver-owned materialization；query remains read-only |
| no lexical text beyond generic label | label-only record remains searchable |
| record missing/stale | excluded from retrieval；query does not repair it |
| storage/Relation changes without Block timestamp | known best-effort freshness gap；explicit rebuild，no speculative dependency graph |
| projection exceeds PostgreSQL engine bound | diagnostic/unavailable，no silent truncation |
| concurrent maintainers | equivalent upsert；possible duplicate work accepted |
| Resolver materializes a child after the current scan cursor | scan may index it later in the same invocation；otherwise the next Job does；`max_records` prevents unbounded self-extension |
| concurrent missing materialization creates equivalent child Blocks | singular graph reads may use any one；distinct Blocks may both be retrieved；no retrieval-owned dedupe or stability promise |
| no capable Peer from browser | existing capability-unavailable behavior |
| post-dispatch unknown outcome | existing Peer outcome-unknown behavior；read operation is not replayed by generic infrastructure |
| literal text contains `%`/`_` | manager escapes wildcard characters before `ILIKE` |
| excerpt contains authored markup | lexical projection contract is plain text；UI renders interpolation，never `v-html` |
| no locally executable media Agent | parameterless Job remains pending and claimable after configuration/runtime changes |
| only some modality Agents are executable | one Peer may claim and process that subset；other candidates remain missing for a later independent Job |
| provider rejects a statically valid media call | candidate diagnostic，continue bounded scan，no fallback or claim rollback |
| streamed multimodal ToolCall deltas are malformed/incomplete | dialect raises output-contract failure；Agent never receives a partial AssistantMessage |
| inline media exceeds the exact dialect's accepted byte bound | use an accepted Storage transfer URL if present；otherwise unavailable；no hidden provider upload、retry or truncation |

## Remaining Review Pressure

The proposal is intentionally opinionated。D-320—D-322 now close primitive matching、derived records、permitted missing
materialization and Block-local/non-recursive lexical projection。

D-323/D-324 reopen and close two missing high-level boundaries：multimodal textualization remains in lexical scope，and lexical/
semantic maintenance use the database-owned Cron → typed Job → one capable Peer claim topology。

System-driven media Organization is closed at the topology level。Repository evidence shows image/audio/video solved values
already carry hydrated bytes and typed metadata，so Organization can consume `get_solved_content()` without another Resolver
projection。The AI schema stores modalities while canonical Chat messages and `AIManager.chat()` hard-code text input；the
remaining adapter work belongs to the AI call boundary。D-327—D-331 close missing-only candidates、independent Agent ownership、
per-modality routing、separate information-role text children and the parameterless convergence Job。The solved-content → Agent
seam has one coherent shape：Organization
builds an AI-owned UserMessage with textual graph context plus actual media bytes/MIME；AIManager validates modalities and the
dialect alone encodes provider content items。Block/Storage references、provider URLs and Resolver-owned AI projections are all
dominated by their cross-domain coupling。

Faithful-text selection likewise derives from existing ownership：image/audio/video Resolvers each own their exact config，with
Model references scoped to `text` or `transcript` roles；source-native subtitles need no AI config。A shared media config would
invent an owner，while Agent reuse would duplicate Resolver prompt/write authority。Provider/model/payload support is now proved
for the exact acceptance shape；the remaining review pressure is whether bounded inline media is an acceptable product limitation，
not another configuration topology question。

The implementation address audit found no hidden competing path：core-py has one legacy semantic maintenance interval in
`run.py`；client-web's Resolver base still requires `getStrForEmbedding()`；its core image/audio/video/PDF Resolvers currently
stop at metadata/unsupported text；and the start view's submit handler only logs the query。These are direct I1/I4/I6 cutover
surfaces，not new product decisions。

Job eligibility needs one shared implementation seam but no new scheduling semantics。Current `JobManager` calls synchronous
`can_handle` before atomic claim；there is no public AIModel/Agent executability predicate yet。AIManager can own static
Model/Provider/dialect/config/modality checks and AgentManager can compose Agent/Tool checks。Neither may call the provider or
promise key/quota health；the resolved earlier Omni 403 remains evidence that static eligibility cannot guarantee execution。

The parameterless media Job does not imply all-or-nothing fleet convergence。Requiring every configured modality Agent at
claim time would make one deliberately unavailable slot block useful work，while three Job types would move candidate-local
modality back into Cron templates。The accepted best-effort boundary is therefore: at least one local modality makes the Peer
eligible，successful Relations are progress，and unsupported candidates remain discoverable by the next independent Job。

Primary provider evidence confirms that this is implementable through an exact Alibaba OpenAI Chat dialect rather than a
hypothetical API。Because the canonical capability returns one complete text/ToolCall AssistantMessage，that adapter can stream
and internally assemble the same output；no provider streaming state crosses the dialect boundary。Provider limits remain
adapter/provider outcomes rather than lexical query semantics。

Primary corpus/provenance evidence：

- NASA asset API：https://images-api.nasa.gov/asset/GSFC_20140121_GPM_m11457_Dave_McComas
- NASA media-usage guidelines：https://www.nasa.gov/nasa-brand-center/images-and-media/

D-325/D-326 require active model-authored interpretation through Organization and define “active” as non-user-driven。This is a
new automatic media-interpretation approach rather than a reason to route media through current text-only focal rumination。
