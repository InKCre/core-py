"""Memo-family extension with a Memos-compatible backend MVP."""

import fastapi

from app.business.extension import ExtensionBase
from .config import MemosConfig


class Extension(
  ExtensionBase[MemosConfig],
  ext_id="memos",
  config_cls=MemosConfig,
):
  """Own memo-family semantics and expose selected product access modes."""

  @classmethod
  def api_dependencies(cls):
    """Use an auth-neutral root so product routes can compose public and PAT auth."""
    return []

  @classmethod
  def _register_apis(cls, router: fastapi.APIRouter):
    from .products.memos.v0_29_1 import register_backend

    register_backend(router)

  @classmethod
  def _init_resolvers(cls):
    from .family.attachment_resolver import AttachmentResolver  # noqa: F401
    from .family.resolver import MemoResolver  # noqa: F401
