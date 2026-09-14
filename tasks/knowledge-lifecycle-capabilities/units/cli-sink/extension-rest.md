# Extension 管理 REST

状态：按 [D-593](../../decisions/D591-D600.md) 确认；尚未增加源码或改变 Extension 生命周期。

## 接入点与执行目标

本机 connection 选择一个 Core REST 接入点。安装记录与 config 属于 deployment；本提案通过该 Core 的
ExtensionHost 读写，不为这些操作增加 `--peer`。启用和禁用针对某个 Peer 的运行实例，因此额外支持
`--peer <uuid>`，REST 对应可选 query parameter `route_to_peer`。省略时操作接入 Core 自己，不自动挑选其它 Peer。

```text
CLI --connection personal extension enable <namespace/name> --peer <uuid>
  → 接入 Core POST /extensions/{namespace}/{name}/enable?route_to_peer=<uuid>
    → ExtensionHost.manage(EnableExtensionCommand, route_to_peer)
      → 本机 manage_local，或已有 PeerManager.delegate
        → 目标 Peer 的非委托 manage_local
```

CLI 不查目标 Peer 的 inbound URL，不签发另一套 Peer 请求，也不直接修改 enabled 数组。指定目标无法执行时
沿用该领域的真实错误，不在别的 Peer 启用。既有 `/extension-management` 仍是 non-delegating Peer inbound；
不把它暴露成 CLI 的通用 management 命令，也不在本轮为了 REST 包装扩展它的 command union。

配置写入返回共享记录，调用接入 Host 已有的配置更新路径；不承诺向全部运行 Peer 广播或重启。
既有 Peer command 的 `patch_config` 分支仍保留，但不据此要求 CLI 的每种配置操作都选择执行 Peer。
若后续出现必须在另一个运行实例执行配置回调的具体需求，再讨论该操作的目标选择，而非先增加通用代理。

## 命令与请求

以下用 `E` 代表 `/extensions/{namespace}/{name}`；CLI 的标识仍为 canonical `namespace/name`。

| CLI | REST | 输入与结果 |
| --- | --- | --- |
| `extension list` | `GET /extensions` | D-600 的 extensions 清单与 next_cursor；元素仍为已安装记录 |
| `extension get <name>` | `GET E` | 一个已安装记录 |
| `extension install <name> --version <exact>` | `POST E?version=<exact>` | 沿用现有 exact-version 安装操作，200 返回已安装记录 |
| `extension uninstall <name>` | `DELETE E` | 沿用现有卸载操作，成功 204 |
| `extension config get <name>` | `GET E` | CLI 取出记录的 config，不新增相同目的的 GET route |
| `extension config replace <name> --input config.json` | `PUT E/config` | body 直接是完整 config object；200 返回更新后的已安装记录 |
| `extension config update <name> --input patch.json` | `PATCH E/config` | body 直接是浅层 patch；200 返回更新后的已安装记录 |
| `extension enable <name> [--peer <uuid>]` | `POST E/enable[?route_to_peer=<uuid>]` | 无业务 body；200 返回已安装记录 |
| `extension disable <name> [--peer <uuid>]` | `POST E/disable[?route_to_peer=<uuid>]` | 无业务 body；200 返回已安装记录 |

新 REST 增量为 PATCH config 和 enable/disable 的目标参数；保留已有 install 的 method/path/version query，
不为格式整齐改造成另一种发布、升级或通用 CRUD 协议。CLI 不自动选择 latest、安装后自动 enable，或为安装
创建后台 Job。已有 Host 操作的同步结果仍是本次请求结果。

replace 与 update 共用 ExtensionHost.update_config 的写入路径；update 由已有 patch_config 浅层合并。
未出现字段不变，嵌套 object/array 整体替换，null 是配置值而非删除字段指令；要移除字段使用完整 replace。
CLI 不先 GET 再自行合并 PATCH。HTTP handler 只负责请求映射与错误表达，不持有这套合并业务。

## 记录与动态配置合同

继续使用现有 InstalledExtension 投影：name、version、enabled、nickname、config、config_schema。
enabled 保留 Peer UUID 数组，不改为一个与接入点相关的 bool；不新增推测的 running/online 状态。
Extension-produced state 按现有 DTO 的 exclude 合同不进入 generic management 输出。

配置输入和 `--schema` 从对应安装记录的 config_schema 发现，CLI 不附带各 Extension 的模型。
config_schema 目前允许 null；该事实必须如实表达，不能以启用 Extension 为 schema 查询的副作用。
准确的 schema-unavailable 呈现与其它动态发现入口在共通输出收敛时统一，不伪造一份完整的 Extension schema。

配置更新仍需在有实际 schema 的输入边界建立合同；与 D-591 一起核验当前 Host、runtime、store 的调用链，
避免外部写入没有校验而内部 get/转换反复校验的倒置。尤其不能机械删除首次加载模型的检查：安装后尚无
config_schema、允许先保存 config 的路径，没有证明这些数据已经通过 Extension 的具体模型。
此处是首次建立合同与重复校验的区别，不撤回 D-590 的普通记录读取边界，也不扩张为强制先启用才能配置。

## 已核实的实现交点

- `app/routes/extension.py` 已有上表除 PATCH 与 route_to_peer 外的 HTTP 操作；GET 返回 InstalledExtension，
  PUT config body 为 config 本身。隐藏的 `/extension-management` 直接调用 manage_local。
- `app/business/extension/main.py` 的 manage 已按 exact Peer 在 local execution 与 delegation 间选择，
  command union 当前为 enable、disable、patch_config；patch_config 已浅层合并后调用 update_config。
- `app/business/extension/state.py` 负责实际持久操作与 InstalledExtension 投影；配置尚未运行时的 update
  当前直接交给 store，而 runtime 启动后才发布 config_schema。这是 D-591 校验调查需要保留的首次输入情形。
- `docs/40-deployment/native-extension-distribution.md` 与 Extension 局部指南拥有安装/启用/运行的既有合同；
  REST 包装不是重新设计或重新审批这些生命周期的理由。
- 当前 client-web 的 `apps/client-web/src/components/extension/extensionCard/extensionCard.vue` 调用自己的
  WebExtensionHost；`packages/core/src/extension/host.ts` 通过其 state port 管理 deployment 记录并启停本机模块。
  对当前 packages/apps 源码检索未发现 `/extension-management` 或 `patch_config` Peer command 的消费者。
  不能把这个预留 capability 写成当前 Web UI 已实际使用的协议，也不能据此断言仓库外不存在消费者。

后续 preflight 核对路由 query 参数、Host errors 到 HTTP errors 的转换，以及有/无运行 Extension 的写入路径；
验收使用实际已发布 Extension 的安装、配置、启停和卸载，不为本批增加 helper/schema 自动化测试。
