# Lineage 读取复验

2026-09-13（Asia/Shanghai），应用提交为 `4a0f26644df6a2071454b8d5cd159db0dbafbd1a`，
[Preview 部署](https://github.com/InKCre/core-py/actions/runs/34704150346) 成功后执行。
使用一次性命令、已安装的 MCP SDK 和既有 Resolver Resource 接口，没有新增测试文件或生产入口。

## 结论

递归溢出修复的本地复现检查通过，但 1000 节点长链的 Preview 端到端读取没有通过。
不能以环检测函数正确替代实际读取成功，也不把这次失败归为模型语义残余。

本地环检测检查中，100/400/1000/10000 节点无环链均返回 false，闭环均返回 true。
标准库 TopologicalSorter 使用显式栈，不需要调整 Python 递归上限。

## 实际读取

Preview 初始 blocks、relations、sinks、jobs 均为空。第一段临时图为 Block 412–1411 的 1000 节点链，
`412 --supersedes--> 413 ... --> 1411`，另有 descriptor 1412 和临时 MCP Sink 1。
通过方法发现可以取得 read_lineage 的参数合同，但说明仅为默认的 `read lineage`。

读取完整链时，SDK 报 `MCPError: Server returned an error response`；本次命令没有保留该错误的完整 data，
所以不能直接断言其 MCP 错误码或服务器内部异常类型。随后 disable 请求返回 503；一个独立的 `/livez`
请求也在约 31.6 秒后收到 503，而 PostgREST 仍可查询临时图。

核对所有临时 Block 的 ID、内容和 Resolver 后，通过 PostgREST 精确删除本次 999 条关系和 1001 个 Block。
随后 `/livez` 在约 1.3 秒返回 200，Sink disable 和 delete 成功。没有重启 Peer 或修改部署配置。

第二次小图读取取得以下结果：

| 输入 | 结果 | 客户端观测耗时 |
| --- | --- | --- |
| 20 节点链，默认探索上限 | 20 Block / 19 Relation，前沿为起点，非环、未截断 | 11.599 秒 |
| 同一链，最多探索 10 节点 | 10 Block / 9 Relation，前沿为空、truncated=true | 7.188 秒 |

一次性小图命令缩小关系数量时未同步缩小批量 Block 创建范围，因此另有 80 个未连接 Block。
标为 `20-node-cycle` 的最后一次探查实际上把其中一个未连接 Block 接到链首，形成 21 节点无环链；
其非环结果正确，但**不作为闭环验收证据**。该辅助命令没有进入仓库，也未改变被测实现。
第二次全部 101 个 Block、20 条 Relation 和 Sink 2 均已清理；blocks、relations、sinks、jobs 再次为空。

## 原因与尚未批准的处理方向

read_lineage 的遍历每访问一个 Block，分别读取两个方向的 Relation 页。一条稀疏的 1000 节点链约需
2000 次关系查询，另有入口、实体读取和会话开销。这些同步 SQL 调用直接位于 async 方法内，没有线程隔离。
这是代码可确认的事实；小图耗时、长链期间健康检查超时以及清理后恢复与此一致。缺少服务端轨迹，不能精确
拆分数据库往返、Peer 调度和传输层对每次 503 的贡献。

需要分别处理两个责任：同步数据库遍历不应阻塞 Peer 事件循环；长链读取的数据库往返成本需要降低。
仅把查询放到工作线程可以改善前者，不能声称消除后者或通过 1000 节点 HTTP 读取。也不应通过提高超时、
降低默认上限或更换验收输入把失败隐藏掉。具体实现方案仍须 Sir 复核，本轮未追加代码修复。
