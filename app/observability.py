"""Runtime projection of optional deployment telemetry and context boundaries."""

import asyncio
from collections.abc import Mapping

from opentelemetry.context import Context
from opentelemetry.trace import Link, SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry import trace
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.business.deployment_config import DeploymentConfigManager, DeploymentConfigService
from app.settings import settings
from app.schemas.observability import CONFIG_KEY, CONFIG_SCHEMA, ObservabilityConfig
from app.version import APPLICATION_VERSION
from libs.obsrv.main import get_logger
from libs.obsrv.telemetry import emit_event, is_enabled, operation, start_telemetry


PROPAGATOR = TraceContextTextMapPropagator()


DeploymentConfigManager.register_schema(
  CONFIG_SCHEMA, ObservabilityConfig, keys=(CONFIG_KEY,)
)


async def initialize_telemetry() -> None:
  """Read once after database admission; telemetry cannot fail business readiness."""
  if not settings.obsrv.telemetry_enabled:
    return
  attributes: dict[str, str] = {"inkcre.peer.id": str(settings.peer_id)}
  endpoints: dict[str, str] = {}
  try:
    async with asyncio.timeout(2):
      config = await DeploymentConfigService.get(CONFIG_KEY)
    if not isinstance(config, ObservabilityConfig):
      raise ValueError("missing or unexpected observability schema")
    attributes["inkcre.deployment.id"] = str(config.deployment_id)
    if config.otlp_http_endpoints is not None:
      endpoints = config.otlp_http_endpoints.model_dump(mode="json", exclude_none=True)
  except Exception as error:
    # Configuration may contain credentials despite the admitted schema. Never render it.
    get_logger().warning("Telemetry configuration unavailable (%s)", type(error).__name__)
    return
  try:
    start_telemetry(
      enabled=True,
      service_version=APPLICATION_VERSION,
      resource_attributes=attributes,
      endpoints=endpoints,
    )
  except Exception as error:
    get_logger().warning("Telemetry initialization failed (%s)", type(error).__name__)


def inject_context() -> dict[str, str]:
  """Inject only standard Trace Context when this runtime explicitly enabled telemetry."""
  carrier: dict[str, str] = {}
  if is_enabled():
    PROPAGATOR.inject(carrier)
  return carrier


def submission_context() -> dict[str, str | None]:
  carrier = inject_context()
  state = carrier.get("tracestate")
  if state is not None and len(state.encode("utf-8")) > 512:
    state = None
    emit_event("telemetry.carrier.dropped", {"reason": "tracestate_capacity"})
  return {
    "submission_traceparent": carrier.get("traceparent"),
    "submission_tracestate": state,
  }


def extract_context(carrier: Mapping[str, str]) -> Context:
  """Use the SDK parser within the application's bounded, two-header carrier."""
  if not is_enabled():
    return Context()
  bounded = {
    key: value
    for key in ("traceparent", "tracestate")
    if (value := carrier.get(key)) is not None and len(value.encode("utf-8")) <= 512
  }
  return PROPAGATOR.extract(bounded, context=Context())


def submission_links(parent: str | None, state: str | None) -> tuple[Link, ...]:
  carrier = {}
  if parent is not None:
    carrier["traceparent"] = parent
  if state is not None:
    carrier["tracestate"] = state
  context = trace.get_current_span(extract_context(carrier)).get_span_context()
  return (Link(context),) if context.is_valid else ()


class TelemetryMiddleware:
  """Observe complete HTTP responses without recording paths, headers or bodies."""

  def __init__(self, app: ASGIApp):
    self.app = app

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] != "http" or not is_enabled():
      await self.app(scope, receive, send)
      return
    carrier = {
      key.decode("ascii"): value.decode("latin-1")
      for key, value in scope.get("headers", ())
      if key in {b"traceparent", b"tracestate"}
    }
    method = scope.get("method", "")
    if method not in {
      "GET",
      "POST",
      "PUT",
      "PATCH",
      "DELETE",
      "HEAD",
      "OPTIONS",
      "CONNECT",
      "TRACE",
    }:
      method = "_OTHER"
    with operation(
      "http.server",
      attributes={"http.request.method": method},
      context=extract_context(carrier),
      kind=SpanKind.SERVER,
    ) as observation:
      span = observation.span

      async def observed_send(message: Message) -> None:
        if message["type"] == "http.response.start":
          span.set_attribute("http.response.status_code", message["status"])
          route = scope.get("route")
          if route is not None and isinstance(getattr(route, "path", None), str):
            span.set_attribute("http.route", route.path)
          if message["status"] >= 500:
            observation.outcome = "error"
        await send(message)

      await self.app(scope, receive, observed_send)
