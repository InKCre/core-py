"""Explicit registration entrypoint for core-owned Agent Tool controllers."""


def register_core_agent_tools() -> None:
  """Import every core Tool owner, including Sink delivery controllers.

  Decorators register Tools when their modules load; Python's import cache makes
  repeated bootstrap calls harmless. Entry points must call this explicitly,
  rather than rely on routes or package re-exports importing the owners first.
  """
  from app.business.graph_navigation_retrieval import tools as _graph_tools
  from app.business.info_base import tools as _info_base_tools
  from app.business.info_base.resolver import tools as _resolver_tools
  from app.business.organization import tools as _organization_tools
  from app.business.sink import agent_query as _agent_query

  del _graph_tools, _info_base_tools, _resolver_tools, _organization_tools, _agent_query
