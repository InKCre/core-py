"""Organization rumination configuration, inbound, and Agent Tool forms."""

import pydantic

from app.schemas.ai import JSONValue
from app.schemas.info_base.block import BlockID
from app.schemas.info_base.main import GraphForm, NegativeBlockID


class RuminationConfig(pydantic.BaseModel):
  """Deployment selection of one reusable Agent definition."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  agent: int


class RuminationRequest(pydantic.BaseModel):
  """Explicit request to reconsider one focal Block."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  block: BlockID


class GetDraftGraphSchemaInput(pydantic.BaseModel):
  """Generic schema-discovery input narrowed when an Agent run binds Tools."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  resolvers: tuple[str, ...]


class DraftGraphInput(pydantic.BaseModel):
  """Generic draft request; Resolver input is validated by its bound run model."""

  model_config = pydantic.ConfigDict(extra="forbid")

  resolver: str
  input: dict[str, JSONValue]
  id_start: NegativeBlockID = -1


class SubmitGraphInput(pydantic.BaseModel):
  """The sole rumination Tool input that can mutate the info-base graph."""

  model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

  graph: GraphForm
