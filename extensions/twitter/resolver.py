import typing
from app.business.info_base.main import InfoBaseManager
from app.business.info_base.resolver import Resolver
from app.business.info_base.resolver.text import TextResolver
from app.engine import SessionLocal
from libs.ai import one_chat_with_vlm
from app.schemas.info_base.main import SubGraphForm
from app.schemas.info_base.block import BlockID
from app.schemas.info_base.relation import RelationModel
from app.schemas.info_base.main import InArcForm


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
      graph = SubGraphForm(
        block=TextResolver.create_graph(text=res).block,
        in_arcs=(
          InArcForm(
            relation=RelationModel(
              content="alt:text",
              from_=typing.cast(BlockID, self._block.id),
            )
          ),
        ),
      )
      InfoBaseManager.add_subgraph_to_session(graph, db)
      db.commit()
