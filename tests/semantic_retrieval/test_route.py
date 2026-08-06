"""Fixed local semantic-retrieval inbound codec."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.business.semantic_retrieval import SemanticRetrievalManager
from app.routes.semantic_retrieval import ROUTER
from app.schemas.semantic_retrieval import SemanticRetrievalResult


def test_route_calls_the_non_delegating_local_path(monkeypatch):
  captured = {}

  async def retrieve_local(_cls, query, profile, options):
    captured.update(query=query, profile=profile, options=options)
    return SemanticRetrievalResult(profile=profile, matches=())

  monkeypatch.setattr(
    SemanticRetrievalManager,
    "retrieve_local",
    classmethod(retrieve_local),
  )
  app = FastAPI()
  app.include_router(ROUTER)

  response = TestClient(app).post(
    "/semantic-retrieval",
    json={
      "query": "direct local request",
      "profile": 7,
      "options": {"limit": 3, "entity_types": ["block"]},
    },
  )

  assert response.status_code == 200
  assert response.json() == {"profile": 7, "metric": "cosine", "matches": []}
  assert captured["query"] == "direct local request"
  assert captured["profile"] == 7
  assert captured["options"].limit == 3
  assert captured["options"].entity_types == {"block"}
