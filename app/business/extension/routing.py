"""FastAPI route publication owned by the extension runtime."""

from dataclasses import dataclass

import fastapi


@dataclass
class ExtensionRouteMount:
  """A retained child router that can be unpublished without rebuilding the app."""

  app: fastapi.FastAPI
  router: fastapi.APIRouter
  published: bool = False

  def publish(self) -> None:
    if self.published:
      raise RuntimeError("extension routes are already published")
    self.app.include_router(self.router)
    self.app.openapi_schema = None
    self.published = True

  def unpublish(self) -> None:
    if not self.published:
      return

    # FastAPI 0.139 keeps included routers as live children. Clearing this retained
    # child removes only routes owned by the extension. The private invalidation call
    # is intentionally localized here and covered by a pinned-version behavior test.
    mark_child_routes_changed = getattr(self.router, "_mark_routes_changed", None)
    mark_app_routes_changed = getattr(self.app.router, "_mark_routes_changed", None)
    if not callable(mark_child_routes_changed) or not callable(mark_app_routes_changed):
      raise RuntimeError("FastAPI route invalidation API changed")
    self.router.routes.clear()
    mark_child_routes_changed()
    mark_app_routes_changed()
    self.app.openapi_schema = None
    self.published = False
