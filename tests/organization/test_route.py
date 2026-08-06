"""Fixed explicit organization rumination inbound."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.business.organization import OrganizationManager
from app.routes.organization import ROUTER


def test_route_calls_non_delegating_local_path_and_returns_204(monkeypatch):
  captured = []

  async def ruminate_local(_cls, block_id):
    captured.append(block_id)

  monkeypatch.setattr(
    OrganizationManager,
    "ruminate_local",
    classmethod(ruminate_local),
  )
  app = FastAPI()
  app.include_router(ROUTER)

  response = TestClient(app).post(
    "/organization/ruminate",
    json={"block": 42},
  )

  assert response.status_code == 204
  assert response.content == b""
  assert captured == [42]
