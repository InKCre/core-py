# Collection Track

## Objective

增加和完善 sources，使 source-specific 信息能够被可靠地收集为 InKCre 的 blocks / relations，
并在需要时推动 extension、resolver、storage 与 registry 能力演进。

## Slices

| Slice | Role | Status |
|---|---|---|
| Existing sources | 兼容性与回归基线：Twitter、GitHub、RSS、Mail、Telegram | Evidence collected |
| Memos extension | memo-like 的首个可实现单元；当前 scope 是 backend MVP | Active — Technical review + implementation-plan probe |
| CalDAV | 日历协议与结构化同步压力 | Queued |
| Nextcloud Files | 文件层级、binary、pointer/storage 压力 | Queued |
| Apple Notes | macOS local runtime 与受限访问压力 | Queued |

## Per-Source Design Card

每个 source 依次填写：

1. **Product**: 用户为什么收集它；纳入和排除什么；用户可观察结果与失败。
2. **Access**: 外部系统、认证、主动 collect / 被动 record、平台限制。
3. **Native shape**: source-specific objects 与保留的信息。
4. **Info-base expression**: 根 block、相关 blocks、relations、inline / pointer。
5. **Resolver / storage**: raw、solved、text/use 表示与外部内容访问。
6. **Change behavior**: identity、新增、更新、删除、移动、重复执行与冲突。
7. **Extension pressure**: artifact、registration、installation、runtime、client-web。
8. **Acceptance**: fixtures、错误、兼容性、重复执行与端到端证明。
9. **Iteration**: 最小 thin slice 与后续增量。
10. **Hub projection**: PRD、Product TDD 与 claim realization 影响。

## Abstraction Rule

不先设计通用 collected object 或万能 source framework。通常只有两个真实 source units 重复
出现同一压力，且统一不会抹去 source-specific 语义时，才进入公共合同；若单个 unit 已证明
现有机制无法正确交付，则只允许解决该 blocker 的最小横切改造。

## Active Slice

See [Memos extension](../units/memos-extension/packet.md)。当前 phase 只属于 backend MVP；future
collectors/products 仍需各自过 gate，不能继承当前 approval。
