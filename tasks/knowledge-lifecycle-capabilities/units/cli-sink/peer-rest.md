# Peer 记录与 HTTP 唤醒接入

状态：按 [D-592](../../decisions/D591-D600.md) 确认，尚未实施。基于 D-573/D-574 的产品范围与 D-582 的命名连接。

## 读取接口

| REST | CLI | 返回 |
| --- | --- | --- |
| GET /peers | peer list | deployment 中的 Peer 记录 |
| GET /peers/self | peer get 未提供 ID | 当前 REST 接入 Peer 的记录 |
| GET /peers/{id} | peer get <id> | 指定 Peer 的记录，缺失为 404 |

沿用 PeerManager.get/get_all/get_current_peer_ref，Peer ID 仍是 UUID。self 是当前 REST 接入 Peer 的内置别名，
在协议入口解析，不是持久 nickname，不引入 alias 表或任意 nickname 查找。静态路径不得被参数路由遮挡。
基础记录保留 name、labels、config、config_schema、capabilities、lease_expires_at 与时间戳；
读取不经 capability_snapshot 重验整个广告。列表分页与紧凑显示沿 D-597 的[共同管理合同](list-error-contract.md)。

增加响应计算字段 lease_active，由 Core 在同一读取操作中按数据库时间比较 lease_expires_at。它只说明
租约是否有效，不命名为 online，不将它等同于此刻网络可达。CLI 无需用本机时钟推断，也不新增状态表或历史事件。

## 唤醒直接使用命名连接

本轮保留轻量 peer wake，使用本次已选的 CLI connection：

```sh
inkcre-cli --connection personal peer wake --for 60s
```

直接请求该 base_url 下既有 GET /readyz，并在指定预算内观察到就绪。无需先 GET /peers，也不新增服务端
POST wake，不经过 Peer delegation。--for 的默认值、过程输出与超时退出码随有界命令共同合同收敛；例中的
60s 是显式预算，不预设新默认值。

另一台提供 REST 的 Core 可保存为另一条 connection。此方案不接受裸 Peer ID 并自动猜 HTTP 地址，也不从
任意 capability inbound URL 裁剪 REST base；后者声明的只是某个精确业务协议，不承诺完整 Core REST。
Peer row 的 config 是 owner-defined JSON，当前也没有统一的 REST endpoint advertisement。为省去录入一个
地址而增加跨 runtime REST endpoint registry，当前收益不足。

Sir 接受上述最小操作，同时指出通用唤醒尚未规范化。当前合同只是请求并有界等待已配置 HTTP 入口就绪，
是否因此启动实例由部署平台决定；不承诺启动任意离线进程，也不将未来唤醒协议列为本 unit 前置工作。
唤醒依靠已配置的入口，不能直接从 peer list 的任意 ID 一步唤醒。
不因此撤回未来不同 Peer 对等、协议异构的定位，也不把没有 REST 的 Peer 表达为坏掉的 Peer。

## 核验依据

app/business/peer/main.py 已有记录读取、自身 ID 与基于数据库时间的 lease 筛选；app/schemas/peer/main.py
保留完整 PeerModel，没有统一 REST 地址字段。CorePeerConfig.http_public_base_url 是 core-py owner 的本机
HTTP 配置，不是所有 Peer 的协议。run.py 的 /readyz 已返回 200/503 和 readiness payload。
app/routes 目前没有 Peer 管理 router。以上仅是设计与源码证据，未修改源码或执行实际唤醒。
