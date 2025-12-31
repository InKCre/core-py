# InkCre/core-py TODO

## Fundaments

### Observability

- [x] 持久化日志（主要是为了 source collect job）（与 OpenTelemetry 对齐）（复用 PostgreSQL）
- [ ] 使 `OBSRV__LOGGING_BACKEND` 为数组

### AI

- [ ] 服务提供商不是字符串而是对象，模型亦然
- [ ] 自动路由
- [ ] 多提供商多凭证管理
- [ ] 添加 `MarkdownMessageContent`
  - 可以由其它 `MessageContent` 组成 (比如 `CSVMessageContent`)

## Source

- [x] Run collect intervally. 
  Each source can has their own interval.
- [x] Collected data will be organized later by running a background task for each data item using `organize` of its resolver.
- [ ] Collect is an active way to gather data. Source should be able to configure webhooks or other ways to passively gathering data. Source can do this in `start` method which will be called once the application starts.
- [x] 和 Resolver, Storage 一样采用子类自动注册的方式
- [x] Source.collect 不应该有参数
- [ ] Organize 不是 source 的职责，而是整个信息库的。Source会在 organize 过程中提供帮助，但绝不是 source 来执行。
- [x] Source 也要有 state，反而是 extension 不应该有 state
- [x] SourceType also has config schema  !!! 不是 Source，是 SourceType
- [ ] 严重 auto collect

## Info-Base

- [x] 添加插入图接口
  - [x] 不插入重复的块和关系。（当前实现是判断解析器、内容、存储器字段一致；来源、去向、内容一致。未来考虑将内容一致性的判断交给解析器）

### Block

- [x] fetchsert 由 resolver 来决定是否相同

### Resolver

- [ ] Standard of auto organization ? 
- [x] Resolver relies on Storage to get the actual content (don't do it yourself, never considering what storage is)
- [x] 改进加载模式
  - 在未找到时，按照类型（和 Python 导入路径语法一致）尝试从插件中导入 （否则插件就需要在初始化时导入）
- [ ] 规范化 Resolver，其负责解析 Block 的 StarGraph

### Storage

- [ ] 你 StorageType 用后端的路径...那我问你其它客户端怎么办？？？

## Sink

- [x] Embedding 也是 interval job 运行
- [x] Embbedding 等 indexing 都是 Sink 的职责
- [x] 定期检查 Embedding 是否过期，过期则刷新
- [ ] 确保 Embedding 使用的模型一致
- [ ] 向量检索多模态对齐问题
  - 为不同的模态的向量设置不同的列
- [ ] 真正地实现 RAG <https://blog.yakkomajuri.com/blog/local-rag>
- [ ] 推理检索不一定要基于 LLM，可以基于传统规则（如 Resolver 自己配置的，举例 learn_english.lexical）
- [ ] 结构有点混乱，应该有 RAGSink, 而不是 Sink.rag
- [ ] GraphSink 提前做社区分析

## Extension
- [x] Run `pdm install` to install dependencies the extension required when install or upgrade an extension.
- [ ] Create `data/extensions/<ext_id>/` folder for extension to locally store its data.
- [x] Add lifespan management: start and close.
- [ ] 使用 git submodules ？ 
- [ ] 插件提供将升级的迁移放在 `extensions/<extid>/mirgations/` 中，upgrade / downgrade 会执行；
      关键的一件事就是迁移 SourceType
- [ ] 移除 disabled 字段，添加 enabled uuid array 字段
- [ ] 拆分 toggle_extension 为 enable_extension 和 disable_extension

## Client

- [ ] 建表
- [ ] 自身初始化

### Twitter

- [x] Introduce a unified interface for fetching bookmarks, user and other stuff from Twitter.
  Current `auth.py` will be a kind of backend: `OfficialAPIBackend`.
  And we are going to introduce `twikit` backend.
  Only one backend can be enabled, config it at `config.backend`.
- [ ] Remove medias link in text
- [x] Add twikit exception handling
- [x] Close APIClient when close the application.
- [ ] Twikit get_tweet_id and _get_more_replies has a bug: last item of entries does not has `itemContent` in `content`, should directly read `value` from `content`
  Follow up this [PR](https://github.com/d60/twikit/pull/377) for solving this issue.
- [ ] Twikit type annotation for tweet.urls are wrong, it should be `list[dict]`, not `list[str]`

### Email

- [x] 测试 IMAP Source 可以收集最近的邮件
- [x] 优化 IMAP Source : 避免重复的部分，比如收件人、发件人；支持配置仅收集 body_text 或 body_html
- [x] Mark collected as seen
- [ ] 优化 IMAP Source: 也收集附件

### Github

### Telegram

- [x] 通过 Webhook 收集消息 / 通过 Collect Job 收集消息
- [x] ExtensionConfig 其实是 SourceConfig
- [x] 仅收集消息内容，不收集用户信息
- [x] FIXME 没有 set webhook !

### RSS

## Trivias

- [x] indent 修改为 2 spaces
- [ ] Github CI environment
- [ ] AGENTS.md / Agent Skills to keep coding guideline (schema, business, basic pattern like use class, extension skill)
- [ ] 将 migration/versions 添加回 git （但是从头来过，更干净）（也是 CI/CD 自动化测试、Copilot Agent 的重要前提）
- [ ] Build agent loop
