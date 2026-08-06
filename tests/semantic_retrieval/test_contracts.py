"""Semantic retrieval input, configuration and exact Resolver contracts."""

import inspect

import pydantic
import pytest

from app.business.info_base.resolver import Resolver
from app.schemas.semantic_retrieval import (
  SemanticRetrievalRequest,
  VectorRetrievalOptions,
)
from extensions.github.resolver import GithubRepoResolver, GithubUserResolver
from extensions.learn_english.resolver import LexicalResolver
from extensions.mail.resolver import (
  EmailAddressResolver,
  EmailResolver,
  NewsletterResolver,
)
from extensions.memos.family.attachment_resolver import AttachmentResolver
from extensions.memos.family.resolver import MemoResolver
from extensions.rss.resolver import EnclosureResolver, FeedItemResolver, FeedResolver
from extensions.telegram.resolver import TelegramMessageResolver
from extensions.twitter.resolver import TweetResolver


EXTENSION_RESOLVERS = (
  (MemoResolver, "extensions.memos.memo.v1"),
  (AttachmentResolver, "extensions.memos.attachment.v2"),
  (FeedResolver, "extensions.rss.feed.v1"),
  (FeedItemResolver, "extensions.rss.feed_item.v1"),
  (EnclosureResolver, "extensions.rss.enclosure.v1"),
  (EmailResolver, "extensions.mail.email.v1"),
  (NewsletterResolver, "extensions.mail.newsletter.v1"),
  (EmailAddressResolver, "extensions.mail.email_address.v1"),
  (GithubRepoResolver, "extensions.github.repo.v1"),
  (GithubUserResolver, "extensions.github.user.v1"),
  (TelegramMessageResolver, "extensions.telegram.message.v1"),
  (TweetResolver, "extensions.twitter.tweet.v1"),
  (LexicalResolver, "extensions.learn_english.lexical.v1"),
)


def test_retrieval_options_are_bounded_and_non_empty():
  assert VectorRetrievalOptions().entity_types == {"block", "relation"}
  assert VectorRetrievalOptions(entity_types={"block"}).entity_types == {"block"}

  with pytest.raises(pydantic.ValidationError):
    VectorRetrievalOptions.model_validate({"limit": 101})
  with pytest.raises(pydantic.ValidationError):
    VectorRetrievalOptions(entity_types=set())
  with pytest.raises(pydantic.ValidationError):
    SemanticRetrievalRequest(query="   ")


@pytest.mark.parametrize(("resolver", "exact_id"), EXTENSION_RESOLVERS)
def test_extension_resolvers_use_exact_ids_and_own_explicit_labels(
  resolver,
  exact_id,
):
  assert resolver.__rsotype__ == exact_id
  assert "get_label" in resolver.__dict__
  assert not inspect.isabstract(resolver)


def test_resolver_label_is_an_abstract_capability():
  assert getattr(Resolver.get_label, "__isabstractmethod__", False) is True
