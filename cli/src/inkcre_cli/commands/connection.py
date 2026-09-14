"""Offline connection editing and explicit connectivity observation."""

from typing import Any

import click
import httpx

from .. import connection as store
from ..command import Group, Invocation, common, input_options, load_input
from ..errors import CommandError


@click.group(cls=Group)
def connection():
    """本机命名连接，不是远端 deployment config 或 Peer 注册。"""


@connection.command("list")
@common
@click.pass_obj
def list_connections(inv: Invocation):
    """离线列出名称、地址与保存的默认名。"""
    data = store.load(inv.local_file)
    inv.show(
        {
            "default": data.default,
            "connections": {
                name: {"base_url": str(value.base_url)} for name, value in data.connections.items()
            },
        }
    )


@connection.command()
@click.argument("name")
@common
@click.pass_obj
def get(inv: Invocation, name):
    """离线读取指定连接，包括保存的 JWT secret。"""
    _, value = store.select(store.load(inv.local_file), name)
    inv.show(value.model_dump(mode="json"))


@connection.command("set")
@click.argument("name")
@input_options
@common
@click.pass_obj
def set_connection(inv: Invocation, name, schema, input_file, input_json):
    """创建或完整替换命名连接；输入 base_url 与 jwt_secret。"""
    if schema:
        return inv.show(store.Connection.model_json_schema())
    value = store.Connection.model_validate(load_input(input_file, input_json))
    data = store.load(inv.local_file)
    data.connections[name] = value
    if data.default is None:
        data.default = name
    store.save(inv.local_file, data)
    inv.show({"name": name, "base_url": str(value.base_url), "default": data.default})


@connection.command()
@click.argument("name")
@common
@click.pass_obj
def use(inv: Invocation, name):
    """修改本机默认连接。"""
    data = store.load(inv.local_file)
    store.select(data, name)
    data.default = name
    store.save(inv.local_file, data)
    inv.show({"default": name})


@connection.command()
@click.argument("name")
@common
@click.pass_obj
def delete(inv: Invocation, name):
    """删除本机连接；不操作远端部署。"""
    data = store.load(inv.local_file)
    store.select(data, name)
    del data.connections[name]
    if data.default == name:
        data.default = None
    store.save(inv.local_file, data)
    inv.show(None, no_content=True)


@connection.command()
@common
@click.pass_obj
def check(inv: Invocation):
    """分别检查公共 readyz 与受保护读取，不把就绪误当成认证成功。"""
    result: dict[str, Any] = {"endpoint": inv.client.base_url}
    failed = False
    for key, path, authenticated in (
        ("readyz", "/readyz", False),
        ("authenticated_read", "/peers/self", True),
    ):
        try:
            result[key] = inv.client.request("GET", path, authenticated=authenticated)
        except CommandError as error:
            result[key] = {"error": error.as_dict()}
            failed = True
        except httpx.RequestError as error:
            result[key] = {"error": {"detail": str(error)}}
            failed = True
    inv.show(result, partial_failure=failed)
