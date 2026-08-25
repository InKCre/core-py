"""Transactional reconciliation of one complete GitHub snapshot."""

from __future__ import annotations

import typing

import pydantic
import sqlalchemy
import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.business.source import SourceManager
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationCreateForm, RelationModel
from app.schemas.source import SourceModel

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


class GitHubGraphRepository:
  """Own exact GitHub identity and current relation-set reconciliation."""

  _resolver_models: typing.ClassVar[dict[str, type[pydantic.BaseModel]]] = {
    ACCOUNT_RESOLVER_ID: GitHubAccount,
    REPOSITORY_RESOLVER_ID: GitHubRepository,
    LIST_RESOLVER_ID: GitHubList,
  }

  def __init__(self, db_session: sqlmodel.Session):
    self.db = db_session
    self.blocks_created = 0
    self.blocks_updated = 0
    self.relations_created = 0
    self.relations_deleted = 0

  def reconcile(self, source_id: int, snapshot: GitHubSnapshot) -> GitHubReconcileReport:
    source = self.db.exec(
      sqlmodel.select(SourceModel).where(SourceModel.id == source_id).with_for_update()
    ).one()
    state = GitHubSourceState.model_validate(source.state or {})
    if (
      state.account_node_id is not None
      and state.account_node_id != snapshot.account.node_id
    ):
      raise GitHubSourceBindingError(
        "GitHub Source token resolves to a different Account; create another Source"
      )

    source_anchor = SourceManager.ensure_block(source, self.db)
    existing = self._load_github_blocks()
    repositories = {
      fact.repository.node_id: fact.repository for fact in snapshot.repositories
    }
    accounts = {fact.owner.node_id: fact.owner for fact in snapshot.repositories}
    accounts[snapshot.account.node_id] = snapshot.account
    lists = {fact.list.node_id: fact.list for fact in snapshot.lists}

    repository_blocks = self._upsert_many(GitHubRepositoryResolver, repositories, existing)
    account_blocks = self._upsert_many(GitHubAccountResolver, accounts, existing)
    list_blocks = self._upsert_many(GitHubListResolver, lists, existing)

    source_block_id = _id(source_anchor)
    account_block_id = _id(account_blocks[snapshot.account.node_id])
    repository_ids = {node_id: _id(block) for node_id, block in repository_blocks.items()}
    current_list_ids = {node_id: _id(block) for node_id, block in list_blocks.items()}
    previous_list_ids = self._previous_list_ids(account_block_id, existing)
    roots = {
      source_block_id,
      account_block_id,
      *previous_list_ids,
      *current_list_ids.values(),
    }
    candidates = self._load_candidate_relations(roots, set(repository_ids.values()))

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
    self._replace_relations(managed, desired)

    source.state = GitHubSourceState(account_node_id=snapshot.account.node_id).model_dump(
      mode="json"
    )
    self.db.add(source)
    self.db.flush()
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

  def _load_github_blocks(self) -> dict[tuple[str, str], BlockModel]:
    blocks = self.db.exec(
      sqlmodel.select(BlockModel).where(
        BlockModel.resolver.in_(tuple(self._resolver_models))  # type: ignore[union-attr]
      )
    ).all()
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

  def _upsert_many(
    self,
    resolver_cls: typing.Any,
    contents: typing.Mapping[str, GitHubAccount | GitHubRepository | GitHubList],
    existing: dict[tuple[str, str], BlockModel],
  ) -> dict[str, BlockModel]:
    resolver_id = typing.cast(str, resolver_cls.__rsotype__)
    result: dict[str, BlockModel] = {}
    missing: list[tuple[str, typing.Any]] = []
    for node_id, content in contents.items():
      form = resolver_cls.create_block(content)
      block = existing.get((resolver_id, node_id))
      if block is None:
        missing.append((node_id, form))
      else:
        if block.content != form.content or block.storage is not None:
          block.storage = None
          block.content = form.content
          self.db.add(block)
          self.blocks_updated += 1
        result[node_id] = block
    created = BlockManager.create_many((form for _, form in missing), self.db)
    self.blocks_created += len(created)
    for (node_id, _), block in zip(missing, created, strict=True):
      result[node_id] = block
      existing[(resolver_id, node_id)] = block
    return result

  def _previous_list_ids(
    self, account_id: int, blocks: dict[tuple[str, str], BlockModel]
  ) -> set[int]:
    list_ids = {
      _id(block) for (resolver, _), block in blocks.items() if resolver == LIST_RESOLVER_ID
    }
    if not list_ids:
      return set()
    return set(
      self.db.exec(
        sqlmodel.select(RelationModel.to_).where(
          RelationModel.from_ == account_id,
          RelationModel.content == "owns",
          RelationModel.to_.in_(tuple(list_ids)),  # type: ignore[union-attr]
        )
      ).all()
    )

  def _load_candidate_relations(
    self, roots: set[int], repository_ids: set[int]
  ) -> tuple[RelationModel, ...]:
    endpoints = roots | repository_ids
    if not endpoints:
      return ()
    return tuple(
      self.db.exec(
        sqlmodel.select(RelationModel).where(
          RelationModel.content.in_(("collects", "stars", "owns", "contains")),  # type: ignore[union-attr]
          sqlalchemy.or_(
            RelationModel.from_.in_(tuple(endpoints)),  # type: ignore[union-attr]
            RelationModel.to_.in_(tuple(endpoints)),  # type: ignore[union-attr]
          ),
        )
      ).all()
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

  def _replace_relations(
    self, existing: tuple[RelationModel, ...], desired: set[tuple[int, int, str]]
  ) -> None:
    retained: set[tuple[int, int, str]] = set()
    for relation in existing:
      key = (relation.from_, relation.to_, relation.content)
      if key in desired and key not in retained:
        retained.add(key)
      else:
        self.db.delete(relation)
        self.relations_deleted += 1
    missing = desired - retained
    RelationManager.create_many(
      (
        RelationCreateForm(from_=from_, to_=to_, content=content)
        for from_, to_, content in missing
      ),
      self.db,
    )
    self.relations_created += len(missing)


__all__ = ["GitHubGraphRepository", "GitHubReconcileReport", "GitHubSourceBindingError"]
