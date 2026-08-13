"""Render + Neon self-host delivery keeps provider mechanics behind one boundary."""

from __future__ import annotations

import httpx
import pytest

from scripts.deploy_render_neon import (
  RenderAPIError,
  RenderClient,
  RenderService,
  RenderServiceSpec,
  _deploy_exact_commit,
  _role_password,
  _validate_inputs,
)


COMMIT = "a" * 40


def _service_document(
  *,
  service_id: str = "srv-core",
  name: str = "selfhost-core",
  url: str = "https://selfhost-core.onrender.com",
) -> dict[str, object]:
  return {
    "id": service_id,
    "name": name,
    "serviceDetails": {
      "url": url,
      "runtime": "docker",
      "plan": "free",
      "region": "singapore",
    },
  }


def test_service_spec_separates_protocol_parameters_and_disables_autodeploy():
  spec = RenderServiceSpec(
    name="selfhost-core",
    repository="https://github.com/example/inkcre-core",
    branch="main",
    dockerfile="./Dockerfile",
    environment={"JWT_SECRET": "private"},
    health_check_path="/readyz",
  )

  document = spec.creation_document("tea-owner")

  assert document["autoDeploy"] == "no"
  assert document["serviceDetails"] == {
    "runtime": "docker",
    "plan": "free",
    "region": "singapore",
    "envSpecificDetails": {
      "dockerContext": ".",
      "dockerfilePath": "./Dockerfile",
    },
    "healthCheckPath": "/readyz",
  }
  assert document["envVars"] == [{"key": "JWT_SECRET", "value": "private"}]


def test_existing_service_is_updated_without_replacing_unowned_environment():
  calls: list[tuple[str, str, object]] = []

  def handler(request: httpx.Request) -> httpx.Response:
    document = request.read().decode() if request.content else None
    calls.append((request.method, request.url.path, document))
    if request.method == "PATCH":
      return httpx.Response(200, json=_service_document())
    if request.method == "GET":
      return httpx.Response(
        200,
        json=[
          {
            "envVar": {"key": "OWNER_NOTE", "value": "keep-me"},
            "cursor": "cursor",
          }
        ],
      )
    if request.method == "PUT":
      return httpx.Response(200, json=[])
    raise AssertionError(f"unexpected request: {request.method} {request.url.path}")

  service = RenderService.from_document(_service_document())
  spec = RenderServiceSpec(
    name="selfhost-core",
    repository="https://github.com/example/inkcre-core",
    branch="main",
    dockerfile="./Dockerfile",
    environment={"DATABASE_URL": "secret", "JWT_SECRET": "secret"},
    health_check_path="/readyz",
  )
  with RenderClient("render-key", transport=httpx.MockTransport(handler)) as client:
    updated = client.update_service(service, spec)

  assert updated.id == service.id
  assert [call[:2] for call in calls] == [
    ("PATCH", "/v1/services/srv-core"),
    ("GET", "/v1/services/srv-core/env-vars"),
    ("PUT", "/v1/services/srv-core/env-vars"),
  ]
  assert calls[-1][2] == (
    '[{"key":"DATABASE_URL","value":"secret"},'
    '{"key":"JWT_SECRET","value":"secret"},'
    '{"key":"OWNER_NOTE","value":"keep-me"}]'
  )


def test_environment_recovery_reads_every_provider_page():
  calls: list[str | None] = []

  def handler(request: httpx.Request) -> httpx.Response:
    cursor = request.url.params.get("cursor")
    calls.append(cursor)
    if cursor is None:
      return httpx.Response(
        200,
        json=[
          {
            "envVar": {"key": f"OWNER_{index}", "value": str(index)},
            "cursor": f"cursor-{index}",
          }
          for index in range(100)
        ],
      )
    assert cursor == "cursor-99"
    return httpx.Response(
      200,
      json=[
        {
          "envVar": {"key": "DATABASE_URL", "value": "secret"},
          "cursor": "cursor-100",
        }
      ],
    )

  with RenderClient("render-key", transport=httpx.MockTransport(handler)) as client:
    environment = client.get_environment("srv-core")

  assert calls == [None, "cursor-99"]
  assert len(environment) == 101
  assert environment["OWNER_0"] == "0"
  assert environment["DATABASE_URL"] == "secret"


def test_existing_role_password_is_recovered_from_render_environment():
  key_material = "slash/colon:at@percent%-database-password"

  def handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/v1/services/srv-core/env-vars"
    return httpx.Response(
      200,
      json=[
        {
          "envVar": {
            "key": "DATABASE_URL",
            "value": (
              "postgresql+psycopg://inkcre_core:"
              "slash%2Fcolon%3Aat%40percent%25-database-password"
              "@db.example.test/inkcre?sslmode=require"
            ),
          },
          "cursor": "cursor",
        },
        {
          "envVar": {
            "key": "INKCRE_DEPLOYMENT_PROFILE",
            "value": "core-py.render-neon.v1",
          },
          "cursor": "cursor-2",
        },
      ],
    )

  service = RenderService.from_document(_service_document())
  with RenderClient("render-key", transport=httpx.MockTransport(handler)) as client:
    recovered = _role_password(
      client,
      service,
      environment_key="DATABASE_URL",
      expected_role="inkcre_core",
      expected_source_url=(
        "postgresql://neondb_owner:owner@db.example.test/inkcre?sslmode=require"
      ),
    )

  assert recovered == key_material


def test_existing_service_without_role_url_refuses_silent_rotation():
  def handler(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
      200,
      json=[
        {
          "envVar": {
            "key": "INKCRE_DEPLOYMENT_PROFILE",
            "value": "core-py.render-neon.v1",
          },
          "cursor": "cursor",
        }
      ],
    )

  service = RenderService.from_document(_service_document())
  with RenderClient("render-key", transport=httpx.MockTransport(handler)) as client:
    with pytest.raises(RenderAPIError, match="refusing silent credential rotation"):
      _role_password(
        client,
        service,
        environment_key="DATABASE_URL",
        expected_role="inkcre_core",
        expected_source_url="postgresql://owner@db.example.test/inkcre",
      )


def test_existing_unowned_service_name_collision_is_not_adopted():
  def handler(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
      200,
      json=[
        {
          "envVar": {
            "key": "DATABASE_URL",
            "value": (
              "postgresql://inkcre_core:"
              "database-password-at-least-thirty-two-bytes"
              "@db.example.test/inkcre"
            ),
          },
          "cursor": "cursor",
        }
      ],
    )

  service = RenderService.from_document(_service_document())
  with RenderClient("render-key", transport=httpx.MockTransport(handler)) as client:
    with pytest.raises(RenderAPIError, match="not owned by this deployment profile"):
      _role_password(
        client,
        service,
        environment_key="DATABASE_URL",
        expected_role="inkcre_core",
        expected_source_url="postgresql://owner@db.example.test/inkcre",
      )


def test_existing_service_refuses_silent_database_rebind():
  def handler(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
      200,
      json=[
        {
          "envVar": {
            "key": "DATABASE_URL",
            "value": (
              "postgresql://inkcre_core:"
              "database-password-at-least-thirty-two-bytes"
              "@old.example.test/inkcre"
            ),
          },
          "cursor": "cursor",
        },
        {
          "envVar": {
            "key": "INKCRE_DEPLOYMENT_PROFILE",
            "value": "core-py.render-neon.v1",
          },
          "cursor": "cursor-2",
        },
      ],
    )

  service = RenderService.from_document(_service_document())
  with RenderClient("render-key", transport=httpx.MockTransport(handler)) as client:
    with pytest.raises(RenderAPIError, match="refusing silent database rebind"):
      _role_password(
        client,
        service,
        environment_key="DATABASE_URL",
        expected_role="inkcre_core",
        expected_source_url="postgresql://owner@new.example.test/inkcre",
      )


def test_initial_non_exact_deploy_is_followed_by_exact_commit():
  calls: list[tuple[str, str]] = []

  def handler(request: httpx.Request) -> httpx.Response:
    calls.append((request.method, request.url.path))
    if request.method == "GET" and request.url.path.endswith("/dep-initial"):
      return httpx.Response(
        200,
        json={"id": "dep-initial", "status": "live", "commit": {"id": "b" * 40}},
      )
    if request.method == "POST":
      assert request.read().decode().find(COMMIT) >= 0
      return httpx.Response(
        201,
        json={"id": "dep-exact", "status": "created"},
      )
    if request.method == "GET" and request.url.path.endswith("/dep-exact"):
      return httpx.Response(
        200,
        json={"id": "dep-exact", "status": "live", "commit": {"id": COMMIT}},
      )
    raise AssertionError(f"unexpected request: {request.method} {request.url.path}")

  service = RenderService.from_document(_service_document())
  with RenderClient("render-key", transport=httpx.MockTransport(handler)) as client:
    _deploy_exact_commit(
      client,
      service,
      "dep-initial",
      COMMIT,
      wait_seconds=1,
    )

  assert calls == [
    ("GET", "/v1/services/srv-core/deploys/dep-initial"),
    ("POST", "/v1/services/srv-core/deploys"),
    ("GET", "/v1/services/srv-core/deploys/dep-exact"),
  ]


@pytest.mark.parametrize(
  ("prefix", "commit", "jwt_secret"),
  [
    ("UPPER", COMMIT, "x" * 32),
    ("a", COMMIT, "x" * 32),
    ("valid-prefix", "short", "x" * 32),
    ("valid-prefix", COMMIT, "short"),
  ],
)
def test_deployment_inputs_fail_before_provider_mutation(prefix, commit, jwt_secret):
  with pytest.raises(ValueError):
    _validate_inputs(
      service_prefix=prefix,
      commit=commit,
      jwt_secret=jwt_secret,
      wait_seconds=1,
    )
