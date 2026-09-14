"""Source configuration and collection admission, with catalog-owned schemas."""

import click

from ..command import Group, Invocation, common, input_options, load_input, paging, segment
from ..errors import CommandError
from ..schema import nested, request_schema


@click.group(cls=Group)
def source():
    """管理 Source，或派发 ordinary / backfill collect Job。"""


@source.command()
@click.argument("type_id", required=False)
@paging
@common
@click.pass_obj
def types(inv: Invocation, type_id, limit, cursor):
    """发现 deployment 的 Source type；不等于接入 Peer 都可执行。"""
    inv.show(
        inv.send(
            "GET",
            "/source-types" + ("/" + segment(type_id) if type_id else ""),
            params={"limit": limit, "cursor": cursor},
        )
    )


@source.command("list")
@paging
@common
@click.pass_obj
def list_sources(inv: Invocation, limit, cursor):
    """列出 Source 配置。"""
    inv.show(inv.send("GET", "/sources", params={"limit": limit, "cursor": cursor}))


@source.command()
@click.argument("source_id", type=int)
@common
@click.pass_obj
def get(inv: Invocation, source_id):
    """读取 Source 记录。"""
    inv.show(inv.send("GET", f"/sources/{source_id}"))


@source.command()
@click.option("--type", "type_id", required=True)
@input_options
@common
@click.pass_obj
def create(inv: Invocation, type_id, schema, input_file, input_json):
    """创建 Source；输入为 nickname/storage/config，不包含 type 或数据库字段。"""
    if schema:
        owner = inv.send("GET", "/source-types/" + segment(type_id))
        return inv.show(
            nested(
                request_schema(inv.client, "/sources", "POST", omit=("type",)),
                "config",
                owner["config_schema"],
            )
        )
    inv.show(
        inv.send(
            "POST",
            "/sources",
            body={**load_input(input_file, input_json), "type": type_id},
            selectors={"type": "--type"},
        )
    )


def source_type(inv: Invocation, source_id: int) -> dict:
    record = inv.send("GET", f"/sources/{source_id}")
    return inv.send("GET", "/source-types/" + segment(record["type"]))


@source.command()
@click.argument("source_id", type=int)
@input_options
@common
@click.pass_obj
def update(inv: Invocation, source_id, schema, input_file, input_json):
    """只改提交的字段；提供 config 时完整替换该 config。"""
    if schema:
        return inv.show(
            nested(
                request_schema(inv.client, "/sources/{source_id}", "PATCH"),
                "config",
                source_type(inv, source_id)["config_schema"],
            )
        )
    inv.show(inv.send("PATCH", f"/sources/{source_id}", body=load_input(input_file, input_json)))


@source.command()
@click.argument("source_id", type=int)
@common
@click.pass_obj
def delete(inv: Invocation, source_id):
    """删除 Source 配置；已收集的图不随之删除。"""
    inv.show(inv.send("DELETE", f"/sources/{source_id}"), no_content=True)


@source.command()
@click.argument("source_id", type=int)
@click.option("--timeout-seconds", type=click.IntRange(min=1))
@input_options
@common
@click.pass_obj
def collect(inv: Invocation, source_id, timeout_seconds, schema, input_file, input_json):
    """派发普通收集 Job；JSON 是该 Source 的 collect config。"""
    if schema:
        return inv.show(source_type(inv, source_id)["collect_config_schema"])
    inv.show(
        inv.send(
            "POST",
            f"/sources/{source_id}/collect",
            params={"timeout_seconds": timeout_seconds},
            body=load_input(input_file, input_json),
        )
    )


@source.command()
@click.argument("source_id", type=int)
@click.option("--timeout-seconds", type=click.IntRange(min=1))
@input_options
@common
@click.pass_obj
def backfill(inv: Invocation, source_id, timeout_seconds, schema, input_file, input_json):
    """派发指定历史边界的收集 Job；不改变 ordinary collect 范围。"""
    if schema:
        contract = source_type(inv, source_id)["backfill_config_schema"]
        if contract is None:
            raise CommandError("此 Source type 不支持 backfill")
        return inv.show(contract)
    inv.show(
        inv.send(
            "POST",
            f"/sources/{source_id}/backfill",
            params={"timeout_seconds": timeout_seconds},
            body=load_input(input_file, input_json),
        )
    )
