import typing
from app.business.info_base.root import RootManager
from app.business.info_base.resolver import Resolver
from app.business.info_base.resolver.text import TextResolver
from app.engine import SessionLocal
from libs.ai import one_chat_with_vlm
from app.schemas.info_base.main import StarGraphForm
from app.schemas.info_base.block import BlockID
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.main import ArcForm


class TweetResolver(Resolver, rso_type="tweet"):
    async def transcribe_to_text(self):
        # TODO move to ImageResolver
        res = one_chat_with_vlm(
            image_url=self._block.content,
            prompt="用Markdown列表的格式告诉我图片类型、图片主题、图片关键内容，只返回列表。",
        )
        if not res:
            # log error
            return
        with SessionLocal() as db:
            graph = StarGraphForm(
                block=TextResolver.create_graph(text=res).block,
                in_relations=(
                    ArcForm(
                        relation=RelationModel(
                            content="alt:text",
                            from_=typing.cast(BlockID, self._block.id),
                        )
                    ),
                ),
            )
            RootManager.add_star_graph_to_session(graph, db)
            db.commit()
