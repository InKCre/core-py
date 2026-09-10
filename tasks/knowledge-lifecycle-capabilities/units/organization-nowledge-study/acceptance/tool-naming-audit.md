# 本轮 Agent Tool 命名检查

2026-09-10 已实际检查 13 个注册工具的绑定输入模型、六个通用 Resolver 方法、Graph Navigation 方法及返回模型，并核对计划新增入口。检查完成，源码改名尚未执行。

| 入口 | 输入处理 |
| --- | --- |
| record_supersession | successor_id/predecessor_id → successor_block_id/predecessor_block_id |
| record_refinement | refinement_id/predecessor_id → refinement_block_id/predecessor_block_id |
| record_evidence_stance | evidence_id/assertion_id → evidence_block_id/assertion_block_id；stance 保留 |
| create_synthesis | source_ids/previous_synthesis_id → source_block_ids/previous_synthesis_block_id；text 保留 |
| anchor_existing_referent | source_id/referent_id → source_block_id/referent_block_id；selected_text 保留 |
| record_duplicate_assertion | left_id/right_id → left_block_id/right_block_id |
| record_organization_candidate | information_id → block_id；behavior 保留 |
| resolver | calls[].block → block_id；blocks/resolvers → block_ids/resolver_types；action/method/arguments/calls 保留 |
| retrieve | query/mode/limit 保留；实体引用与 get_entity 对接 |
| graph_retrieval | 按 D-532 删除元工具，不孤立改名其旧字段 |
| get_draft_graph_schema | resolvers → resolver_types |
| draft_graph | resolver → resolver_type；id_start → local_block_id_start；input 保留 |
| submit_graph | graph 保留；内部普通实体字段不改 |
| find_path | from_block/to_block → from_block_id/to_block_id；其余参数保留 |
| get_connected_components | seed_block_ids 已明确；计数参数不加 id 后缀 |
| get_entity / get_entity_neighborhood | 共享明确类型和 ID 的实体引用，具体形状按该接口评审收敛 |

通用 Resolver 的 refresh/context/materialize_missing/include_in/include_out 保留，必要含义用简短字段说明；read_lineage 的 focal_block_id 已明确。get_existing 的 db_session 是内部参数，不进入 Agent 工具。

## 返回字段

标量身份 relation/descriptor/synthesis/fragment 对应 relation_id/descriptor_block_id/synthesis_block_id/fragment_block_id；保留既已接受的返回信息，仅澄清名字。basis/edited/has_mention/refers_to 是嵌套结果对象，不能把整个对象误命名为 *_id。

Resolver 响应关联 block 与输入同步为 block_id，保留 index/method。seed_blocks/member_blocks/current_frontier 是 ID 列表，对应 seed_block_ids/member_block_ids/current_block_ids。graph.blocks/relations 是完整对象集合，不改成 *_ids；block_path/relation_path 已表明实体类型及路径语义，不机械改名。created 等创建事实保留，具体多对象响应需确保能辨认它描述哪个对象。

## 边界

实施时同步 schema、adapter、操作参数及本 unit 调用者，不用 description 重复“这是 Block ID”。不改数据库列、普通实体自身 id、Peer 或 MCP wire 合同；共享 owner 若影响 MCP 内部调用，只作适配。未评审工具的其它语义不因命名检查完成而视为已批准，不建设通用兼容别名机制。

