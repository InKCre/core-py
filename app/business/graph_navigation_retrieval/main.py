"""Bounded, presentation-neutral navigation over persisted graph authority."""

import typing

import sqlmodel

from app.business.info_base.block import BlockManager
from app.business.info_base.relation import RelationManager
from app.engine import SessionLocal
from app.schemas.graph_navigation_retrieval import (
  BlockNeighborhood,
  GraphDirection,
  GraphModel,
  PathFound,
  PathLimitReached,
  PathNotFound,
  PathResult,
  RelationNeighborhood,
)
from app.schemas.info_base.block import BlockID, BlockModel
from app.schemas.info_base.relation import RelationID, RelationModel


DEFAULT_NEIGHBORHOOD_LIMIT = 20
MAX_NEIGHBORHOOD_LIMIT = 100
DEFAULT_MAX_HOPS = 4
MAX_MAX_HOPS = 8
DEFAULT_MAX_EXPLORED_BLOCKS = 1000
MAX_MAX_EXPLORED_BLOCKS = 10000
FRONTIER_QUERY_SIZE = 200


class GraphNavigationRetrievalManager:
  """Own graph-navigation semantics while hiding query and closure mechanics."""

  @classmethod
  def get_random_block(
    cls,
    db_session: sqlmodel.Session | None = None,
  ) -> BlockModel | None:
    return BlockManager.get_random(db_session)

  @classmethod
  def get_block_neighborhood(  # noqa: PLR0913
    cls,
    focal_block: BlockID,
    *,
    direction: GraphDirection = "both",
    contents: typing.Collection[str] = (),
    limit: int = DEFAULT_NEIGHBORHOOD_LIMIT,
    cursor: RelationID | None = None,
    db_session: sqlmodel.Session | None = None,
  ) -> BlockNeighborhood | None:
    if not 1 <= limit <= MAX_NEIGHBORHOOD_LIMIT:
      raise ValueError(f"limit must be between 1 and {MAX_NEIGHBORHOOD_LIMIT}")
    if db_session is None:
      with SessionLocal() as owned_session:
        return cls.get_block_neighborhood(
          focal_block,
          direction=direction,
          contents=contents,
          limit=limit,
          cursor=cursor,
          db_session=owned_session,
        )
    focal = BlockManager.get(focal_block, db_session)
    if focal is None:
      return None

    requested = limit + 1
    branches: list[tuple[RelationModel, ...]] = []
    if direction in ("out", "both"):
      branches.append(
        RelationManager.get_endpoint_page(
          (focal_block,),
          endpoint="from",
          contents=contents,
          cursor=cursor,
          limit=requested,
          db_session=db_session,
        )
      )
    if direction in ("in", "both"):
      branches.append(
        RelationManager.get_endpoint_page(
          (focal_block,),
          endpoint="to",
          contents=contents,
          cursor=cursor,
          limit=requested,
          db_session=db_session,
        )
      )
    by_id = {
      relation.id: relation
      for branch in branches
      for relation in branch
      if relation.id is not None
    }
    ordered = sorted(
      by_id.values(),
      key=lambda relation: typing.cast(int, relation.id),
      reverse=True,
    )
    page = ordered[:requested]
    has_more = len(page) > limit
    page = page[:limit]
    endpoint_ids = {focal_block}
    for relation in page:
      endpoint_ids.update((relation.from_, relation.to_))
    blocks = BlockManager.get_many(endpoint_ids, db_session)
    existing_ids = {block.id for block in blocks}
    closed_relations = tuple(
      relation
      for relation in page
      if relation.from_ in existing_ids and relation.to_ in existing_ids
    )
    next_cursor = typing.cast(RelationID, page[-1].id) if has_more and page else None
    return BlockNeighborhood(
      focal_block=focal_block,
      graph=GraphModel(blocks=blocks, relations=closed_relations),
      next_cursor=next_cursor,
    )

  @classmethod
  def get_relation_neighborhood(
    cls,
    focal_relation: RelationID,
    *,
    db_session: sqlmodel.Session | None = None,
  ) -> RelationNeighborhood | None:
    if db_session is None:
      with SessionLocal() as owned_session:
        return cls.get_relation_neighborhood(focal_relation, db_session=owned_session)
    relation = RelationManager.get_by_id(focal_relation, db_session)
    if relation is None:
      return None
    blocks = BlockManager.get_many((relation.from_, relation.to_), db_session)
    if {block.id for block in blocks} != {relation.from_, relation.to_}:
      return None
    return RelationNeighborhood(
      focal_relation=focal_relation,
      graph=GraphModel(blocks=blocks, relations=(relation,)),
    )

  @classmethod
  def find_path(  # noqa: PLR0913
    cls,
    from_block: BlockID,
    to_block: BlockID,
    *,
    direction: GraphDirection = "both",
    contents: typing.Collection[str] = (),
    max_hops: int = DEFAULT_MAX_HOPS,
    max_explored_blocks: int = DEFAULT_MAX_EXPLORED_BLOCKS,
    db_session: sqlmodel.Session | None = None,
  ) -> PathResult:
    if not 0 <= max_hops <= MAX_MAX_HOPS:
      raise ValueError(f"max_hops must be between 0 and {MAX_MAX_HOPS}")
    if not 1 <= max_explored_blocks <= MAX_MAX_EXPLORED_BLOCKS:
      raise ValueError(
        f"max_explored_blocks must be between 1 and {MAX_MAX_EXPLORED_BLOCKS}"
      )
    if db_session is None:
      with SessionLocal() as owned_session:
        return cls.find_path(
          from_block,
          to_block,
          direction=direction,
          contents=contents,
          max_hops=max_hops,
          max_explored_blocks=max_explored_blocks,
          db_session=owned_session,
        )
    endpoints = BlockManager.get_many((from_block, to_block), db_session)
    if {block.id for block in endpoints} != {from_block, to_block}:
      return PathNotFound()
    if from_block == to_block:
      return PathFound(
        graph=GraphModel(blocks=endpoints, relations=()),
        block_path=(from_block,),
        relation_path=(),
      )

    forward_parents: dict[BlockID, tuple[BlockID, RelationID] | None] = {from_block: None}
    backward_next: dict[BlockID, tuple[BlockID, RelationID] | None] = {to_block: None}
    forward_depths = {from_block: 0}
    backward_depths = {to_block: 0}
    forward_frontier = {from_block}
    backward_frontier = {to_block}

    while forward_frontier and backward_frontier:
      forward_level = forward_depths[next(iter(forward_frontier))]
      backward_level = backward_depths[next(iter(backward_frontier))]
      if forward_level + backward_level >= max_hops:
        return PathLimitReached()

      expand_forward = len(forward_frontier) <= len(backward_frontier)
      if expand_forward:
        next_frontier, meeting = cls._expand_path_frontier(
          forward_frontier,
          direction=direction,
          contents=contents,
          reverse=False,
          own_steps=forward_parents,
          own_depths=forward_depths,
          other_depths=backward_depths,
          max_hops=max_hops,
          db_session=db_session,
        )
        forward_frontier = next_frontier
      else:
        next_frontier, meeting = cls._expand_path_frontier(
          backward_frontier,
          direction=direction,
          contents=contents,
          reverse=True,
          own_steps=backward_next,
          own_depths=backward_depths,
          other_depths=forward_depths,
          max_hops=max_hops,
          db_session=db_session,
        )
        backward_frontier = next_frontier
      explored = set(forward_parents) | set(backward_next)
      if len(explored) > max_explored_blocks:
        return PathLimitReached()
      if meeting is not None:
        return cls._assemble_bidirectional_path(
          from_block,
          to_block,
          meeting=meeting,
          forward_parents=forward_parents,
          backward_next=backward_next,
          direction=direction,
          contents=contents,
          db_session=db_session,
        )
    return PathNotFound()

  @classmethod
  def _expand_path_frontier(  # noqa: PLR0913
    cls,
    frontier: set[BlockID],
    *,
    direction: GraphDirection,
    contents: typing.Collection[str],
    reverse: bool,
    own_steps: dict[BlockID, tuple[BlockID, RelationID] | None],
    own_depths: dict[BlockID, int],
    other_depths: dict[BlockID, int],
    max_hops: int,
    db_session: sqlmodel.Session,
  ) -> tuple[set[BlockID], BlockID | None]:
    next_frontier: set[BlockID] = set()
    meeting: BlockID | None = None
    best_hops: int | None = None
    for chunk_start in range(0, len(frontier), FRONTIER_QUERY_SIZE):
      chunk = tuple(frontier)[chunk_start : chunk_start + FRONTIER_QUERY_SIZE]
      relations = cls._frontier_relations(
        chunk,
        direction=direction,
        contents=contents,
        reverse=reverse,
        db_session=db_session,
      )
      for relation in relations:
        relation_id = typing.cast(RelationID, relation.id)
        for current, neighbor in cls._relation_steps(
          relation, frontier=set(chunk), direction=direction, reverse=reverse
        ):
          if neighbor in own_steps:
            continue
          own_steps[neighbor] = (current, relation_id)
          own_depths[neighbor] = own_depths[current] + 1
          next_frontier.add(neighbor)
          if neighbor not in other_depths:
            continue
          hops = own_depths[neighbor] + other_depths[neighbor]
          if hops <= max_hops and (best_hops is None or hops < best_hops):
            best_hops = hops
            meeting = neighbor
    return next_frontier, meeting

  @staticmethod
  def _relation_steps(
    relation: RelationModel,
    *,
    frontier: set[BlockID],
    direction: GraphDirection,
    reverse: bool,
  ) -> tuple[tuple[BlockID, BlockID], ...]:
    steps: list[tuple[BlockID, BlockID]] = []
    if not reverse:
      if direction in ("out", "both") and relation.from_ in frontier:
        steps.append((relation.from_, relation.to_))
      if direction in ("in", "both") and relation.to_ in frontier:
        steps.append((relation.to_, relation.from_))
    else:
      if direction in ("out", "both") and relation.to_ in frontier:
        steps.append((relation.to_, relation.from_))
      if direction in ("in", "both") and relation.from_ in frontier:
        steps.append((relation.from_, relation.to_))
    return tuple(steps)

  @classmethod
  def _frontier_relations(
    cls,
    frontier: typing.Collection[BlockID],
    *,
    direction: GraphDirection,
    contents: typing.Collection[str],
    reverse: bool = False,
    db_session: sqlmodel.Session,
  ) -> tuple[RelationModel, ...]:
    relations: dict[RelationID, RelationModel] = {}
    needs_from = (
      direction in ("out", "both")
      if not reverse
      else direction
      in (
        "in",
        "both",
      )
    )
    needs_to = (
      direction in ("in", "both")
      if not reverse
      else direction
      in (
        "out",
        "both",
      )
    )
    if needs_from:
      for relation in RelationManager.get_endpoint_page(
        frontier,
        endpoint="from",
        contents=contents,
        limit=MAX_MAX_EXPLORED_BLOCKS,
        db_session=db_session,
      ):
        if relation.id is not None:
          relations[relation.id] = relation
    if needs_to:
      for relation in RelationManager.get_endpoint_page(
        frontier,
        endpoint="to",
        contents=contents,
        limit=MAX_MAX_EXPLORED_BLOCKS,
        db_session=db_session,
      ):
        if relation.id is not None:
          relations[relation.id] = relation
    return tuple(relations.values())

  @classmethod
  def _assemble_bidirectional_path(  # noqa: PLR0913
    cls,
    from_block: BlockID,
    to_block: BlockID,
    *,
    meeting: BlockID,
    forward_parents: dict[BlockID, tuple[BlockID, RelationID] | None],
    backward_next: dict[BlockID, tuple[BlockID, RelationID] | None],
    direction: GraphDirection,
    contents: typing.Collection[str],
    db_session: sqlmodel.Session,
  ) -> PathFound:
    block_path: list[BlockID] = [meeting]
    relation_path: list[RelationID] = []
    current = meeting
    while current != from_block:
      parent = forward_parents[current]
      if parent is None:  # pragma: no cover - reconstruction invariant
        raise RuntimeError("Path reconstruction lost its parent")
      current, relation_id = parent
      block_path.append(current)
      relation_path.append(relation_id)
    block_path.reverse()
    relation_path.reverse()
    current = meeting
    while current != to_block:
      next_step = backward_next[current]
      if next_step is None:  # pragma: no cover - reconstruction invariant
        raise RuntimeError("Path reconstruction lost its next step")
      current, relation_id = next_step
      block_path.append(current)
      relation_path.append(relation_id)
    blocks = BlockManager.get_many(block_path, db_session)
    relations = tuple(
      relation
      for relation_id in relation_path
      if (relation := RelationManager.get_by_id(relation_id, db_session)) is not None
    )
    if {block.id for block in blocks} != set(block_path) or len(relations) != len(
      relation_path
    ):
      raise RuntimeError("Persisted path changed during retrieval")
    for index, relation in enumerate(relations):
      from_path = block_path[index]
      to_path = block_path[index + 1]
      direction_valid = (
        (direction == "both" and {relation.from_, relation.to_} == {from_path, to_path})
        or (direction == "out" and (relation.from_, relation.to_) == (from_path, to_path))
        or (direction == "in" and (relation.to_, relation.from_) == (from_path, to_path))
      )
      if not direction_valid or (contents and relation.content not in contents):
        raise RuntimeError("Persisted path changed during retrieval")
    return PathFound(
      graph=GraphModel(blocks=blocks, relations=relations),
      block_path=tuple(block_path),
      relation_path=tuple(relation_path),
    )
