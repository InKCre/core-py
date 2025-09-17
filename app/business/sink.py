import asyncio
import typing
from typing import Annotated as Anno, Literal as Lit, Optional as Opt

import fastapi
import sqlmodel

from app.business.block import BlockManager
from app.libs.ai import Chat, Message, MessageContent, Prompt
from app.schemas.block import BlockID


class SinkV1RAGResBody(sqlmodel.SQLModel):
    message: str


class SinkManager:
    type RetrieveMode = Lit["feature", "embedding", "reasoning"]

    @classmethod
    async def rag(
        cls,
        query: str,
        context: Opt[str] = None,
        context_blocks: list[BlockID] = fastapi.Query([]),
        retrieve_mode: RetrieveMode = "feature",
    ) -> SinkV1RAGResBody:
        # retrieve from base
        if retrieve_mode == "reasoning":
            related_blocks = await BlockManager.query_by_reasoning(query=query)
            tmp = []
            for block in related_blocks:
                tmp.append(await block.get_context_as_text())
            retrieve_result_prompt = MessageContent(content="\n".join(tmp))
        else:
            raise NotImplementedError

        # context + context_blocks -> context_text
        context_text = context or ""
        if context_blocks:
            resolvers = [BlockManager.get_resolver(bid) for bid in context_blocks]
            block_content_texts = await asyncio.gather(
                *tuple(i.get_text() for i in resolvers if i)
            )
            context_text += "\n".join(block_content_texts)

        prompt = Prompt("sink_rag")
        prompt.format(
            query=query,
            context=context_text,
        )
        chat = Chat("", "qwen-plus")
        chat.add_messages(
            Message(role="system", content=prompt),
            Message(role="system", content=retrieve_result_prompt),
        )

        res = chat.complete()
        return SinkV1RAGResBody(message=res.content)
