"""Presentation-neutral graph-navigation retrieval contracts."""

import typing

import pydantic

from app.schemas.info_base.block import BlockID, BlockModel
from app.schemas.info_base.relation import RelationID, RelationModel


GraphDirection: typing.TypeAlias = typing.Literal["in", "out", "both"]


class GraphModel(pydantic.BaseModel):
  """Endpoint-closed persisted graph read model."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  blocks: tuple[BlockModel, ...]
  relations: tuple[RelationModel, ...]


class BlockNeighborhood(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  focal_block: BlockID
  graph: GraphModel
  next_cursor: RelationID | None = None


class RelationNeighborhood(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  focal_relation: RelationID
  graph: GraphModel


class PathFound(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  status: typing.Literal["found"] = "found"
  graph: GraphModel
  block_path: tuple[BlockID, ...]
  relation_path: tuple[RelationID, ...]


class PathNotFound(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  status: typing.Literal["not_found"] = "not_found"


class PathLimitReached(pydantic.BaseModel):
  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  status: typing.Literal["limit_reached"] = "limit_reached"


PathResult: typing.TypeAlias = typing.Annotated[
  PathFound | PathNotFound | PathLimitReached,
  pydantic.Field(discriminator="status"),
]
