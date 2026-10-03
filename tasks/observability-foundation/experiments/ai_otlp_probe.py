"""Synthetic HTTP provider -> real OpenAI SDK -> first OTLP outlet acceptance.

Run from the repository using pdm run python and this script path.
Database lookups use synthetic domain objects; Tools, Resolver, Thread, Sink,
provider HTTP, SDK parsing and OTLP exporters execute their production code.
"""

import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import secrets
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ["INKCRE_ENV_FILE"] = ""
os.environ["DATABASE_URL"] = "postgresql://probe:probe@127.0.0.1:1/probe"
os.environ["JWT_SECRET"] = secrets.token_hex(32)

import pydantic
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
  ExportTraceServiceRequest,
)
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
  ExportMetricsServiceRequest,
)

from app.business.ai import AIManager
from app.business.agent import (
  BoundAgentTool,
  InMemoryThreadPersistenceBackend,
  Thread,
  ThreadState,
)
from app.schemas.ai import (
  AIModelModel,
  AIProviderModel,
  ChatCapability,
  EmbeddingCapability,
  FunctionTool,
  TextContentPart,
  UserMessage,
)
from app.business.agent.contracts import ToolExecutionError
from app.business.agent import AgentManager
from app.business.info_base.main import InfoBaseManager, RetrievalBranch
from app.business.info_base.services import BlockService
from app.business.info_base import tools as info_tools
from app.business.info_base.resolver import tools as resolver_tools
from app.business.info_base.resolver.text import TextResolver
from app.business.sink.agent_query import AgentQuerySink
from app.schemas.info_base.block import BlockModel
from app.schemas.info_base.relation import RelationModel
from app.schemas.semantic_retrieval import (
  SemanticRetrievalResult,
  BlockSemanticRetrievalMatch,
  RelationSemanticRetrievalMatch,
)
from app.schemas.job import JobModel
from app.schemas.sink import SinkModel
from libs.obsrv.telemetry import start_telemetry, close_telemetry, operation

CANARY = "CONTENT_CANARY_4f7ca94e"
exports = []
requests = []


class Server(BaseHTTPRequestHandler):
  def log_message(self, *_args):
    pass

  def do_POST(self):
    body = self.rfile.read(int(self.headers["Content-Length"]))
    if self.path.startswith("/otlp/"):
      exports.append((self.path, body))
      self.send_response(200)
      self.end_headers()
      return
    request = json.loads(body)
    requests.append(request)
    model = request["model"]
    if model == "error":
      self.send_response(400)
      self.send_header("Content-Type", "application/json")
      self.end_headers()
      self.wfile.write(
        json.dumps({"error": {"message": CANARY, "type": "invalid_request_error"}}).encode()
      )
      return
    self.send_response(200)
    self.send_header(
      "Content-Type", "text/event-stream" if request.get("stream") else "application/json"
    )
    self.end_headers()
    usage = {
      "prompt_tokens": 7,
      "completion_tokens": 0,
      "total_tokens": 7,
      "prompt_tokens_details": {"cached_tokens": 3},
      "completion_tokens_details": {"reasoning_tokens": 0},
    }
    if request.get("stream"):
      for choice, chunk_usage in [
        ([{"index": 0, "delta": {"content": CANARY}, "finish_reason": None}], usage),
        ([{"index": 0, "delta": {}, "finish_reason": "stop"}], None),
        ([], usage),
      ]:
        chunk = {
          "id": CANARY,
          "object": "chat.completion.chunk",
          "created": 1,
          "model": CANARY,
          "choices": choice,
          "usage": chunk_usage,
        }
        self.wfile.write(("data: " + json.dumps(chunk) + "\n\n").encode())
      self.wfile.write(b"data: [DONE]\n\n")
      return
    if self.path.endswith("/embeddings"):
      response = {
        "object": "list",
        "model": CANARY,
        "data": [{"object": "embedding", "index": 0, "embedding": [1.0, 2.0]}],
        "usage": {"prompt_tokens": 5, "total_tokens": 5},
      }
    else:
      message = {"role": "assistant", "content": CANARY}
      if model == "tools":
        message = {
          "role": "assistant",
          "content": None,
          "tool_calls": [
            {
              "id": CANARY + str(i),
              "type": "function",
              "function": {
                "name": "probe.tool",
                "arguments": json.dumps({"value": CANARY}),
              },
            }
            for i in range(2)
          ],
        }
      if model == "journey":
        completed = sum(item["role"] == "tool" for item in request["messages"])
        actions = [
          [("retrieve", {"query": CANARY, "mode": "semantic"})],
          [
            (
              "get_entities",
              {
                "entities": [
                  {"type": "block", "id": 11},
                  {"type": "relation", "id": 21},
                  {"type": "block", "id": 99},
                ]
              },
            )
          ],
          [
            (
              "resolver",
              {
                "action": "invoke",
                "calls": [{"block_id": 11, "method": "get_text", "arguments": {}}],
              },
            )
          ],
          [
            (
              "submit_query_result",
              {"answer": CANARY, "references": [{"type": "block", "id": 11}]},
            ),
            (
              "submit_query_result",
              {"answer": CANARY, "references": [{"type": "relation", "id": 21}]},
            ),
          ],
        ][completed]
        message = {
          "role": "assistant",
          "content": None,
          "tool_calls": [
            {
              "id": CANARY + str(index),
              "type": "function",
              "function": {"name": name, "arguments": json.dumps(arguments)},
            }
            for index, (name, arguments) in enumerate(actions)
          ],
        }
      response = {
        "id": CANARY,
        "object": "chat.completion",
        "created": 1,
        "model": CANARY,
        "choices": [
          {
            "index": 0,
            "message": message,
            "finish_reason": "tool_calls" if model == "tools" else CANARY,
          }
        ],
        "usage": usage if model != "unknown" else None,
      }
      if model == "partial":
        response["usage"] = {"prompt_tokens": -1, "completion_tokens": 2, "total_tokens": 2}
    self.wfile.write(json.dumps(response).encode())


class ToolInput(pydantic.BaseModel):
  value: str


async def main():
  server = ThreadingHTTPServer(("127.0.0.1", 0), Server)
  threading.Thread(target=server.serve_forever, daemon=True).start()
  origin = f"http://127.0.0.1:{server.server_port}"
  for signal in ("TRACES", "METRICS", "LOGS"):
    os.environ[f"OTEL_EXPORTER_OTLP_{signal}_ENDPOINT"] = f"{origin}/otlp/{signal.lower()}"
  start_telemetry(enabled=True, service_version="ai-probe")
  names = {
    1: "known",
    2: "unknown",
    3: "partial",
    4: "stream",
    5: "tools",
    6: "error",
    7: "journey",
  }
  original_loader = AIManager.__dict__["_load_target_async"]

  async def load_target(cls, model_id):
    dialect = (
      "core.alibaba-model-studio.v1" if model_id == 4 else "core.openai-compatible.v1"
    )
    provider = AIProviderModel(
      id=1,
      name=CANARY,
      dialect=dialect,
      config={"api_key": CANARY, "base_url": origin + "/v1"},
    )
    model = AIModelModel(
      id=model_id,
      provider=1,
      native_model_id=names[model_id],
      capabilities=(
        ChatCapability(
          input_modalities=["text"], output_modalities=["text"], features=["tool_calling"]
        ),
        EmbeddingCapability(input_modalities=["text"], output_modalities=["vector"]),
      ),
    )
    return cls._execution_target(model_id, model, provider)

  AIManager._load_target_async = classmethod(load_target)
  try:
    user = UserMessage(content=(TextContentPart(text=CANARY),))
    for model_id in (1, 2, 3, 4):
      result = await AIManager.chat(model_id, [user])
      assert result.content == CANARY
    assert await AIManager.embed(1, [CANARY], 2) == ((1.0, 2.0),)
    try:
      await AIManager.chat(6, [user])
    except Exception as error:
      assert CANARY in str(error)
    else:
      raise AssertionError("expected provider rejection")

    running = 0
    overlapped = asyncio.Event()

    async def handler(value):
      nonlocal running
      running += 1
      ordinal = running
      if running == 2:
        overlapped.set()
      await asyncio.wait_for(overlapped.wait(), 2)
      if ordinal == 2:
        raise ToolExecutionError({"error": CANARY})
      return value.value

    backend = InMemoryThreadPersistenceBackend()
    tool = BoundAgentTool(
      FunctionTool(
        id="probe.tool", description=CANARY, input_schema=ToolInput.model_json_schema()
      ),
      ToolInput,
      handler,
    )
    ident, state = await backend.create(
      ThreadState(
        model=5,
        tools=(tool.definition,),
        tool_choice="auto",
        max_model_calls_per_turn=1,
        messages=(),
      )
    )
    thread = Thread(ident, state, backend, (tool,))
    assert (await thread.start_turn(user)).value == "max_model_calls"
    assert overlapped.is_set()
    assert len(thread.messages[-1].results) == 2
    assert [result.is_error for result in thread.messages[-1].results] == [False, True]
    entered = asyncio.Event()

    async def blocking_handler(value):
      entered.set()
      await asyncio.Event().wait()

    blocking_tool = BoundAgentTool(tool.definition, ToolInput, blocking_handler)
    ident, state = await backend.create(state)
    cancelled_thread = Thread(ident, state, backend, (blocking_tool,))
    task = cancelled_thread.start_turn(user)
    await asyncio.wait_for(entered.wait(), 2)
    task.cancel()
    try:
      await task
    except asyncio.CancelledError:
      pass
    else:
      raise AssertionError("cancellation must propagate")
    assert len(cancelled_thread.messages) == 1

    # Synthetic domain data isolates the real Tool / Resolver / Thread / Sink journey.
    block = BlockModel(id=11, resolver=TextResolver.__rsotype__, content=CANARY)
    candidate_only = BlockModel(id=12, resolver=TextResolver.__rsotype__, content=CANARY)
    relation = RelationModel(id=21, from_=11, to_=12, content=CANARY)

    async def retrieve_data(cls, query, mode, limit):
      return {
        "semantic": RetrievalBranch(
          result=SemanticRetrievalResult(
            profile=1,
            matches=(
              BlockSemanticRetrievalMatch(entity=block, score=0.9),
              BlockSemanticRetrievalMatch(entity=candidate_only, score=0.8),
              RelationSemanticRetrievalMatch(entity=relation, score=0.7),
            ),
          )
        )
      }

    async def read_data(cls, references, *, random_count=1):
      assert references == (("block", 11), ("relation", 21), ("block", 99))
      return block, relation, None

    async def read_block(cls, identity):
      assert identity == 11
      return block

    async def run_agent(cls, agent_id, initial_message):
      bound = cls._bind_tools(
        (
          info_tools.RETRIEVE_TOOL,
          info_tools.GET_ENTITIES_TOOL,
          resolver_tools.RESOLVER_TOOL,
          "submit_query_result",
        )
      )
      ident, state = await backend.create(
        ThreadState(
          model=7,
          tools=tuple(tool.definition for tool in bound),
          tool_choice="auto",
          max_model_calls_per_turn=4,
          messages=(),
        )
      )
      thread = Thread(ident, state, backend, bound)
      thread.start_turn(initial_message)
      return thread

    saved = [
      (owner, name, owner.__dict__[name])
      for owner, name in [
        (InfoBaseManager, "retrieve"),
        (InfoBaseManager, "get_entities"),
        (BlockService, "get"),
        (AgentManager, "run"),
      ]
    ]
    InfoBaseManager.retrieve = classmethod(retrieve_data)
    InfoBaseManager.get_entities = classmethod(read_data)
    BlockService.get = classmethod(read_block)
    AgentManager.run = classmethod(run_agent)
    try:
      job = JobModel(
        id=31, type="core.sink.agent-query.v1", parameters={}, state={}, timeout_seconds=30
      )
      sink = AgentQuerySink(
        SinkModel(id=41, type="core.agent-query.v1", config={"agent": 1})
      )
      with operation("job.execute", attributes={"inkcre.job.id": 31}):
        await sink.execute(job, CANARY)
      assert job.state["result"] == {
        "answer": CANARY,
        "references": [{"type": "relation", "id": 21}],
      }
    finally:
      for owner, name, original in saved:
        setattr(owner, name, original)

  finally:
    await close_telemetry()
    try:
      outside_provider = TracerProvider()
      with outside_provider.get_tracer("third-party").start_as_current_span(
        "outside"
      ) as outside:
        assert (await AIManager.chat(4, [user])).content == CANARY
        assert trace.get_current_span() is outside
        assert not outside.attributes
      outside_provider.shutdown()
    finally:
      AIManager._load_target_async = original_loader
      server.shutdown()

  assert requests and exports
  assert all(CANARY.encode() not in body for _, body in exports)
  spans = []
  metrics = []
  logs = []
  for path, body in exports:
    if path.endswith("traces"):
      batch = ExportTraceServiceRequest.FromString(body)
      spans.extend(
        span
        for resource in batch.resource_spans
        for scope in resource.scope_spans
        for span in scope.spans
      )
    elif path.endswith("logs"):
      batch = ExportLogsServiceRequest.FromString(body)
      logs.extend(
        record
        for resource in batch.resource_logs
        for scope in resource.scope_logs
        for record in scope.log_records
      )
    else:
      batch = ExportMetricsServiceRequest.FromString(body)
      metrics.extend(
        metric
        for resource in batch.resource_metrics
        for scope in resource.scope_metrics
        for metric in scope.metrics
      )

  def attrs(span):
    return {item.key: item.value for item in span.attributes}

  chats = {}
  for span in spans:
    if span.name == "ai.chat":
      chats.setdefault(attrs(span)["inkcre.ai.model.id"].int_value, span)
  assert attrs(chats[1])["gen_ai.usage.output_tokens"].int_value == 0
  assert "gen_ai.usage.input_tokens" not in attrs(chats[2])
  assert "gen_ai.usage.input_tokens" not in attrs(chats[3])
  assert attrs(chats[3])["gen_ai.usage.output_tokens"].int_value == 2
  assert attrs(chats[4])["gen_ai.usage.input_tokens"].int_value == 7
  assert attrs(chats[4])["gen_ai.response.time_to_first_chunk"].double_value >= 0
  assert chats[6].status.code == 2 and not chats[6].status.message
  assert all(not span.events for span in spans)
  turn = next(span for span in spans if span.name == "agent.turn")
  step = next(span for span in spans if span.name == "agent.step")
  tools = [
    span for span in spans if span.name == "agent.tool" and span.trace_id == turn.trace_id
  ]
  assert step.parent_span_id == turn.span_id
  assert chats[5].parent_span_id == step.span_id
  assert len(tools) == 2 and all(span.parent_span_id == step.span_id for span in tools)
  assert (
    tools[0].start_time_unix_nano < tools[1].end_time_unix_nano
    and tools[1].start_time_unix_nano < tools[0].end_time_unix_nano
  )
  assert sorted(span.status.code for span in tools) == [0, 2]
  cancelled = [
    span
    for span in spans
    if attrs(span).get("inkcre.agent.outcome")
    and attrs(span)["inkcre.agent.outcome"].string_value == "cancelled"
  ]
  assert {span.name for span in cancelled} == {"agent.turn", "agent.tool"}
  assert all(span.status.code == 2 for span in cancelled)
  tokens = next(metric for metric in metrics if metric.name == "inkcre.ai.token.usage")
  totals = {
    tuple((a.key, a.value.string_value) for a in point.attributes): point.as_int
    for point in tokens.sum.data_points
  }
  chat_input = next(
    value
    for labels, value in totals.items()
    if ("operation", "chat") in labels and ("token.type", "input") in labels
  )
  assert chat_input == 56, (
    totals
  )  # known + streaming + two Agent calls; repeated stream total is not accumulated.
  assert all(
    "model" not in attr.key and "tool" not in attr.key
    for metric in metrics
    for point in metric.sum.data_points
    for attr in point.attributes
  )
  assert [record.body.string_value for record in logs] == [
    "inkcre.retrieval.candidates",
    "inkcre.entity.read",
    "inkcre.entity.read",
    "inkcre.agent.query.result",
  ]

  def ids(record, field):
    return tuple(item.int_value for item in attrs(record)[field].array_value.values)

  assert ids(logs[0], "inkcre.entity.block_ids") == (11, 12)
  assert ids(logs[1], "inkcre.entity.block_ids") == (11,)
  assert ids(logs[2], "inkcre.entity.block_ids") == (11,)
  assert ids(logs[3], "inkcre.entity.block_ids") == ()
  assert ids(logs[3], "inkcre.entity.relation_ids") == (21,)
  assert attrs(logs[3])["inkcre.agent.reference_count"].int_value == 1
  assert all(record.trace_id and record.span_id for record in logs)
  assert len({record.trace_id for record in logs}) == 1
  print(
    json.dumps(
      {
        "status": "passed",
        "provider_http_requests": len(requests),
        "otlp_batches": len(exports),
        "spans": len(spans),
        "source_events": len(logs),
        "metric_names": [metric.name for metric in metrics],
        "checks": [
          "unknown-zero-partial",
          "usage-only-terminal-chunk",
          "stream-total-once",
          "embedding",
          "concurrent-parentage",
          "tool-error-result-preserved",
          "cancellation-propagates",
          "provider-error-content-absent",
          "first-egress-canary-absent",
          "disabled-preserves-third-party-context",
          "candidate-read-final-reference-separation",
        ],
      },
      indent=2,
    )
  )


asyncio.run(main())
