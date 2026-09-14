"""Information retrieval, record writes and dynamic Resolver calls."""

import click
import httpx

from ..command import (
    Command,
    Group,
    Invocation,
    common,
    entity,
    input_options,
    load_input,
    paging,
    segment,
)
from ..errors import CommandError
from ..schema import request_schema


@click.command("get", cls=Command)
@click.argument("references", nargs=-1)
@click.option(
    "--content", type=click.Choice(["none", "raw", "hydrated"]), default="raw", show_default=True
)
@common
@click.pass_obj
def get(inv: Invocation, references, content):
    """批量取得 info-base Block / Relation 记录；引用为 block:42 / relation:8。"""
    result = inv.send(
        "POST",
        "/entities/get",
        body={
            "entities": [entity(ref).model_dump() for ref in references],
            "content": content,
        },
    )
    inv.show(result, partial_failure=any("error" in item for item in result))


@click.command("update", cls=Command)
@click.argument("reference")
@input_options
@common
@click.pass_obj
def update(inv: Invocation, reference, schema, input_file, input_json):
    """原地修改一个 info-base 实体；省略字段保持不变。"""
    ref = entity(reference)
    if schema:
        return inv.show(request_schema(inv.client, f"/{ref.type}s/{{{ref.type}_id}}", "PATCH"))
    inv.show(inv.send("PATCH", f"/{ref.type}s/{ref.id}", body=load_input(input_file, input_json)))


@click.command("delete", cls=Command)
@click.argument("reference")
@common
@click.pass_obj
def delete(inv: Invocation, reference):
    """删除明确的 info-base Block / Relation；不是删除 Source 或其它管理对象。"""
    ref = entity(reference)
    inv.show(inv.send("DELETE", f"/{ref.type}s/{ref.id}"), no_content=True)


@click.command(cls=Command)
@click.argument("query")
@click.option("--mode", multiple=True, required=True, type=click.Choice(["lexical", "semantic"]))
@click.option("--limit", type=click.IntRange(min=1))
@click.option("--profile", type=int, help="Semantic embedding profile ID")
@click.option("--min-score", type=float)
@click.option("--entity-type", multiple=True, type=click.Choice(["block", "relation"]))
@click.option("--peer", help="明确的检索执行 Peer；不改变本机接入连接")
@common
@click.pass_obj
def recall(inv: Invocation, query, mode, limit, profile, min_score, entity_type, peer):
    """显式选择检索模式；每个模式独立返回，不合并排名或自动重试。"""
    if "semantic" not in mode and (profile is not None or min_score is not None or entity_type):
        raise click.UsageError("--profile / --min-score / --entity-type 需要 --mode semantic")
    _ = inv.client  # Resolve the shared connection before entering the independent-mode batch.
    results = []
    for selected in dict.fromkeys(mode):
        body = {"query": query}
        if selected == "semantic":
            options = {
                key: value
                for key, value in {
                    "limit": limit,
                    "min_score": min_score,
                    "entity_types": entity_type or None,
                }.items()
                if value is not None
            }
            body.update({"profile": profile, "options": options})
        elif limit is not None:
            body["limit"] = limit
        try:
            result = inv.send(
                "POST", f"/retrieval/{selected}", params={"route_to_peer": peer}, body=body
            )
            results.append({"mode": selected, **result})
        except CommandError as error:
            results.append({"mode": selected, "error": error.as_dict()})
        except httpx.RequestError as error:
            results.append({"mode": selected, "error": {"detail": str(error)}})
    inv.show(results, partial_failure=any("error" in item for item in results))


@click.group(cls=Group)
def graph():
    """查询图结构，或提交互相引用的新实体；不隐式读取 Resolver 内容。"""


@graph.command()
@click.argument("reference")
@click.option("--direction", type=click.Choice(["both", "out", "in"]))
@click.option("--content", "contents", multiple=True, help="重复传入关系 content 过滤值")
@paging
@common
@click.pass_obj
def neighborhood(inv: Invocation, reference, direction, contents, limit, cursor):
    """展开一个实体的一跳邻域。"""
    ref = entity(reference)
    if ref.type == "relation" and (direction or contents or limit or cursor):
        raise click.UsageError("Relation 邻域只有两个端点，不接受 Block 的遍历参数")
    inv.show(
        inv.send(
            "GET",
            f"/{ref.type}s/{ref.id}/neighborhood",
            params={
                "direction": direction,
                "contents": contents or None,
                "limit": limit,
                "cursor": cursor,
            },
        )
    )


@graph.command("path")
@click.option("--from", "from_id", required=True, type=int)
@click.option("--to", "to_id", required=True, type=int)
@input_options
@common
@click.pass_obj
def path(inv: Invocation, from_id, to_id, schema, input_file, input_json):
    """在边界内查找路径；JSON 可填写 direction、contents 和探索预算。"""
    if schema:
        return inv.show(
            request_schema(inv.client, "/graph/path", "POST", omit=("from_block_id", "to_block_id"))
        )
    inv.show(
        inv.send(
            "POST",
            "/graph/path",
            body={
                **load_input(input_file, input_json),
                "from_block_id": from_id,
                "to_block_id": to_id,
            },
            selectors={"from_block_id": "--from", "to_block_id": "--to"},
        )
    )


@graph.command()
@click.argument("seeds", nargs=-1, type=int)
@input_options
@common
@click.pass_obj
def components(inv: Invocation, seeds, schema, input_file, input_json):
    """按 JSON 中明确的关系 contents 查询种子 Block 的连通分量。"""
    if schema:
        return inv.show(
            request_schema(inv.client, "/graph/components", "POST", omit=("seed_block_ids",))
        )
    inv.show(
        inv.send(
            "POST",
            "/graph/components",
            body={
                **load_input(input_file, input_json),
                "seed_block_ids": seeds,
            },
            selectors={"seed_block_ids": "seeds"},
        )
    )


@graph.command()
@input_options
@common
@click.pass_obj
def submit(inv: Invocation, schema, input_file, input_json):
    """追加 GraphForm；负数 ID 表达本次新实体之间的引用。"""
    if schema:
        return inv.show(request_schema(inv.client, "/graph", "POST"))
    inv.show(inv.send("POST", "/graph", body=load_input(input_file, input_json)))


@click.group(cls=Group)
def resolver():
    """发现并调用 Core 当前加载的 Resolver 读取方法。"""


@resolver.command("list")
@paging
@common
@click.pass_obj
def list_resolvers(inv: Invocation, limit, cursor):
    """列出当前接入 Core 的 Resolver，不枚举每个方法的 schema。"""
    inv.show(inv.send("GET", "/resolvers", params={"limit": limit, "cursor": cursor}))


@resolver.command()
@click.argument("target")
@paging
@common
@click.pass_obj
def methods(inv: Invocation, target, limit, cursor):
    """TARGET 为 block:<id> 或 exact Resolver ID。"""
    route = (
        f"/blocks/{entity(target, block_only=True).id}/resolver"
        if target.startswith("block:")
        else f"/resolvers/{segment(target)}"
    )
    inv.show(inv.send("GET", route + "/methods", params={"limit": limit, "cursor": cursor}))


@resolver.command()
@click.argument("reference")
@click.option("--method", required=True, help="准确的方法名，例如 get_solved_content")
@input_options
@common
@click.pass_obj
def invoke(inv: Invocation, reference, method, schema, input_file, input_json):
    """在指定 Block 的 Resolver 上调用一个方法；读取可能触发 materialization。"""
    route = f"/blocks/{entity(reference, block_only=True).id}/resolver/methods"
    if schema:
        contract = inv.send("GET", route)
        selected = next((item for item in contract["methods"] if item["name"] == method), None)
        if selected is None:
            raise CommandError(f"未发现 Resolver method {method!r}")
        return inv.show(selected["input_schema"])
    inv.show(
        inv.send("POST", route + "/" + segment(method), body=load_input(input_file, input_json))
    )
