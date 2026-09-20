"""Explicit registration entrypoint for core-owned Agent Tool controllers."""


def register_core_agent_tools() -> None:
  """Load each owning domain's core Tool controllers into AgentManager."""
  from app.business.graph_navigation_retrieval import tools as _graph_tools
  from app.business.info_base import tools as _info_base_tools
  from app.business.info_base.resolver import tools as _resolver_tools
  from app.business.organization import tools as _organization_tools

  del _graph_tools, _info_base_tools, _resolver_tools, _organization_tools
