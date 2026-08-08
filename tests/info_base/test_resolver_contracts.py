"""Exact resolver registry, projection controls, and capability outcomes."""

import asyncio

from app.business.info_base.resolver import (
  CORE_RESOLVER_IDS,
  DuplicateResolverRegistrationError,
  Resolver,
  ResolverManager,
  UnknownResolverError,
  UnsupportedResolverCapability,
  register_core_resolvers,
)
from app.business.info_base.resolver.video import VideoResolver
from app.schemas.info_base.block import BlockModel
import pytest


class _ProjectionResolver(
  Resolver[str, str],
  rso_type="tests.resolver.projection.v1",
):
  async def get_text(
    self,
    *,
    refresh: bool = False,
    materialize_missing: bool = True,
  ) -> str | None:
    content = await self.get_solved_content(
      refresh=refresh,
      materialize_missing=materialize_missing,
    )
    return None if content == "supported-null" else content

  async def get_label(self, *, refresh: bool = False) -> str:
    del refresh
    return "projection"


def _block(content: str, resolver: str = _ProjectionResolver.__rsotype__) -> BlockModel:
  return BlockModel(id=17, resolver=resolver, content=content)


def test_registry_is_exact_idempotent_and_rejects_collisions():
  ResolverManager.register_resolver(_ProjectionResolver)

  with pytest.raises(DuplicateResolverRegistrationError):

    class _CollisionResolver(
      Resolver[str, str],
      rso_type=_ProjectionResolver.__rsotype__,
    ):
      async def get_text(self, **_kwargs) -> str:
        return "collision"


def test_unknown_id_is_not_reinterpreted_by_a_default_resolver():
  with pytest.raises(UnknownResolverError, match="tests.resolver.unknown.v1"):
    ResolverManager.get(_block("content", "tests.resolver.unknown.v1"))


def test_refresh_replaces_only_the_resolver_instance_snapshot():
  block = _block("first")
  resolver = _ProjectionResolver(block)

  assert asyncio.run(resolver.get_solved_content()) == "first"
  block.content = "second"
  assert asyncio.run(resolver.get_solved_content()) == "first"
  assert asyncio.run(resolver.get_solved_content(refresh=True)) == "second"


def test_supported_null_authored_empty_and_unsupported_are_distinct():
  assert asyncio.run(_ProjectionResolver(_block("supported-null")).get_text()) is None
  assert asyncio.run(_ProjectionResolver(_block("")).get_text()) == ""

  video = VideoResolver(_block("pointer", VideoResolver.__rsotype__))
  with pytest.raises(UnsupportedResolverCapability):
    asyncio.run(video.get_text())


def test_explicit_core_bootstrap_does_not_require_extension_loading(monkeypatch):
  monkeypatch.setattr(ResolverManager, "RESOLVER_CLS", {})

  register_core_resolvers()

  assert set(ResolverManager.RESOLVER_CLS) == set(CORE_RESOLVER_IDS)


@pytest.mark.parametrize(
  ("media_type", "resolver_id"),
  (
    ("text/plain; charset=utf-8", "core.text.v1"),
    ("application/xhtml+xml", "core.html.v1"),
    ("image/avif", "core.image.v1"),
    ("audio/ogg", "core.audio.v1"),
    ("video/webm", "core.video.v1"),
    ("application/pdf", "core.pdf.v1"),
    ("application/epub+zip", "core.epub.v1"),
    ("application/x-zip-compressed", "core.zip.v1"),
  ),
)
def test_media_type_matching_is_normalized_and_exactly_registered(
  monkeypatch,
  media_type,
  resolver_id,
):
  monkeypatch.setattr(ResolverManager, "RESOLVER_CLS", {})
  register_core_resolvers()

  assert ResolverManager.match_media_type(media_type) == resolver_id


@pytest.mark.parametrize(
  "media_type",
  (None, "", "application/octet-stream", "application/vnd.example.unknown"),
)
def test_media_type_matching_does_not_choose_extension_fallback(media_type):
  assert ResolverManager.match_media_type(media_type) is None
