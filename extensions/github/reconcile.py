"""Transactional reconciliation of one complete GitHub snapshot."""

from __future__ import annotations

import typing

import pydantic

from app.business.source import SourceManager
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationCreateForm, RelationModel
from app.persistence.source.uow import SourceUnitOfWork

from .resolver import (
  ACCOUNT_RESOLVER_ID,
  LIST_RESOLVER_ID,
  REPOSITORY_RESOLVER_ID,
  GitHubAccountResolver,
  GitHubGraphIntegrityError,
  GitHubListResolver,
  GitHubRepositoryResolver,
)
from .schema import (
  GitHubAccount,
  GitHubList,
  GitHubRepository,
  GitHubSnapshot,
  GitHubSourceState,
)


class GitHubSourceBindingError(RuntimeError):
  """A Source token resolved to another GitHub Account."""


class GitHubReconcileReport(pydantic.BaseModel):
  """Bounded observable effect summary for one complete snapshot."""

  model_config = pydantic.ConfigDict(extra="forbid")
  account: str
  stars: int
  lists: int
  memberships: int
  blocks_created: int = 0
  blocks_updated: int = 0
  relations_created: int = 0
  relations_deleted: int = 0


def _id(block: BlockModel) -> int:
  if block.id is None:  # pragma: no cover - database persistence invariant
    raise RuntimeError("Persisted GitHub Block has no ID")
  return block.id


class GitHubGraphReconciler:
  """Own exact GitHub identity and current relation-set reconciliation."""

  _resolver_models: typing.ClassVar[dict[str, type[pydantic.BaseModel]]] = {
    ACCOUNT_RESOLVER_ID: GitHubAccount,
    REPOSITORY_RESOLVER_ID: GitHubRepository,
    LIST_RESOLVER_ID: GitHubList,
  }

  def __init__(self, uow: SourceUnitOfWork):
    self.uow = uow
    self.blocks_created = 0
    self.blocks_updated = 0
    self.relations_created = 0
    self.relations_deleted = 0

  async def reconcile(
    self, source_id: int, snapshot: GitHubSnapshot
  ) -> GitHubReconcileReport:
    source = await self.uow.sources.get(source_id, lock=True)
    if source is None:
      raise ValueError(f"Source {source_id} does not exist")
    state = GitHubSourceState.model_validate(source.state or {})
    if (
      state.account_node_id is not None
      and state.account_node_id != snapshot.account.node_id
    ):
      raise GitHubSourceBindingError(
        "GitHub Source token resolves to a different Account; create another Source"
      )

    source_anchor = await SourceManager.ensure_block_async(source, self.uow)
    existing = await self._load_github_blocks()
    repositories = {
      fact.repository.node_id: fact.repository for fact in snapshot.repositories
    }
    accounts = {fact.owner.node_id: fact.owner for fact in snapshot.repositories}
    accounts[snapshot.account.node_id] = snapshot.account
    lists = {fact.list.node_id: fact.list for fact in snapshot.lists}

    repository_blocks = await self._upsert_many(
      GitHubRepositoryResolver, repositories, existing
    )
    account_blocks = await self._upsert_many(GitHubAccountResolver, accounts, existing)
    list_blocks = await self._upsert_many(GitHubListResolver, lists, existing)

    source_block_id = _id(source_anchor)
    account_block_id = _id(account_blocks[snapshot.account.node_id])
    repository_ids = {node_id: _id(block) for node_id, block in repository_blocks.items()}
    current_list_ids = {node_id: _id(block) for node_id, block in list_blocks.items()}
    previous_list_ids = await self._previous_list_ids(account_block_id, existing)
    roots = {
      source_block_id,
      account_block_id,
      *previous_list_ids,
      *current_list_ids.values(),
    }
    candidates = await self._load_candidate_relations(roots, set(repository_ids.values()))

    blocks_by_id = {_id(block): block for block in existing.values()}
    for values in (
      repository_blocks.values(),
      account_blocks.values(),
      list_blocks.values(),
    ):
      blocks_by_id.update({_id(block): block for block in values})
    desired = self._desired_relations(
      source_block_id,
      account_block_id,
      repository_ids,
      account_blocks,
      current_list_ids,
      snapshot,
    )
    managed = self._managed_relations(
      candidates,
      blocks_by_id,
      source_block_id,
      account_block_id,
      previous_list_ids | set(current_list_ids.values()),
      set(repository_ids.values()),
    )
    await self._replace_relations(managed, desired)

    source.state = GitHubSourceState(account_node_id=snapshot.account.node_id).model_dump(
      mode="json"
    )
    await self.uow.sources.save(source)
    return GitHubReconcileReport(
      account=snapshot.account.login,
      stars=len(snapshot.starred_repository_node_ids),
      lists=len(snapshot.lists),
      memberships=sum(len(item.repository_node_ids) for item in snapshot.lists),
      blocks_created=self.blocks_created,
      blocks_updated=self.blocks_updated,
      relations_created=self.relations_created,
      relations_deleted=self.relations_deleted,
    )

  async def _load_github_blocks(self) -> dict[tuple[str, str], BlockModel]:
    blocks = await self.uow.graph.blocks.get_by_resolvers(tuple(self._resolver_models))
    indexed: dict[tuple[str, str], BlockModel] = {}
    for block in blocks:
      resolver_id = block.resolver
      try:
        content = self._resolver_models[resolver_id].model_validate_json(block.content)
        node_id = typing.cast(str, getattr(content, "node_id"))
      except (pydantic.ValidationError, TypeError, KeyError) as error:
        raise GitHubGraphIntegrityError(
          f"GitHub Block {_id(block)} has malformed canonical content"
        ) from error
      key = (resolver_id, node_id)
      if key in indexed:
        raise GitHubGraphIntegrityError(
          f"GitHub node {node_id!r} resolves to multiple Blocks"
        )
      indexed[key] = block
    return indexed

  async def _upsert_many(
    self,
    resolver_cls: typing.Any,
    contents: typing.Mapping[str, GitHubAccount | GitHubRepository | GitHubList],
    existing: dict[tuple[str, str], BlockModel],
  ) -> dict[str, BlockModel]:
    resolver_id = typing.cast(str, resolver_cls.__rsotype__)
    result: dict[str, BlockModel] = {}
    missing: list[tuple[str, typing.Any]] = []
    changed: list[BlockModel] = []
    for node_id, content in contents.items():
      form = resolver_cls.create_block(content)
      block = existing.get((resolver_id, node_id))
      if block is None:
        missing.append((node_id, form))
      else:
        if block.content != form.content or block.storage is not None:
          block.storage = None
          block.content = form.content
          changed.append(block)
          self.blocks_updated += 1
        result[node_id] = block
    await self.uow.graph.blocks.save_many(changed)
    created = await self.uow.graph.blocks.create_many(form for _, form in missing)
    self.blocks_created += len(created)
    for (node_id, _), block in zip(missing, created, strict=True):
      result[node_id] = block
      existing[(resolver_id, node_id)] = block
    return result

  async def _previous_list_ids(
    self, account_id: int, blocks: dict[tuple[str, str], BlockModel]
  ) -> set[int]:
    list_ids = {
      _id(block) for (resolver, _), block in blocks.items() if resolver == LIST_RESOLVER_ID
    }
    if not list_ids:
      return set()
    return {
      relation.to_
      for relation in await self.uow.graph.relations.get(
        account_id, include_in=False, content="owns"
      )
      if relation.to_ in list_ids
    }

  async def _load_candidate_relations(
    self, roots: set[int], repository_ids: set[int]
  ) -> tuple[RelationModel, ...]:
    return await self.uow.graph.relations.get_for_endpoints(
      roots | repository_ids, contents=("collects", "stars", "owns", "contains")
    )

  @staticmethod
  def _desired_relations(  # noqa: PLR0913
    source_block_id: int,
    account_block_id: int,
    repository_ids: dict[str, int],
    account_blocks: dict[str, BlockModel],
    list_ids: dict[str, int],
    snapshot: GitHubSnapshot,
  ) -> set[tuple[int, int, str]]:
    desired = {(source_block_id, account_block_id, "collects")}
    desired.update(
      (account_block_id, repository_ids[node_id], "stars")
      for node_id in snapshot.starred_repository_node_ids
    )
    desired.update((account_block_id, list_id, "owns") for list_id in list_ids.values())
    desired.update(
      (list_ids[item.list.node_id], repository_ids[node_id], "contains")
      for item in snapshot.lists
      for node_id in item.repository_node_ids
    )
    desired.update(
      (
        _id(account_blocks[item.owner.node_id]),
        repository_ids[item.repository.node_id],
        "owns",
      )
      for item in snapshot.repositories
    )
    return desired

  @staticmethod
  def _managed_relations(  # noqa: PLR0913
    relations: tuple[RelationModel, ...],
    blocks_by_id: dict[int, BlockModel],
    source_block_id: int,
    account_block_id: int,
    list_ids: set[int],
    current_repository_ids: set[int],
  ) -> tuple[RelationModel, ...]:
    managed: list[RelationModel] = []
    for relation in relations:
      from_block = blocks_by_id.get(relation.from_)
      to_block = blocks_by_id.get(relation.to_)
      if (
        (
          relation.content == "collects"
          and relation.from_ == source_block_id
          and to_block is not None
          and to_block.resolver == ACCOUNT_RESOLVER_ID
        )
        or (
          relation.content == "stars"
          and relation.from_ == account_block_id
          and to_block is not None
          and to_block.resolver == REPOSITORY_RESOLVER_ID
        )
        or (
          relation.content == "owns"
          and relation.from_ == account_block_id
          and to_block is not None
          and to_block.resolver == LIST_RESOLVER_ID
        )
        or (
          relation.content == "contains"
          and relation.from_ in list_ids
          and to_block is not None
          and to_block.resolver == REPOSITORY_RESOLVER_ID
        )
        or (
          relation.content == "owns"
          and relation.to_ in current_repository_ids
          and from_block is not None
          and from_block.resolver == ACCOUNT_RESOLVER_ID
        )
      ):
        managed.append(relation)
    return tuple(managed)

  async def _replace_relations(
    self, existing: tuple[RelationModel, ...], desired: set[tuple[int, int, str]]
  ) -> None:
    retained: set[tuple[int, int, str]] = set()
    removed: list[int] = []
    for relation in existing:
      key = (relation.from_, relation.to_, relation.content)
      if key in desired and key not in retained:
        retained.add(key)
      else:
        if relation.id is not None:
          removed.append(relation.id)
        self.relations_deleted += 1
    missing = desired - retained
    await self.uow.graph.relations.delete_many(removed)
    await self.uow.graph.relations.create_many(
      (
        RelationCreateForm(from_=from_, to_=to_, content=content)
        for from_, to_, content in missing
      ),
    )
    self.relations_created += len(missing)


__all__ = ["GitHubGraphReconciler", "GitHubReconcileReport", "GitHubSourceBindingError"]
