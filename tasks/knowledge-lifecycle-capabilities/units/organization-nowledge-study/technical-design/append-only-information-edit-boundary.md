# Append-only Information Edit Boundary

- **状态**：档位 1 已由 D-513 接受；具体 Organization caller/factoring 继续 Technical review。
- **问题**：D-502 已接受普通信息编辑保留旧 Block、追加新 Block 并写 `old --edited--> new`。现有代码仍有多条
  原地修改 `content/resolver/storage` 的路径。哪些在语义上属于信息版本编辑，哪些确实只是另一 authority 的可重建
  投影同步，以及当前值得采用哪一档实现？
- **范围**：确定 Block 含义与版本连续性的指导原则，并比较从局部遵守到全局 enforcement 的不同档位。不在这里
  发明通用对象版本框架，也不因为原则成立就自动授权跨 Extension 迁移。

## 第一性原理

一条已持久 Relation 的判断对象是两个 Block 当时可寻址的完整含义：

```text
A --supports--> X
A --synthesis--> S
N --supersedes--> P
```

如果 `A.content`、`X.content` 或 `P.content` 原地改变，Relation 的图形没有变化，但它声称的事实被追溯性换成了另一
个事实。`updated_at` 能提示“发生过更新”，却不能恢复旧含义，所以它不能修复历史依据、旧证据或旧演进判断。

由此不能按“谁写的”分类，而要按 **Block 是否就是信息 authority** 分类：

```text
Block 自己拥有这项已留存信息
  + Resolver-visible meaning 发生变化
    -> information revision
    -> append new Block + old --edited--> new

Block 只是另一份本地持久 authority 的可重建投影
  + stable referent 不变
  + 更新没有新增/替换 Block 自己拥有的信息
    -> projection reconciliation
    -> exact owner may update in place
```

“来自 Source/Extension”、“具有 external ID”或“调用方希望 URL 不变”都不能单独证明第二类。否则任何采集器都可以
把自己唯一保存的信息称为 projection，从而使 append-only 规律失效。

## 判断原地投影更新是否合理的指导条件

当具体 owner 决定是否采用 append-only 时，以下条件可帮助判断原地更新是否只是 projection reconciliation：

1. 另一个本地持久对象是这份状态的 authority；
2. Block 与该对象之间有可恢复的一对一持久 binding，而不是运行时猜测；
3. 删除并从 authority 重建 Block 不会丢失独立采集、作者表达、证据或历史信息；
4. 更新前后 Block 指向同一 referent，且没有把一个可判断的命题替换成另一个；
5. exact owner 在自己的事务中同步投影；generic Block API 不能代表它执行。

当前已核实清楚满足这组条件的运行时路径只有 `SourceManager.ensure_block()`：`SourceModel.block` 持久绑定 Source row，
Block 只投影该 row 的 `id/type/nickname`，Source row 才是 authority。

数据库 migration 对历史表示作一次性转换，不是 runtime information edit，也不需要伪装成 `edited` history。未被调用的
`WritableStorage.update_raw_content()` 仍保留为 Storage capability，但未来若它被用于替换一项已留存信息，应创建新
blob、新 Block 和 `edited`；外部 bytes 在同一 pointer 后静默改变继续是 D-502 已接受的 best-effort 缺陷。

## ROI 档位

| 档位 | 实施内容 | 收益 | 成本/风险 | 当前判断 |
| --- | --- | --- | --- | --- |
| 0. 放弃 append-only 语义 | Organization 自己的 changed synthesis 也可原地覆盖 | 最少代码 | 直接违反 D-502/D-503；旧 basis 与旧综合不可恢复 | reject |
| 1. 局部语义合同 + 全局指导 | Organization exact commands 对自己的 derived revisions 必须追加；其它 producer 可选择用 `edited` 暴露变化；本 unit 不改通用写 API | 保住本 unit 承诺的来源依据、重应用和历史结果；零跨 unit compatibility 成本 | mutable upstream 仍可能让旧 Relation 追溯性改义；明确作为 best-effort residual | **recommended** |
| 2. 提供 opt-in convenience seam | 在档位 1 上增加共享 `append_block_edit()` 或明确 append-edit API，但不禁用原地编辑 | 降低 producer 正确表达版本的事务成本 | 当前没有两个以上获批调用者；会提前拥有 API、error/replay contract | defer until concrete callers |
| 3. 定向迁移 producer | 由某个已观察 use failure 推动 Memos、RSS、Mail 或 GitHub 的 exact graph/version 迁移 | 修复该 producer 的真实历史错义和重新考虑缺口 | 每个协议都有不同 stable identity/current-edge compatibility；不能批量机械改写 | adopt per demonstrated failure |
| 4. 全局 enforcement | 让 Block schema/manager/database 普遍拒绝 UPDATE，迁移全部 callers | 最强历史不变量 | 破坏现有 API/协议、migration/projection 路径；需要全局 identity/version 模型 | reject without new Product mandate |

档位 1 不是“部分实现档位 4”。它承认两种不同责任：一个 exact Organization operation 必须正确实现自己承诺的
append-only result；它无权替所有 producer 规定持久化模型。指导原则提供未来诊断语言，而不是数据库约束、lint、
Block flag 或全局 manager policy。

## 真实写路径风险分类

| 当前写路径 | 当前 Block 的 authority/meaning | 按原则观察到的风险 | 当前档位 1 的处理 |
| --- | --- | --- | --- |
| `PATCH /blocks/{id}` → `BlockManager.edit_block()` | Block 本身就是调用者选择修改的信息；没有另一个 authority 或 exact reconciliation contract | 最像普通 information revision；旧 incident Relations 可能改义 | 保持现状并记录风险；不由本 unit 改 API |
| Memos `MemoApplicationService.update()` | memo 正文、状态和时间只持久在 memo Block；Memos resource name 又直接使用 Block ID | 历史含义与 stable protocol identity 冲突最明显 | 不迁移；出现具体 use failure 时由 Memos owner 设计 exact identity/version contract |
| GitHub account/repository/list `_upsert_many()` | external node ID 证明 referent continuity，但描述、topic、语言、可见性等采集信息只存在于 Block | 新观察覆盖旧 metadata，可能改变旧 Organization 判断依据 | 不迁移；等待 GitHub-specific failure |
| RSS feed/item/enclosure reconciliation | identity ladder 找到同一 source object，但 feed/item/enclosure 的作者信息只存在于 Block | 新观察覆盖旧 authored information | 不迁移；等待 RSS-specific failure |
| RSS full-text refresh | text Block 是 materialized derived information | 最接近 derived information revision，旧综合可能失去文本依据 | 不迁移；可作为未来档位 2/3 的优先候选，但当前没有已证明失败 |
| Mail mailbox/email completion/body/MIME-part reconciliation | external identifiers 帮助找同一对象；采集到的信息仍只存在于 Blocks | completion/correction 可能追溯性改变旧判断 | 不迁移；等待 Mail-specific failure |
| `SourceManager.ensure_block()` | Source row 是 authority；`SourceModel.block` 是一对一持久 binding；Block 是可重建 anchor projection | 已证明是 projection reconciliation | 继续保留原地同步 |
| Alembic representation/data migrations | migration owns one-time representation transition | 非 runtime edit | 保持 migration-local |

这个表刻意不把 GitHub/RSS/Mail Blocks 仅因具有 external identity 就当作 mutable entity。Continuity 说明“新旧信息谈的是
同一对象”，正是 `edited` 能表达的条件；它不说明旧信息可以消失。

## 可选的共享写操作——当前不增加

如果档位 2 将来出现真实调用者，最小形状可以是一个 Agent-neutral、caller-transaction-friendly operation：

```text
append_block_edit(previous_id, next_form, db_session)
  -> lock/read previous
  -> if resolver/storage/content exactly unchanged: return no-op(previous)
  -> create a fresh Block from next_form       # 不使用 fetchsert
  -> fetchsert previous --edited--> new
  -> return previous_id, new_id, relation_id, effects
```

它不做以下事情：

- 不复制、删除或重定向 previous 的其它 incident Relations；
- 不判断 supersession、refinement、currentness 或 producer identity；
- 不沿 `edited` 自动寻找“最新版本”；
- 不更新外部 protocol resource name；
- 不创建 version table、logical-object ID、cursor 或全局 immutable 标记。

这些都取决于 exact producer graph。Memos、RSS、Mail 和 GitHub 必须分别决定哪些关系表示当前 composition/membership，
以及调用者如何继续寻址当前版本；generic InfoBase manager 无法从任意 Relation content 安全猜测。

### 当前 Organization caller audit

| exact operation / path | 是否产生 information revision | 当前是否需要独立 helper |
| --- | --- | --- |
| synthesis reapplication | yes；new synthesis + previous `edited` + new exact basis 必须在同一事务 | 唯一确定的 direct caller；可先留在 `create_synthesis()` 的完整 command 内 |
| rumination | only when its proposal explicitly revises an existing Block | existing `submit_graph` 已能原子表达 new Block + `edited`；当前没有第二个 exact revision method |
| supersession / refinement / evidence stance | no；只在既有 Blocks 间写 exact semantic Relation | no |
| existing-referent anchoring | no；创建新的指称片段并写 `has mention` / `refers to` | no |
| duplicate assertion | no；只写 canonical `duplicates assertion` | no |
| `candidate for` | no；只写 attention Relation | no |

因此这些 methods 共享的是 **append-only semantic law**，不是已经重复出现的 helper call。首个 synthesis command 直接
拥有完整 atomic mutation 更清楚；当第二个 exact direct caller 不能由现有 `submit_graph` 合理表达时，再提取
`append_block_edit()`。这不改变 D-513 的指导原则，也不提升为 cross-owner enforcement。

## API 边界

当前 `PATCH /blocks/{id}` 声称 partial update，实际请求却是完整 `BlockModel`，并把 `content/resolver/storage` 原地写回。
直接让同一路径悄悄返回不同 ID 会改变 PATCH 的资源语义和客户端预期。当前 repository search 没有发现该 PATCH 的
真实客户端调用，但 OpenAPI 已公开它，所以“没有已知 caller”不等于可以静默破坏。

档位 1 保持 `PATCH /blocks/{id}` 及现有 producer APIs 不变，不增加 `POST /blocks/{id}/edits`。未来进入档位 2 时，优先
增加语义明确的 append-edit transport，而不是让既有 PATCH 悄悄返回另一个资源 ID；是否弃用 PATCH 必须由真实 caller
与 compatibility evidence 单独决定。

本 unit 的 Organization exact commands 仍只创建新 Blocks/Relations，从不调用 legacy in-place edit。这是各 operation
自己的正确性，不是对整个 info-base 的 enforcement。

## Acceptance implications

这一边界至少需要证明：

1. changed synthesis 等本 unit 自有 derived revision 后，旧 Block 的 resolver-visible meaning 保持不变，新 Block 可独立读取；
2. exactly unchanged replay 不新增 Block/Relation；
3. `edited` 方向固定为 old -> new，且 Block 与 Relation 在一个事务中完成；
4. 旧 Organization Relations 仍连接旧版本，不被复制成对新版本仍然成立；
5. 新版本会进入 evolution/synthesis 等 behavior 的候选，但 `edited` 本身不授权其它关系；
6. representative upstream `edited` graph 可触发 best-effort reconsideration，不要求现有 producer 全部改造；
7. mutable upstream 的残余风险被明确报告，不虚假声称历史 basis 在所有 producer 上都完整。

## 当前决策点

D-513 确认两个层次：

1. **指导原则**：除可证明由另一份本地持久 authority 支撑的可重建 projection 外，Resolver-visible information change
   最好以新 Block + `edited` 表达；external identity 和 Extension ownership 本身不是语义豁免。
2. **当前实施档位**：只要求本 unit 自己的 Organization operations 遵守 append-only output contract；不 enforce 通用
   Block immutability、不改 PATCH、不迁移现有 producers、不新增共享 helper。以后只由具体 use failure 提升对应 owner。
