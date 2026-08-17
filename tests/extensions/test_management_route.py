"""Fixed Extension-management inbound over the canonical Host."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.business.extension import EXTENSION_HOST, InstalledExtension
from app.routes.extension import ROUTER


def test_fixed_route_calls_non_delegating_extension_path(monkeypatch):
  captured = []

  async def manage_local(command):
    captured.append(command)
    return InstalledExtension(
      name=command.extension,
      version="1.0.0",
      enabled=[],
      config={},
      state={"access_token": "must-not-leave-core"},
    )

  monkeypatch.setattr(EXTENSION_HOST, "manage_local", manage_local)
  app = FastAPI()
  app.include_router(ROUTER)

  response = TestClient(app).post(
    "/extension-management",
    json={
      "action": "patch_config",
      "extension": "inkcre/rss",
      "patch": {"limit": 4},
    },
  )

  assert response.status_code == 200
  assert response.json()["name"] == "inkcre/rss"
  assert "state" not in response.json()
  assert captured[0].action == "patch_config"
