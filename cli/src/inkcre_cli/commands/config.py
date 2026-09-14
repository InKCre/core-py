"""Deployment config values and their runtime-owned input schemas."""

import click

from ..command import Group, Invocation, common, input_options, load_input, paging, segment
from ..schema import partial


@click.group(cls=Group)
def config():
    """远端 deployment 配置，与本机 connection 文件分开。"""


@config.command("list")
@paging
@common
@click.pass_obj
def list_configs(inv: Invocation, limit, cursor):
    """列出保存的 deployment config，不要求 schema 已加载。"""
    inv.show(inv.send("GET", "/configs", params={"limit": limit, "cursor": cursor}))


@config.command()
@click.argument("key")
@common
@click.pass_obj
def get(inv: Invocation, key):
    """读取配置的实际 schema/value。"""
    inv.show(inv.send("GET", "/configs/" + segment(key)))


@config.command()
@click.argument("schema_id", required=False)
@paging
@common
@click.pass_obj
def schemas(inv: Invocation, schema_id, limit, cursor):
    """发现接入 Peer 已加载的 schema；给出 ID 时读取输入合同。"""
    inv.show(
        inv.send(
            "GET",
            "/config-schemas" + ("/" + segment(schema_id) if schema_id else ""),
            params={"limit": limit, "cursor": cursor},
        )
    )


@config.command()
@click.argument("key")
@click.option("--schema-id", required=True)
@input_options
@common
@click.pass_obj
def replace(inv: Invocation, key, schema_id, schema, input_file, input_json):
    """创建或完整替换；JSON 是 value 本身，不再包装 value。"""
    if schema:
        return inv.show(inv.send("GET", "/config-schemas/" + segment(schema_id))["input_schema"])
    inv.show(
        inv.send(
            "PUT",
            "/configs/" + segment(key),
            body={
                "schema": schema_id,
                "value": load_input(input_file, input_json),
            },
            strip=("value",),
            selectors={"schema": "--schema-id"},
        )
    )


@config.command()
@click.argument("key")
@input_options
@common
@click.pass_obj
def update(inv: Invocation, key, schema, input_file, input_json):
    """更新 value 的提交字段；嵌套值按 owner 合同处理。"""
    if schema:
        existing = inv.send("GET", "/configs/" + segment(key))
        return inv.show(
            partial(
                inv.send("GET", "/config-schemas/" + segment(existing["schema"]))["input_schema"]
            )
        )
    inv.show(inv.send("PATCH", "/configs/" + segment(key), body=load_input(input_file, input_json)))


@config.command()
@click.argument("key")
@common
@click.pass_obj
def delete(inv: Invocation, key):
    """删除保存的配置值。"""
    inv.show(inv.send("DELETE", "/configs/" + segment(key)), no_content=True)
