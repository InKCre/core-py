"""Project the server's input schemas without validating or compiling them."""

from copy import deepcopy
from typing import Any

import click

from .http import CoreRESTClient


def request_schema(
    client: CoreRESTClient, path: str, method: str, *, omit: tuple[str, ...] = ()
) -> dict:
    document = client.request("GET", "/openapi.json", authenticated=False)
    try:
        schema = deepcopy(
            document["paths"][path][method.lower()]["requestBody"]["content"]["application/json"][
                "schema"
            ]
        )
    except KeyError as error:
        raise click.ClickException(
            f"当前 Core 未发布 {method.upper()} {path} 的 JSON 输入 schema；确认能力或实例已启用"
        ) from error
    if "$ref" in schema:
        schema = deepcopy(document["components"]["schemas"][schema["$ref"].rsplit("/", 1)[1]])
    for name in omit:
        schema.get("properties", {}).pop(name, None)
    if "required" in schema:
        schema["required"] = [name for name in schema["required"] if name not in omit]
    # Copy only reachable definitions. Keep the original JSON pointers, including recursive ones.
    definitions: dict[str, Any] = {}

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            ref = value.get("$ref", "")
            if ref.startswith("#/components/schemas/"):
                name = ref.rsplit("/", 1)[1]
                if name not in definitions:
                    definitions[name] = deepcopy(document["components"]["schemas"][name])
                    collect(definitions[name])
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(schema)
    if definitions:
        schema["components"] = {"schemas": definitions}
    return schema


def nested(schema: dict, field: str, child: dict) -> dict:
    """Rebase local references when putting an owner schema at its actual input position."""
    prefix = "#/properties/" + field.replace("~", "~0").replace("/", "~1")

    def rebase(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: prefix + item[1:]
                if key == "$ref" and isinstance(item, str) and item.startswith("#")
                else rebase(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [rebase(item) for item in value]
        return value

    result = deepcopy(schema)
    result.setdefault("properties", {})[field] = rebase(child)
    return result


def partial(schema: dict) -> dict:
    result = deepcopy(schema)
    result.pop("required", None)
    return result
