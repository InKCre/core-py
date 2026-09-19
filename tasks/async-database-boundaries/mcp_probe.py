"""Exercise registered MCP tools through the SDK against isolated PostgreSQL."""

import asyncio
import uuid

from mcp.server import MCPServer
from mcp_types import CallToolResult

from app.business.info_base.resolver import register_core_resolvers
from app.business.sink.mcp import MCPSink
from app.engine import ASYNC_DB_ENGINE
from app.persistence.info_base.uow import graph_uow
from app.schemas.info_base.block import BlockForm
from app.schemas.sink import SinkModel


async def main():
  register_core_resolvers()
  ids = []
  try:
    async with graph_uow() as uow:
      blocks = await uow.blocks.create_many(
        BlockForm(resolver="core.text.v1", content=uuid.uuid4().hex) for _ in range(2)
      )
      ids = [block.id for block in blocks if block.id is not None]
      relation = await uow.relations.create(*ids, content="probe")
    server = MCPServer(name="database-acceptance")
    sink = MCPSink(SinkModel(id=1, type="core.mcp.v1", config={"pat": uuid.uuid4().hex}))
    sink._register_tools(server)
    requests = {
      "inkcre_open_entities": {"entities": [f"block:{ids[0]}", f"relation:{relation.id}"]},
      "inkcre_read_blocks": {"blocks": ids, "content": "raw"},
      "inkcre_expand_entities": {"entities": [f"block:{ids[0]}"]},
      "inkcre_find_path": {"from_block": ids[0], "to_block": ids[1]},
      "inkcre_resolver_methods": {"blocks": ids},
      "inkcre_invoke_resolver_methods": {
        "calls": [{"block": ids[0], "method": "get_label", "arguments": {}}]
      },
    }
    for name, arguments in requests.items():
      result = await server.call_tool(name, arguments)
      assert isinstance(result, CallToolResult) and not result.is_error, (name, result)
      assert "coroutine" not in str(result)
      assert "error" not in str(result.structured_content), (name, result)
      print(name, "passed")
  finally:
    async with graph_uow() as uow:
      for block_id in ids:
        await uow.blocks.delete(block_id)
    await ASYNC_DB_ENGINE.dispose()


if __name__ == "__main__":
  asyncio.run(main())
