# Feature Retrieval

- **Unit ID**: `feature-retrieval`（产品与技术 ownership boundary 已成立；内部按可独立交付的 increment 推进）。
- **State**: **Execute complete locally；Verify/Promote in progress**。
- **Objective**: 从真实 information-finding jobs 倒推 semantic similarity 与 graph navigation 之外缺少的 retrieval
  capability，使用户或 Agent 能从持续增长的 info-base 中定位有用的 Blocks/Relations，并得到足以理解“为什么命中”
  的 evidence。文本、图像、音频、视频、文件、source 与 graph facts 都可以进入发现视野。
- **Guardrails**: 不把“特征”先验定义为 metadata filters、全文搜索、embedding 之外的剩余集合或 modality operator
  checklist；不为了宣称 multimodal 而预先批准 OCR、object detection、transcription、EXIF、perceptual hash 或新
  indexes。先区分 evidence authority、matching/ranking mechanism、query composition 与 result explanation。
- **Representation-sensitive ownership**: retrieval ownership 取决于 evidence 当前在 info-base 中的表示，而不是其
  现实世界分类。仍嵌在 PDF content / Resolver lexical projection 中的 filename、page count、MIME 等只能作为
  feature evidence 被发现；Organization 将有 use value 的 facts 拆成 Blocks/Relations 后，后续定位与探索由
  graph-navigation-retrieval 承担。Feature retrieval 不因此扩张为任意 schema-aware field-query engine。
- **Current Truth**: core-py now owns Resolver lexical projection、`block_lexical_records`、bounded maintain/rebuild Jobs、
  exact local/delegated capability、multimodal faithful materialization、Alibaba Model Studio dialect and system-driven media
  interpretation。client-web now owns the peer facade、InfoBaseListView and List-hosted Inspector/SolvedContent outlets。The
  real NASA image/audio/video → PostgreSQL Storage → Resolver → provider → graph → lexical → Organization Agent journey passed；
  core's hermetic contract passes after the `origin/main` extension-registry integration with 445 tests and 41 external skips；
  a fresh PostgreSQL database also passes migration、init and readiness against the merge revision。Render API mechanics pass
  simulated contract tests，and real account inputs are ready；live creation remains pending in this acceptance run。
- **Verification Direction**: Acceptance 最终必须以真实 collected graph 和用户可判断的 finding tasks 证明新增能力
  补足了 semantic/graph retrieval 不能合理完成的工作；不能以 operator 数量、schema round-trip 或人工构造的 query
  fixture 代替产品价值。J1–J7 已冻结 exact identifier、中文片段、Mail attachment metadata、freshness、PDF body、
  multimodal textualization/interpretation 与 browser recall actors；具体合法媒体 asset provenance 在 execution
  preflight 固定，不进入生产实现。
- **Internal decomposition**: lexical retrieval 与 perceptual retrieval 都属于 feature retrieval；前者是必做的第一
  increment，后者后续按真实模态场景继续切分。Graph 中的 fact/relationship 定位由 graph-navigation-retrieval
  承担；hybrid recall 是各基础 retrieval 能力成立后的组合层，不反向模糊本 Unit 的边界。
- **Multimodal lexical scope**: perceptual matching 延后不代表媒体文本化延后。Image OCR、audio speech transcription、
  video subtitles/transcription/on-screen text 等 faithful text derivations 必须能通过 Resolver materialization 变成
  ordinary text Blocks，并进入同一 lexical-record/query path；模型生成的描述/摘要由 system-driven Organization
  主动产生为 interpretation graph，再进入同一 lexical path，而不是被 `materialize_missing` 偷渡成 Resolver effect。
  Organization 通过 existing `get_solved_content()` 理解媒体，不引入平行的 Resolver media projection。忠实文本化按
  信息角色分别形成 `text`、`transcript`、`subtitle` child Blocks，不合并为来源不明的聚合文本。
- **Current Question**: no unresolved product/technical fork blocks implementation。Public JWT publication is deferred under
  D-340；D-341 separates fork-based self-host onboarding from the canonical production demo。The remaining evidence is a real
  Render account-backed service creation、cold-start probe and matching PR previews。
- **Next Step**: Sir 已授权 delivery closure。先完成 core/client 与主线的合并、push 与 exact preview regression；再以
  preview 执行 matching J7，并独立运行 checked-in Render + Neon fork workflow，关闭 host-specific operational probe。
  两条 journey 共享产品产物，但 canonical preview/demo 不被 fork workflow 配置或重定义。
- **Delivery Gate**: implementation is not accepted after local checks alone。After separately authorized commits and pushes，
  the current core-py and client-web PR previews must both pass；core-py's preview must prove fresh migration/database readiness，
  and the built client journey must target the matching live core preview rather than a stable-release substitute。
- **Decision Authority**: D-316—D-342；D-336—D-338 close Alibaba dialect、Storage transfer hints and AI ContentPart ownership，
  D-339 fixes Render Free as the sleeping self-host profile，D-340 keeps signing authority private，and D-341/D-342 separate
  self-host identity from canonical production plus manual black-box acceptance from automated regression checks。
  后续决定继续追加到 program decision register，不在本 packet 重复。

## Working Proposal Navigation

- [Product design](product-design.md)：user job、feature/semantic/graph boundary、plain-query matching and result meaning。
- [Technical design](technical-design.md)：Resolver projection context、derived records、PostgreSQL execution、Peer and UI topology。
- [Preflight](preflight.md)：observed code facts、rejected alternatives、failure branches and remaining review pressure。
- [Acceptance](acceptance.md)：real producer corpus and seven end-to-end journeys。
- [Implementation plan](implementation-plan.md)：approved-boundary execution order；not implementation authorization。
- [Deployment readiness](deployment-readiness.md)：accepted GitHub-only Render + Neon self-host contract、implemented controller
  and remaining live-host probe。
