"""Extension Host REST management; no CLI-specific Extension adapters."""

import click

from ..command import Group, Invocation, common, input_options, load_input, paging, segment
from ..errors import CommandError
from ..schema import partial


def route(coordinate: str) -> str:
    namespace, separator, name = coordinate.partition("/")
    if not separator or not namespace or not name or "/" in name:
        raise click.BadParameter("Extension 使用 namespace/name coordinate")
    return "/extensions/" + segment(namespace) + "/" + segment(name)


@click.group(cls=Group)
def extension():
    """安装、配置和启停 Extension；发布仍由 Extension 的交付流程负责。"""


@extension.command("list")
@paging
@common
@click.pass_obj
def list_extensions(inv: Invocation, limit, cursor):
    """列出 Extension 的安装、启用意图与运行状态。"""
    inv.show(inv.send("GET", "/extensions", params={"limit": limit, "cursor": cursor}))


@extension.command()
@click.argument("coordinate")
@common
@click.pass_obj
def get(inv: Invocation, coordinate):
    """读取一个已安装 Extension。"""
    inv.show(inv.send("GET", route(coordinate)))


@extension.command()
@click.argument("coordinate")
@click.option("--version", required=True, help="准确的已发布版本，不解析 latest")
@common
@click.pass_obj
def install(inv: Invocation, coordinate, version):
    """安装准确版本；不隐式启用。"""
    inv.show(inv.send("POST", route(coordinate), params={"version": version}))


@extension.command()
@click.argument("coordinate")
@common
@click.pass_obj
def uninstall(inv: Invocation, coordinate):
    """卸载 Extension。"""
    inv.show(inv.send("DELETE", route(coordinate)), no_content=True)


@extension.command()
@click.argument("coordinate")
@click.option("--peer", help="启用意图的目标 Peer；省略时为接入 Peer")
@common
@click.pass_obj
def enable(inv: Invocation, coordinate, peer):
    """在指定或当前 Peer 启用 Extension。"""
    inv.show(inv.send("POST", route(coordinate) + "/enable", params={"route_to_peer": peer}))


@extension.command()
@click.argument("coordinate")
@click.option("--peer", help="禁用意图的目标 Peer；省略时为接入 Peer")
@common
@click.pass_obj
def disable(inv: Invocation, coordinate, peer):
    """在指定或当前 Peer 禁用 Extension。"""
    inv.show(inv.send("POST", route(coordinate) + "/disable", params={"route_to_peer": peer}))


@extension.group()
def config():
    """读写 Extension 的持久配置，不要求先启用。"""


@config.command("get")
@click.argument("coordinate")
@common
@click.pass_obj
def get_config(inv: Invocation, coordinate):
    """从安装记录读取 config；不调用业务 schema 验证。"""
    inv.show(inv.send("GET", route(coordinate))["config"])


def config_schema(inv: Invocation, coordinate: str) -> dict:
    contract = inv.send("GET", route(coordinate))["config_schema"]
    if contract is None:
        raise CommandError("该 Extension 尚未发布配置 schema；可在启用后重新发现")
    return contract


@config.command("replace")
@click.argument("coordinate")
@input_options
@common
@click.pass_obj
def replace_config(inv: Invocation, coordinate, schema, input_file, input_json):
    """完整替换 Extension config。"""
    if schema:
        return inv.show(config_schema(inv, coordinate))
    inv.show(
        inv.send("PUT", route(coordinate) + "/config", body=load_input(input_file, input_json))
    )


@config.command("update")
@click.argument("coordinate")
@input_options
@common
@click.pass_obj
def update_config(inv: Invocation, coordinate, schema, input_file, input_json):
    """更新提交的 config 字段。"""
    if schema:
        return inv.show(partial(config_schema(inv, coordinate)))
    inv.show(
        inv.send("PATCH", route(coordinate) + "/config", body=load_input(input_file, input_json))
    )
