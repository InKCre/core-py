"""Telegram direct private delivery inbox Extension."""

import fastapi
import pydantic

from app.business.extension.main import ExtensionBase
from app.business.info_base.block import BlockManager
from app.business.info_base.resolver import ResolverManager
from app.business.peer import PeerHTTPInbound
from app.schemas.info_base.block import BlockModel

from .resolver import (
  ATTACHMENT_RESOLVER,
  TelegramAttachmentResolver,
  TelegramMaterializationUnavailable,
)
from .schema import TelegramAttachmentMaterializeRequest


TELEGRAM_ATTACHMENT_MATERIALIZE_CAPABILITY = "extensions.telegram.attachment.materialize.v1"
TELEGRAM_ATTACHMENT_MATERIALIZE_INBOUND = PeerHTTPInbound(
  capability=TELEGRAM_ATTACHMENT_MATERIALIZE_CAPABILITY,
  method="POST",
  path="/telegram/attachments/materialize",
)


class TelegramExtensionConfig(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid")


class Extension(
  ExtensionBase[TelegramExtensionConfig],
  ext_id="telegram",
  config_cls=TelegramExtensionConfig,
):
  """Collect useful content sent directly to one sender-bound Telegram bot."""

  @classmethod
  def _init_resolvers(cls) -> None:
    from . import resolver as resolver_module  # noqa: F401

  @classmethod
  def _init_sources(cls) -> None:
    from .source import Source  # noqa: F401

  @classmethod
  def peer_inbounds(cls):
    return (TELEGRAM_ATTACHMENT_MATERIALIZE_INBOUND,)

  @classmethod
  def _register_apis(cls, router: fastapi.APIRouter) -> None:
    @router.post("/attachments/materialize")
    async def materialize_attachment(
      body: TelegramAttachmentMaterializeRequest,
    ) -> BlockModel:
      block = BlockManager.get(body.block)
      if block is None:
        raise fastapi.HTTPException(status_code=404, detail="attachment Block not found")
      resolver = ResolverManager.get(block)
      if resolver.__rsotype__ != ATTACHMENT_RESOLVER:
        raise fastapi.HTTPException(
          status_code=422, detail="Block is not a Telegram attachment"
        )
      try:
        return await TelegramAttachmentResolver(block).materialize_content()
      except TelegramMaterializationUnavailable as error:
        raise fastapi.HTTPException(status_code=409, detail=str(error)) from error
