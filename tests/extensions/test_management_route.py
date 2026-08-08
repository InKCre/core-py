"""Fixed Extension-management inbound and hard-cut legacy routes."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.business.extension import ExtensionManager
from app.routes.extension import ROUTER
from app.schemas.extension.main import ExtensionModel


def test_fixed_route_calls_non_delegating_extension_path(monkeypatch):
  captured = []

  async def manage_local(_cls, command):
    captured.append(command)
    return ExtensionModel(
      id=command.extension,
      version="1.0.0",
      enabled=[],
      config={},
    )

  monkeypatch.setattr(ExtensionManager, "manage_local", classmethod(manage_local))
  app = FastAPI()
  app.include_router(ROUTER)

  response = TestClient(app).post(
    "/extension-management",
    json={"action": "patch_config", "extension": "rss", "patch": {"limit": 4}},
  )

  assert response.status_code == 200
  assert response.json()["id"] == "rss"
  assert captured[0].action == "patch_config"
  paths = {getattr(route, "path", None) for route in app.routes}
  assert "/extensions/{extid}/enable" not in paths
  assert "/extensions/{extid}/disable" not in paths
  assert "/extensions/{extid}/config" not in paths
