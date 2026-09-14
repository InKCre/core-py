"""Small shared Click options and one invocation's resources."""

import sys
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

import click
from pydantic import BaseModel, TypeAdapter

from . import connection
from .errors import CommandError
from .http import CoreRESTClient
from .output import Output


class Command(click.Command):
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        original = args.copy()
        try:
            return super().parse_args(ctx, args)
        except click.UsageError:
            # Click rejects unknown options before eager callbacks run. Its native
            # tolerant parse can still find presentation options without scanning
            # raw argv (which would mistake an --input-json value for an option).
            with self.make_context(
                ctx.info_name,
                original,
                parent=ctx.parent,
                obj=ctx.obj,
                resilient_parsing=True,
                ignore_unknown_options=True,
            ):
                pass
            raise


class Group(Command, click.Group):
    command_class = Command
    group_class = type


class Entity(BaseModel):
    type: Literal["block", "relation"]
    id: int


def entity(value: str, *, block_only: bool = False) -> Entity:
    kind, separator, identity = value.partition(":")
    if not separator:
        raise click.BadParameter("使用 block:<id> 或 relation:<id>")
    result = Entity.model_validate({"type": kind, "id": identity})
    if block_only and result.type != "block":
        raise click.BadParameter("此操作需要 block:<id>")
    return result


def segment(value: str | int) -> str:
    return quote(str(value), safe="")


def duration(value: str) -> float:
    suffix = value[-1:] if value[-1:].isalpha() else ""
    scale = {"": 1, "s": 1, "m": 60, "h": 3600}
    try:
        result = float(value[:-1] if suffix else value) * scale[suffix]
        if not 0 < result < float("inf"):
            raise ValueError
        return result
    except (ValueError, KeyError) as error:
        raise click.BadParameter("使用正数秒，或 30s / 2m / 1h") from error


class Invocation:
    def __init__(self):
        self.connection_name: str | None = None
        self.connections_file: Path | None = None
        self.output = Output()
        self._client: CoreRESTClient | None = None

    @property
    def local_file(self) -> Path:
        return connection.file_path(self.connections_file)

    @property
    def client(self) -> CoreRESTClient:
        if self._client is None:
            _, selected = connection.select(connection.load(self.local_file), self.connection_name)
            self._client = CoreRESTClient(selected)
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()

    def send(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        body: Any = None,
        strip: tuple[str, ...] = (),
        selectors: dict[str, str] | None = None,
    ) -> Any:
        try:
            return self.client.request(method, path, params=params, body=body)
        except CommandError as error:
            if error.status == 422 and isinstance(error.detail, list):
                detail = []
                for item in error.detail:
                    loc = list(item.get("loc", ()))
                    if loc[:1] == ["body"]:
                        loc = loc[1:]
                        if loc[: len(strip)] == list(strip):
                            loc = loc[len(strip) :]
                        if loc and selectors and loc[0] in selectors:
                            loc[0] = selectors[loc[0]]
                    detail.append({**item, "loc": loc})
                raise CommandError(detail, status=error.status) from error
            raise

    def show(self, value: Any, *, no_content: bool = False, partial_failure: bool = False) -> None:
        self.output.emit(value, no_content=no_content)
        if partial_failure:
            raise CommandError("结果中存在逐项错误；成功项已保留")


def _option(ctx: click.Context, parameter: click.Parameter, value: Any) -> Any:
    invocation = ctx.ensure_object(Invocation)
    if value is not None:
        if parameter.name == "json_mode":
            invocation.output.json_mode = value
        elif parameter.name == "output_dir":
            invocation.output.directory = value
        else:
            setattr(invocation, parameter.name, value)
    return value


def common(function):
    options: list[tuple[tuple[str, ...], dict[str, Any]]] = [
        (("--connection", "connection_name"), {"help": "本次使用的本机连接名"}),
        (("--connections-file",), {"type": click.Path(path_type=Path), "help": "替换连接配置文件"}),
        (
            ("--output-dir",),
            {"type": click.Path(path_type=Path), "help": "保存完整结果，返回入口文件"},
        ),
        (
            ("--json", "json_mode"),
            {"is_flag": True, "default": None, "is_eager": True, "help": "完整紧凑 JSON"},
        ),
    ]
    for args, kwargs in options:
        function = click.option(*args, callback=_option, expose_value=False, **kwargs)(function)
    return function


def input_options(function):
    function = click.option("--schema", is_flag=True, help="只查询输入 JSON Schema，不执行操作")(
        function
    )
    function = click.option("--input-json", help="直接提供 JSON 对象")(function)
    return click.option(
        "--input", "input_file", type=click.Path(path_type=Path), help="JSON 文件，- 表示 stdin"
    )(function)


def paging(function):
    function = click.option("--cursor", help="前一页返回的 next_cursor；保留相同过滤条件")(function)
    return click.option(
        "--limit", type=click.IntRange(min=1), help="本次最多返回多少项；不自动翻页"
    )(function)


def load_input(input_file: Path | None, input_json: str | None) -> dict[str, Any]:
    if input_file is not None and input_json is not None:
        raise click.UsageError("--input 与 --input-json 不能同时使用")
    if input_file is not None:
        text = (
            sys.stdin.read() if str(input_file) == "-" else input_file.read_text(encoding="utf-8")
        )
    elif input_json is not None:
        text = input_json
    else:
        return {}
    return TypeAdapter(dict[str, Any]).validate_json(text)
