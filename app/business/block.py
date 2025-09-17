__all__ = ["BlockManager"]

import json
import typing
import sqlmodel
from typing import Optional as Opt
from app.business.relation import RelationManager
from utils.types_ import Undefined, _undefined
from ..engine import SessionLocal
from ..libs.ai import (
    CSVMessageContent,
    Chat,
    Embedding,
    Message,
    MessageContent,
    Prompt,
    one_chat,
)
from ..schemas.block import BlockEmbeddingModel, BlockID, BlockModel, ResolverType
from ..schemas.relation import RelationID, RelationModel

if typing.TYPE_CHECKING:
    from app.business.resolver import Resolver


class BlockManager:
    @classmethod
    def get_recent(
        cls, num: int = 10, resolver: Opt[ResolverType] = None
    ) -> tuple[BlockModel, ...]:
        """获取最新的块

        按创建时间倒序排序。

        :param num: 获取的块数量
        :param resolver: 限定解析器类型, None则不限定
        """
        with SessionLocal() as db_session:
            blocks = db_session.exec(
                sqlmodel.select(BlockModel)
                .order_by(sqlmodel.desc(BlockModel.created_at))
                .where(BlockModel.resolver == resolver if resolver else True)
                .limit(num)
            ).all()

        return tuple(blocks)

    @classmethod
    def get(cls, block_id: BlockID) -> Opt[BlockModel]:
        with SessionLocal() as db_session:
            block = db_session.exec(
                sqlmodel.select(BlockModel).where(BlockModel.id == block_id)
            ).one_or_none()
        return block

    @classmethod
    def get_resolver(cls, block_id: BlockID) -> Opt["Resolver"]:
        """Get resolver instance of the block"""
        from .resolver import ResolverManager

        block = cls.get(block_id)
        if block is None:
            return None
        return ResolverManager.new_resolver(block)

    @classmethod
    def create(cls, block: BlockModel) -> BlockModel:
        with SessionLocal() as db_session:
            db_session.add(block)
            db_session.commit()
            db_session.refresh(block)

        return block

    @classmethod
    def fetchsert(cls, block: BlockModel, db_session: sqlmodel.Session) -> BlockModel:
        """Create if not exists, else return the existing one.

        Will not commit the session.
        """
        existing = db_session.exec(
            sqlmodel.select(BlockModel).where(
                BlockModel.resolver == block.resolver,
                BlockModel.storage == block.storage,
                BlockModel.content == block.content,
            )
        ).one_or_none()
        if existing is not None:
            return existing
        db_session.add(block)
        db_session.flush()
        db_session.refresh(block)
        return block

    @classmethod
    async def organize(cls, block: BlockModel):
        """整理块

        FIXME
        """
        with SessionLocal() as db_session:
            resolver = ResolverManager.new_resolver(block)
            generator = (await resolver.breakdown())()
            try:
                i = generator.send(None)
                while True:
                    db_session.add(i)
                    db_session.flush()
                    db_session.refresh(i)
                    i = generator.send(i)
            except StopIteration:
                pass

            db_session.commit()

    @classmethod
    def query_by_embedding(
        cls,
        block_id: Opt[int] = None,
        embedding: Opt[list[float]] = None,
        num: int = 10,
    ) -> tuple[BlockModel, ...]:
        """根据余弦相似度查询块

        :param block_id: 用已有块的embedding查询
        :param embedding: 用给定的embedding查询
        """
        with SessionLocal() as db_session:
            if block_id is not None:
                base_embedding = db_session.exec(
                    sqlmodel.select(BlockEmbeddingModel.embedding).where(
                        BlockEmbeddingModel.id == block_id
                    )
                )
            else:
                if embedding is not None:
                    base_embedding = embedding
                else:
                    raise ValueError("one of block_id or embedding must be provided")

            similar_blocks = db_session.exec(
                sqlmodel.select(BlockModel, BlockEmbeddingModel)
                .select_from(BlockModel)
                .join(BlockEmbeddingModel, BlockEmbeddingModel.id == BlockModel.id)  # type: ignore
                .where(BlockEmbeddingModel.embedding is not None)
                .where(BlockEmbeddingModel.id != block_id)
                .order_by(BlockEmbeddingModel.embedding.cosine_distance(base_embedding))  # type: ignore
                .limit(num)
            ).all()

        return tuple(similar_blocks)

    @classmethod
    async def iterate_from_block(
        cls,
        block_id: int,
        max_depth: int = 2,
        exclude_start_block: bool = True,
    ):
        db_session = SessionLocal()
        depth = 0
        r_blocks: set[int] = set()
        r_relations: set[int] = set()

        if not exclude_start_block:
            r_blocks.add(block_id)

        def iterate_one(inner_block_id: int):
            nonlocal depth

            relations = db_session.exec(
                sqlmodel.select(RelationModel).where(
                    RelationModel.from_ == inner_block_id
                )
            ).all()

            r_relations.update(relation.id for relation in relations)

            for relation in relations:
                block = db_session.exec(
                    sqlmodel.select(BlockModel).where(BlockModel.id == relation.to_)
                ).one()
                r_blocks.add(block.id)

                if depth <= max_depth:
                    iterate_one(block.id)

            depth += 1

        iterate_one(block_id)

        db_session.close()

        return {"relations": r_relations, "blocks": r_blocks}

    class PickBaRBody(sqlmodel.SQLModel):
        blocks: set[int]
        relations: set[int]
        requirements: list[str] | None = None

    @classmethod
    def pick_blocks(
        cls,
        body: PickBaRBody,
        method: typing.Literal["llm"] = "llm",
    ):
        if method == "llm":
            with SessionLocal() as db_session:
                blocks = db_session.exec(
                    sqlmodel.select(BlockModel).where(BlockModel.id in body.blocks)
                ).all()

                relations = db_session.exec(
                    sqlmodel.select(RelationModel).where(
                        RelationModel.id in body.relations
                    )
                ).all()

            prompt = (
                "下面有一组块和一组关系，根据关系对块的注释，选出最满足要求的几个块。"
            )
            prompt += "块的内容即信息。关系描述块和块之间的联系，是块的动态属性。"
            prompt += (
                "关系可以解读为：<to.content>是<from.content>的<relation.content>。"
            )
            prompt += "务必只返回JSON，格式为整数数组。"

            prompt += "## 块\n```csv\n"
            prompt += "id,content\n"
            for block in blocks:
                prompt += f"{block.id},{block.content}\n"

            prompt += "```\n## 关系\n```csv\n"
            prompt += "id,from,to,content\n"
            for relation in relations:
                prompt += f"{relation.id},{relation.from_},{relation.to_},{relation.content}\n"

            prompt += "```\n## 要求"
            if body.requirements:
                prompt += "\n- ".join(body.requirements)
            else:
                raise ValueError

            llm_res = one_chat(prompt)

            return json.loads(llm_res.strip("```")[4:])
        else:
            raise NotImplementedError

    @classmethod
    async def query_by_reasoning(
        cls,
        query: str = "",
        scope: int = 1,  # 视野范围
    ) -> tuple[BlockModel, ...]:
        """推理检索

        :param query: 在找什么
        """
        query_embedding = Embedding("", "text-embedding-v3").embed(query)
        start_blocks = cls.query_by_embedding(embedding=query_embedding, num=3)
        prompt = Prompt("block_reasoning_query")
        prompt.format(query=query)
        chat = Chat("", "qwen-plus")
        chat.add_messages(prompt.to_message("system"))
        res = []

        async def iterate_chat(*block_ids: Opt[BlockID]) -> None:
            blocks = tuple(
                cls.get(block_id) for block_id in block_ids if block_id is not None
            )
            relation2block: dict[RelationID, BlockID] = {}

            graph_tool_res = MessageContent("")
            for block in blocks:
                if block is None:
                    continue  # TODO warning log
                relations = RelationManager.get(
                    typing.cast(BlockID, block.id),
                )
                outgoing_relations = []
                incoming_relations = []
                for relation in relations:
                    if relation.from_ == block.id:
                        outgoing_relations.append(relation)
                        relation2block[typing.cast(RelationID, relation.id)] = (
                            relation.to_
                        )
                    elif relation.to_ == block.id:
                        incoming_relations.append(relation)
                        relation2block[typing.cast(RelationID, relation.id)] = (
                            relation.from_
                        )

                graph_tool_res_i = MessageContent(
                    "## 节点{block_id} \n节点内容: {block_content}\n### 出边\n{outgoing_relations}\n### 入边\n{incoming_relations}\n"
                )
                outgoing_relations_csv = CSVMessageContent(
                    header=("ID", "标签"),
                    rows=[(str(r.id), r.content) for r in outgoing_relations],
                )
                incoming_relations_csv = CSVMessageContent(
                    header=("ID", "标签"),
                    rows=[(str(r.id), r.content) for r in incoming_relations],
                )
                graph_tool_res_i.format(
                    block_id=block.id,
                    block_content=await block.get_context_as_text(),
                    outgoing_relations=str(outgoing_relations_csv),
                    incoming_relations=str(incoming_relations_csv),
                )
                graph_tool_res.contact(graph_tool_res_i)

            chat_res = chat.complete(
                Message(role="user", content=graph_tool_res),
                add_to_history=False,
            )
            command, params = chat_res.content.split(":", 1)

            params = params.split(" ", 1)[0]
            if command == "FOUND":
                found_blocks = json.loads(params)
                res.extend(
                    filter(
                        lambda x: x.id in found_blocks if x is not None else False,
                        blocks,
                    )
                )
            elif command == "CONTINUE":
                # 没有保留历史
                follow_relations = json.loads(params)
                follow_blocks = tuple(
                    relation2block.get(relation_id) for relation_id in follow_relations
                )
                await iterate_chat(*follow_blocks)
            else:
                raise ValueError(f"unknown command from LLM, {command}")

        for start_block in start_blocks:
            await iterate_chat(start_block.id)
        return tuple(res)

    @classmethod
    def edit_block(
        cls,
        block_id: BlockID,
        content: Opt[str] = None,
        resolver: Opt[ResolverType] = None,
        storage: Opt[str] | Undefined = _undefined,
    ) -> BlockModel:
        """编辑块"""
        with SessionLocal() as db_session:
            block = db_session.exec(
                sqlmodel.select(BlockModel).where(BlockModel.id == block_id)
            ).one_or_none()
            if block is None:
                raise ValueError("Block not found")

            if content is not None:
                block.content = content
            if resolver is not None:
                block.resolver = resolver
            if storage is not _undefined:
                block.storage = storage

            db_session.add(block)
            db_session.commit()
            db_session.refresh(block)

        return block
