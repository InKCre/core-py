# 验收材料与人工判据

本页固定 D-628 的小规模软件工程 corpus。它是验收依据，不是产品 prompt、schema 或检索特殊处理。
新 Query 尚未实现，因此这里没有查询成功记录。加载后在执行证据中记录真实 ID；下面文件名不变为产品 alias。

## 版本与材料

| 材料 | 版本/来源 | SHA-256 |
| --- | --- | --- |
| SQLite Architecture | 已有 tests/semantic_retrieval/acceptance/corpus/sqlite-architecture.html；官方 https://www.sqlite.org/arch.html 的 2026-08-07 快照 | e5e00e53255dc1093fc8c087ff31b84c93dc802366392bda14e3f085776f521a |
| Graph Navigation Retrieval | 本仓库 676886a 的 docs/30-unit-tdd/graph-navigation-retrieval.md | 9e248d02cdf87d604fd62052aca98dafbfec735b11880fd6279df1380f1eb93d |
| Lexical Retrieval | 本仓库 676886a 的 docs/30-unit-tdd/lexical-retrieval.md | a162f6dfb153871a5133bd6f729f61df11f3e00569af829e8bafa6e518b68bbf |
| NASA GPM / Dave McComas 视频与作者字幕 | 既有 prepare_media_assets.py 的 origin URLs；.assets 文件仍在本机，两个原始 digest 已核对 | 视频 03168dd86fe492fed362cb64d5ce3d29989b8573cd9dfdaebfed0e11512f7427；字幕 69d12ca3151641496096e074b81749ad4f3fb173fcc08b56ce012dd1eddcc40d |

文档以固定版本所说的内容为 authority，不把文档自动当作当前运行源码事实。文档之间可互为同主题干扰项；
不使用旧人工撰写的“deep modules”feed 条目冒充外部真实文章。SQLite 保留 HTML，经 HTMLResolver
读取；技术文档以真实 text/markdown 内容入库，不给 query 注入答案摘要。

NASA 原始媒体与派生文件继续留在 ignored assets；以现有 Storage/Resolver 路径准备 media → subtitle/
transcript 等子图。优先使用作者字幕验证精确事实；若使用模型生成转录/解释，标明来源并人工对照，
不以模型输出给另一模型自证。数据准备与索引维护在 Query 外进行，保留其实际运行结果。

## 查询与预期依据

| 问题意图 | 必要依据 | 不应推导出的结论 |
| --- | --- | --- |
| SQLite 谁处理 page cache、locking、rollback/commit；B-tree 与它怎样分工？ | Architecture 的 B-Tree / Page Cache 段，pager.c 与 page-cache 职责 | 不能把 SQL parser 说成事务实现 owner；不凭常识编造快照未写的算法细节 |
| 根据这两份 InKCre 检索文档，图导航与词法查询怎样互补？ | 图导航遍历已有关系；lexical 找 Block-local 文本线索；子图文字独立索引 | 图导航不是 Resolver 解释，也不自动补齐未建模关系；lexical 不递归复制所有子块文字 |
| 已知这份媒体中的人物：他为何说软件实验室仿真并不能完成所有验证？ | 视频字幕约 32–52 秒：仿真可验证范围、实际 spacecraft/flat sat、交付后性能测试 | 不能把具体项目说明扩成“所有仿真都不可信”；不能仅凭视频 title 回答 |
| 从给定媒体 Block 找到支撑上述回答的文字依据 | 实际 media → subtitle/transcript 关系及其正文；引用应能重新打开 | 未观察到关系不能臆造；Query 不因问题而重写 graph |
| 这些材料能否给出原始图片中某处颜色，或哪项设计在所有场景都性能最优？ | 材料缺少必要依据/本轮不能查看原始媒体 | 必须区分未能理解与不存在；不得用无引用常识作确定结论 |

复述查询时不增加指向答案的工具顺序提示。评审看答案是否回应问题、引用是否对应证据、推论有无
越界；不要求句子相同、引用顺序相同、固定最短图路径或命中固定数据库 ID。

这是最小验收集，不宣称覆盖全部 retrieval 难度。若轨迹只用标题即可命中全部答案，应增强真实材料
干扰/问题，而不是让实现识别 corpus。预算值与 prompt 的调整要记录原轨迹和改动原因。
