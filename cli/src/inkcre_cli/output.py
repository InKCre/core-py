"""Bounded presentation and complete local content delivery from the same response."""

import json
import tempfile
from pathlib import Path
from typing import Any

import click

from .errors import CommandError


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def has_bytes(value: Any) -> bool:
    if isinstance(value, bytes):
        return True
    if isinstance(value, dict):
        return any(has_bytes(item) for item in value.values())
    if isinstance(value, list):
        return any(has_bytes(item) for item in value)
    return False


def preview_binary(value: Any) -> Any:
    if isinstance(value, bytes):
        return f"<{len(value)} bytes; 完整内容见导出文件>"
    raise TypeError(f"Cannot present {type(value).__name__}")


class Output:
    def __init__(self, json_mode: bool = False, directory: Path | None = None):
        self.json_mode = json_mode
        self.directory = directory

    def _save(self, value: Any, *, entry: bool) -> Any:
        if self.directory:
            self.directory.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(prefix="inkcre-", dir=self.directory)).resolve()
        number = 0

        def convert(item: Any) -> Any:
            nonlocal number
            if isinstance(item, bytes):
                number += 1
                path = directory / f"{number:03}.bin"
                path.write_bytes(item)
                return {"file": path.name if entry else str(path)}
            if isinstance(item, dict):
                return {key: convert(child) for key, child in item.items()}
            if isinstance(item, list):
                return [convert(child) for child in item]
            return item

        try:
            if not entry:
                return convert(value)
            if isinstance(value, bytes):
                path = directory / "result.bin"
                path.write_bytes(value)
            elif isinstance(value, str):
                path = directory / "result.txt"
                path.write_text(value, encoding="utf-8")
            else:
                path = directory / "result.json"
                path.write_text(compact(convert(value)), encoding="utf-8")
            return {"file": str(path)}
        except OSError as error:
            raise CommandError({"message": str(error), "directory": str(directory)}) from error

    def emit(self, value: Any, *, no_content: bool = False) -> None:
        if self.directory:
            value = self._save(value, entry=True)
        elif not self.json_mode:
            # The preview is deliberately a presentation budget, not a business result limit.
            preview = value if isinstance(value, str) else None
            if preview is None:
                preview = json.dumps(value, ensure_ascii=False, indent=2, default=preview_binary)
            if preview is not None and len(preview) > 8000:
                receipt = self._save(value, entry=True)
                click.echo(preview[:2000] + "\n…\n完整结果: " + receipt["file"])
                return
        if has_bytes(value):
            value = self._save(value, entry=False)
        if self.json_mode:
            click.echo(compact(value))
        elif not no_content:
            click.echo(
                value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
            )
