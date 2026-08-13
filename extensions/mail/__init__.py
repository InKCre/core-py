"""Mail extension lifecycle and exact remote MIME materialization command."""

import fastapi
import pydantic

from app.business.extension.main import ExtensionBase
from app.business.info_base.block import BlockManager
from app.business.info_base.resolver import ResolverManager
from app.business.peer import PeerHTTPInbound
from app.schemas.info_base.block import BlockModel

from .schema import MailboxExclusionPolicy, MimePartMaterializeRequest


MAIL_MIME_PART_MATERIALIZE_CAPABILITY = "extensions.mail.mime_part.materialize.v1"
MAIL_MIME_PART_INBOUND = PeerHTTPInbound(
  capability=MAIL_MIME_PART_MATERIALIZE_CAPABILITY,
  method="POST",
  path="/mail/mime-parts/materialize",
)


class MailExtensionConfig(pydantic.BaseModel):
  """Deployment defaults inherited once by newly used Mail Sources."""

  model_config = pydantic.ConfigDict(extra="forbid")

  default_excluded_mailboxes: MailboxExclusionPolicy = pydantic.Field(
    default_factory=MailboxExclusionPolicy
  )


class Extension(
  ExtensionBase[MailExtensionConfig],
  ext_id="mail",
  config_cls=MailExtensionConfig,
):
  """Collect and solve Mail without introducing a Mail-specific browsing surface."""

  @classmethod
  def _init_resolvers(cls) -> None:
    from . import resolver as resolver_module  # noqa: F401

  @classmethod
  def _init_sources(cls) -> None:
    from .source import Source  # noqa: F401

  @classmethod
  def peer_inbounds(cls):
    return (MAIL_MIME_PART_INBOUND,)

  @classmethod
  def _register_apis(cls, router: fastapi.APIRouter) -> None:
    @router.post("/mime-parts/materialize")
    async def materialize_mime_part(
      body: MimePartMaterializeRequest,
    ) -> BlockModel:
      block = BlockManager.get(body.block)
      if block is None:
        raise fastapi.HTTPException(status_code=404, detail="MIME part Block not found")
      resolver = ResolverManager.get(block)
      if resolver.__rsotype__ != "extensions.mail.mime_part.v1":
        raise fastapi.HTTPException(status_code=422, detail="Block is not a Mail MIME part")
      solved = await resolver.get_solved_content(materialize_missing=True)
      child = getattr(solved, "content", None)
      if child is None:
        raise fastapi.HTTPException(status_code=409, detail="MIME part is unavailable")
      return child.block
