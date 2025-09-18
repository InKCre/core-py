## Fundaments

- [ ] 可观测性
  - 日志

### AI

- [ ] 服务提供商不是字符串而是对象，模型亦然
- [ ] 自动路由
- [ ] 多提供商多凭证管理
- [ ] 添加 `MarkdownMessageContent`
  - 可以由其它 `MessageContent` 组成 (比如 `CSVMessageContent`)

## Base

- [x] 添加插入图接口
  - [x] 不插入重复的块和关系。（当前实现是判断解析器、内容、存储器字段一致；来源、去向、内容一致。未来考虑将内容一致性的判断交给解析器）

## Block

- [ ] 确保 Embedding 使用的模型一致
- [ ] 定期检查 Embedding 是否过期，过期则刷新
- [ ] 推理检索不一定要基于 LLM，可以基于传统规则（如 Resolver 自己配置的，举例 learn_english.lexical）
- [ ] 向量检索多模态对齐问题
  - 为不同的模态的向量设置不同的列

## Source

- [x] Run collect intervally. 
  Each source can has their own interval.
- [x] Collected data will be organized later by running a background task for each data item using `organize` of its resolver.
- [ ] Collect is an active way to gather data. Source should be able to configure webhooks or other ways to passively gathering data. Source can done this in `start` method which will be called once the application starts.
- [ ] Provide an API Endpoint for remote source (out source) to commit collected data. Collected data will be organized automatically also.
- [ ] 和 Resolver, Storage 一样采用子类自动注册的方式

## Resolver

- [ ] Standard of auto organization ? 
- [ ] Resolver relies on Storage to get the actual content (don't do it yourself, never considering what storage is)
- [ ] 改进加载模式
  - 在未找到时，按照类型（和 Python 导入路径语法一致）尝试从插件中导入 （否则插件就需要在初始化时导入）

## Extension
- [ ] Run `pdm install` to install dependencies the extension required when install or upgrade an extension.
- [ ] Create `data/extensions/<ext_id>/` folder for extension to locally store its data.
- [x] Add lifespan management: start and close.
- [ ] 使用 git submodules ？ 

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
- [ ] Use state to store the latest post

### Github

### Telegram

### Rsshub
