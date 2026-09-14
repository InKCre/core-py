"""One local file of complete named connections; no deployment config ownership."""

import json
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .errors import CommandError


class Connection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: HttpUrl
    jwt_secret: str = Field(min_length=1)


class Connections(BaseModel):
    default: str | None = None
    connections: dict[str, Connection] = Field(default_factory=dict)


def file_path(override: Path | None) -> Path:
    configured = override or os.environ.get("INKCRE_CLI_CONNECTIONS_FILE")
    return (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".inkcre/cli/connections.json"
    )


def load(path: Path) -> Connections:
    return Connections.model_validate_json(path.read_bytes()) if path.exists() else Connections()


def save(path: Path, data: Connections) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Replace one complete file so a reader never observes a partially written JSON document.
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, delete=False, encoding="utf-8"
    ) as out:
        temporary = Path(out.name)
        try:
            json.dump(data.model_dump(mode="json"), out, ensure_ascii=False, separators=(",", ":"))
            out.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def select(data: Connections, name: str | None) -> tuple[str, Connection]:
    selected = name or os.environ.get("INKCRE_CLI_CONNECTION") or data.default
    if selected not in data.connections:
        raise CommandError(
            {
                "connection": selected,
                "available": sorted(data.connections),
                "message": "请选择已保存的连接",
            },
            exit_code=2,
        )
    return selected, data.connections[selected]
