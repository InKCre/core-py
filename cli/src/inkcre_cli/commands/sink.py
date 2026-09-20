"""Sink instance management and Agent Query admission."""

import click

from ..command import Group, Invocation, common, input_options, load_input, segment
from ..schema import nested, request_schema


@click.group(cls=Group)
def sink():
    """管理 deployment Sink type 与当前 Peer 上的实例生命周期。"""


@sink.command()
@common
@click.pass_obj
def types(inv: Invocation):
    """列出当前 Core 注册的 Sink type。"""
    inv.show(inv.send("GET", "/sink-types"))


@sink.command("list")
@common
@click.pass_obj
def list_sinks(inv: Invocation):
    """列出 deployment 的 Sink 实例。"""
    inv.show(inv.send("GET", "/sinks"))


@sink.command()
@click.argument("sink_id", type=int)
@common
@click.pass_obj
def get(inv: Invocation, sink_id):
    """读取一个 Sink 实例。"""
    inv.show(inv.send("GET", f"/sinks/{sink_id}"))


@sink.command()
@click.option("--type", "type_id", required=True)
@input_options
@common
@click.pass_obj
def create(inv: Invocation, type_id, schema, input_file, input_json):
    """创建 Sink；JSON 包含 nickname 与该 type 的 config。"""
    if schema:
        owner = inv.send("GET", "/sink-types/" + segment(type_id))
        return inv.show(
            nested(
                request_schema(inv.client, "/sinks", "POST", omit=("type",)),
                "config",
                owner["config_schema"],
            )
        )
    inv.show(
        inv.send(
            "POST",
            "/sinks",
            body={**load_input(input_file, input_json), "type": type_id},
            selectors={"type": "--type"},
        )
    )


@click.group(cls=Group)
def config():
    """读取或完整替换一个 Sink 的 config。"""


@config.command("get")
@click.argument("sink_id", type=int)
@common
@click.pass_obj
def get_config(inv: Invocation, sink_id):
    """读取当前 config。"""
    inv.show(inv.send("GET", f"/sinks/{sink_id}")["config"])


@config.command("replace")
@click.argument("sink_id", type=int)
@input_options
@common
@click.pass_obj
def replace_config(inv: Invocation, sink_id, schema, input_file, input_json):
    """按 Sink type 合同完整替换 config。"""
    if schema:
        record = inv.send("GET", f"/sinks/{sink_id}")
        owner = inv.send("GET", "/sink-types/" + segment(record["type"]))
        return inv.show(owner["config_schema"])
    inv.show(
        inv.send(
            "PUT",
            f"/sinks/{sink_id}/config",
            body=load_input(input_file, input_json),
        )
    )


sink.add_command(config)


@sink.command()
@click.argument("sink_id", type=int)
@common
@click.pass_obj
def enable(inv: Invocation, sink_id):
    """在当前连接的 Peer 上启用实例。"""
    inv.show(inv.send("POST", f"/sinks/{sink_id}/enable"))


@sink.command()
@click.argument("sink_id", type=int)
@common
@click.pass_obj
def disable(inv: Invocation, sink_id):
    """在当前连接的 Peer 上禁用实例，不取消已领取 Job。"""
    inv.show(inv.send("POST", f"/sinks/{sink_id}/disable"))


@sink.command()
@click.argument("sink_id", type=int)
@common
@click.pass_obj
def delete(inv: Invocation, sink_id):
    """删除已禁用的 Sink 实例。"""
    inv.show(inv.send("DELETE", f"/sinks/{sink_id}"), no_content=True)


@click.command()
@click.argument("question", required=False)
@click.option("--sink", "sink_id", required=True, type=int)
@click.option("--timeout-seconds", type=click.IntRange(min=1))
@click.option("--schema", is_flag=True, help="只查询当前启用实例的输入合同")
@common
@click.pass_obj
def query(inv: Invocation, question, sink_id, timeout_seconds, schema):
    """通过一个已启用的 Agent Query Sink 创建 Job。"""
    route = f"/sinks/{sink_id}/query"
    if schema:
        return inv.show(request_schema(inv.client, route, "POST"))
    if question is None:
        raise click.UsageError("QUESTION 是必需的；或使用 --schema")
    inv.show(
        inv.send(
            "POST",
            route,
            body={"query": question, "timeout_seconds": timeout_seconds},
            selectors={"query": "QUESTION", "timeout_seconds": "--timeout-seconds"},
        )
    )
