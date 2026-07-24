import asyncio
import base64
import typing
import json
import tencentcloud.common.credential
import tencentcloud.lke.v20231130.lke_client
import tencentcloud.lke.v20231130.models
import aiohttp
import sqlmodel

from typing import Optional as Opt

from .main import BreakdownItem, Resolver
from app.schemas.info_base.main import SubGraphForm, ArcForm
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.engine import SessionLocal
from utils.base import AIOHTTP_CONNECTOR_GETTER


TENCENT_LKE_CLIENT = tencentcloud.lke.v20231130.lke_client.LkeClient(
  tencentcloud.common.credential.EnvironmentVariableCredential().get_credential(),
  "ap-guangzhou",
)


class Detail(typing.TypedDict):
  type: str
  content: str
  actions: list[str]


class Img2TextResult(typing.TypedDict):
  details: list[Detail]
  summary: str


class ImageResolver(Resolver[str, bytes], rso_type="image"):
  @classmethod
  def create_graph(cls, url: str, alt_text: Opt[str] = None) -> SubGraphForm:
    return SubGraphForm(
      block=BlockModel(resolver=cls.__rsotype__, content=url, storage=-1),
      out_arcs=(
        ArcForm(
          relation=RelationModel(content="alt:text"),
          to_subgraph=cls.__create_text_brs(alt_text),
        ),
      )
      if alt_text
      else (),
    )

  @classmethod
  def __create_text_brs(cls, text: str) -> SubGraphForm:
    from .text import TextResolver

    return TextResolver.create_graph(text)

  def __get_custom_variables(self) -> dict:
    if self._block.storage is None:
      return {
        "ImgSource": base64.b64encode(self._block.content.encode("utf-8")).decode("utf-8")
      }
    if self._block.storage != -1:
      raise NotImplementedError(
        f"Image workflow does not support storage {self._block.storage}"
      )
    return {"ImgURL": self._block.content}

  async def __img2text(self) -> Img2TextResult:
    """Transform image to text

    - summary of image
    - key infos image provided
      - actions that needs the info
    """
    return Img2TextResult(
      **(
        await self.__run_lke_workflow(
          "1948959057036216384", **self.__get_custom_variables()
        )
      )["result"]
    )

  async def __run_lke_workflow(self, workflow_id: str, **kwargs) -> dict:
    create_request = tencentcloud.lke.v20231130.models.CreateWorkflowRunRequest()
    create_request.AppBizId = workflow_id
    create_request.CustomVariables = tuple(
      {"Name": key, "Value": value} for key, value in kwargs.items()
    )
    create_response = TENCENT_LKE_CLIENT.CreateWorkflowRun(create_request)
    workflow_run_id = create_response.WorkflowRunId
    if not isinstance(workflow_run_id, str):
      raise RuntimeError("Tencent LKE did not return a workflow run ID")

    describe_request = tencentcloud.lke.v20231130.models.DescribeWorkflowRunRequest()
    describe_request.WorkflowRunId = workflow_run_id
    while True:
      describe_response = TENCENT_LKE_CLIENT.DescribeWorkflowRun(describe_request)
      workflow_run = describe_response.WorkflowRun
      if workflow_run is None:
        raise RuntimeError("Tencent LKE did not return workflow state")
      if workflow_run.State in (2, 3, 4):
        break
      await asyncio.sleep(1)

    for node in describe_response.NodeRuns or ():
      if node.NodeType == 16:
        node_run_id = node.NodeRunId
        if not isinstance(node_run_id, str):
          raise RuntimeError("Tencent LKE end node is missing its run ID")
        node_request = tencentcloud.lke.v20231130.models.DescribeNodeRunRequest()
        node_request.NodeRunId = node_run_id
        node_response = TENCENT_LKE_CLIENT.DescribeNodeRun(node_request)
        node_run = node_response.NodeRun
        if node_run is None:
          raise RuntimeError("Tencent LKE did not return end-node output")

        output_ref = node_run.OutputRef
        if output_ref is None:
          output = node_run.Output
          if not isinstance(output, str):
            raise RuntimeError("Tencent LKE end node returned no inline output")
          parsed_output = json.loads(output)
          if not isinstance(parsed_output, dict):
            raise RuntimeError("Tencent LKE workflow output must be a JSON object")
          return parsed_output

        if not isinstance(output_ref, str):
          raise RuntimeError("Tencent LKE returned an invalid output URL")
        # TODO extract to download()
        async with aiohttp.ClientSession(connector=AIOHTTP_CONNECTOR_GETTER()) as session:
          async with session.get(output_ref) as response:
            response.raise_for_status()
            remote_output = await response.json()
            if not isinstance(remote_output, dict):
              raise RuntimeError("Tencent LKE workflow output must be a JSON object")
            return remote_output

    raise RuntimeError("Workflow did not complete successfully.")

  async def breakdown(
    self,
  ) -> typing.AsyncGenerator[BreakdownItem, BreakdownItem]:
    """Persist an image summary and its extracted details as related blocks."""
    img2text_result = await self.__img2text()

    # alt:text
    alt_text_block = typing.cast(
      BlockModel,
      (yield BlockModel(resolver="text", content=img2text_result["summary"])),
    )
    yield RelationModel(
      from_=self.block_id,
      to_=typing.cast(int, alt_text_block.id),
      content="alt:text",
    )

    # info (key information)
    for item in img2text_result["details"]:
      info_block = typing.cast(
        BlockModel,
        (yield BlockModel(resolver="text", content=item["content"])),
      )
      yield RelationModel(
        from_=self.block_id,
        to_=typing.cast(int, info_block.id),
        content="has content",
      )
      info_type_block = typing.cast(
        BlockModel,
        (yield BlockModel(resolver="text", content=item["type"])),
      )
      yield RelationModel(
        from_=typing.cast(int, info_block.id),
        to_=typing.cast(int, info_type_block.id),
        content="is",
      )
      for action in item["actions"]:
        action_block = typing.cast(
          BlockModel,
          (yield BlockModel(resolver="text", content=action)),
        )
        yield RelationModel(
          from_=typing.cast(int, action_block.id),
          to_=typing.cast(int, info_type_block.id),
          content="needs",
        )

  async def get_text(self) -> str:
    """find relation "alt:text" and return the to block content"""
    with SessionLocal() as db_session:
      alt_text_relation = db_session.exec(
        sqlmodel.select(RelationModel).where(
          sqlmodel.col(RelationModel.content) == "alt:text",
          sqlmodel.col(RelationModel.from_) == self.block_id,
        )
      ).one_or_none()
      if alt_text_relation:
        alt_text_to_block = db_session.exec(
          sqlmodel.select(BlockModel).where(
            sqlmodel.col(BlockModel.id) == alt_text_relation.to_
          )
        ).one()
        return alt_text_to_block.content

      img2text_result = await self.__img2text()
      alt_text_block = BlockModel(resolver="text", content=img2text_result["summary"])
      db_session.add(alt_text_block)
      db_session.flush()
      if alt_text_block.id is None:
        raise RuntimeError("Persisted alt-text block is missing its database ID")
      alt_text_relation = RelationModel(
        content="alt:text",
        to_=alt_text_block.id,
        from_=self.block_id,
      )
      db_session.add(alt_text_relation)

      db_session.commit()

      return img2text_result["summary"]

  async def get_str_for_embedding(self) -> str:
    """Use the image's text representation as the embedding input."""
    return await self.get_text()
