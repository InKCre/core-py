"""Job admission and bounded observation; the CLI never executes a Job."""

import asyncio

import click
import httpx

from ..command import (
    Group,
    Invocation,
    common,
    duration,
    input_options,
    load_input,
    paging,
    segment,
)
from ..errors import CommandError
from ..schema import nested, request_schema


@click.group(cls=Group)
def job():
    """创建、观察和请求停止后台 Job。"""


@job.command()
@click.argument("type_id", required=False)
@paging
@common
@click.pass_obj
def types(inv: Invocation, type_id, limit, cursor):
    """列出持久化 Job type；给出 exact ID 时读取其参数合同。"""
    inv.show(
        inv.send(
            "GET",
            "/job-types" + ("/" + segment(type_id) if type_id else ""),
            params={"limit": limit, "cursor": cursor},
        )
    )


@job.command()
@click.option("--type", "type_id", required=True)
@input_options
@common
@click.pass_obj
def create(inv: Invocation, type_id, schema, input_file, input_json):
    """受理一个 Job；JSON 包含 parameters 与可选 timeout_seconds。"""
    if schema:
        owner = inv.send("GET", "/job-types/" + segment(type_id))
        return inv.show(
            nested(
                request_schema(inv.client, "/jobs", "POST", omit=("type",)),
                "parameters",
                owner["parameters_schema"],
            )
        )
    inv.show(
        inv.send(
            "POST",
            "/jobs",
            body={**load_input(input_file, input_json), "type": type_id},
            selectors={"type": "--type"},
        )
    )


@job.command("list")
@click.option("--type", "type_id")
@click.option(
    "--status",
    type=click.Choice(["pending", "running", "finished", "failed", "timed_out", "aborted"]),
)
@paging
@common
@click.pass_obj
def list_jobs(inv: Invocation, type_id, status, limit, cursor):
    """最近的 Job，默认 20 项；cursor 由上一页返回。"""
    inv.show(
        inv.send(
            "GET",
            "/jobs",
            params={"type": type_id, "status": status, "limit": limit, "cursor": cursor},
        )
    )


@job.command()
@click.argument("job_id", type=int)
@common
@click.pass_obj
def get(inv: Invocation, job_id):
    """读取实际记录；failed Job 也是一次成功的读取。"""
    inv.show(inv.send("GET", f"/jobs/{job_id}"))


@job.command()
@click.argument("job_id", type=int)
@common
@click.pass_obj
def abort(inv: Invocation, job_id):
    """请求 best-effort 停止；running + abort_requested 不等于已经结束。"""
    inv.show(inv.send("POST", f"/jobs/{job_id}/abort"))


async def observe(inv: Invocation, job_id: int, seconds: float):
    client = inv.client
    last = None
    # HTTPX phase timeouts are not a wall-clock deadline. This small asynchronous
    # scope bounds the entire observation, including a slow in-flight response;
    # cancellation closes the actual request, not an abandoned worker thread.
    async with httpx.AsyncClient(timeout=30) as http:
        try:
            async with asyncio.timeout(seconds):
                while True:
                    response = await http.send(client.build_request("GET", f"/jobs/{job_id}"))
                    last = client.read_response(response)
                    if last["status"] not in {"pending", "running"}:
                        return last
                    await asyncio.sleep(2)
        except TimeoutError:
            if last is None:
                raise CommandError("观察预算已用尽，尚未取得 Job 记录") from None
    return last


@job.command()
@click.argument("job_id", type=int)
@click.option("--for", "wait_for", default="30s", show_default=True)
@common
@click.pass_obj
def wait(inv: Invocation, job_id, wait_for):
    """最多观察指定时间，终态提前返回；用尽预算不会停止远端 Job。"""
    inv.show(asyncio.run(observe(inv, job_id, duration(wait_for))))


@click.group(cls=Group)
def organization():
    """为整理创建 Job；自动行为与 Agent 的选择通过 deployment config 管理。"""


@organization.command()
@click.argument("block_id", type=int)
@click.option("--timeout-seconds", type=click.IntRange(min=1))
@common
@click.pass_obj
def ruminate(inv: Invocation, block_id, timeout_seconds):
    """为一个 Block 派发 explicit rumination Job，不直接调用 Peer inbound。"""
    inv.show(
        inv.send(
            "POST",
            "/jobs",
            body={
                "type": "core.organization.rumination.explicit.v1",
                "parameters": {"block": block_id},
                "timeout_seconds": timeout_seconds,
            },
            selectors={"parameters": "block_id"},
        )
    )


@click.group(cls=Group)
def cron():
    """配置服务端定期派发的 Job 模板；CLI 不运行 scheduler。"""


@cron.command("list")
@paging
@common
@click.pass_obj
def list_crons(inv: Invocation, limit, cursor):
    """列出 Cron。"""
    inv.show(inv.send("GET", "/crons", params={"limit": limit, "cursor": cursor}))


@cron.command("get")
@click.argument("cron_id", type=int)
@common
@click.pass_obj
def get_cron(inv: Invocation, cron_id):
    """读取一个 Cron。"""
    inv.show(inv.send("GET", f"/crons/{cron_id}"))


@cron.command("create")
@click.option("--job-type", required=True)
@input_options
@common
@click.pass_obj
def create_cron(inv: Invocation, job_type, schema, input_file, input_json):
    """创建五字段 UNIX Cron；时区来自 deployment config。"""
    if schema:
        owner = inv.send("GET", "/job-types/" + segment(job_type))
        return inv.show(
            nested(
                request_schema(inv.client, "/crons", "POST", omit=("job_type",)),
                "job_parameters",
                owner["parameters_schema"],
            )
        )
    inv.show(
        inv.send(
            "POST",
            "/crons",
            body={**load_input(input_file, input_json), "job_type": job_type},
            selectors={"job_type": "--job-type"},
        )
    )


@cron.command("update")
@click.argument("cron_id", type=int)
@click.option("--job-type", help="同时替换 Job type；--schema 据此投影参数")
@input_options
@common
@click.pass_obj
def update_cron(inv: Invocation, cron_id, job_type, schema, input_file, input_json):
    """修改提交的 Cron 字段；省略字段保持。"""
    if schema:
        selected = job_type or inv.send("GET", f"/crons/{cron_id}")["job_type"]
        owner = inv.send("GET", "/job-types/" + segment(selected))
        return inv.show(
            nested(
                request_schema(
                    inv.client, "/crons/{cron_id}", "PATCH", omit=("job_type",) if job_type else ()
                ),
                "job_parameters",
                owner["parameters_schema"],
            )
        )
    body = load_input(input_file, input_json)
    if job_type:
        body["job_type"] = job_type
    inv.show(
        inv.send(
            "PATCH",
            f"/crons/{cron_id}",
            body=body,
            selectors={"job_type": "--job-type"} if job_type else None,
        )
    )


@cron.command("delete")
@click.argument("cron_id", type=int)
@common
@click.pass_obj
def delete_cron(inv: Invocation, cron_id):
    """删除 Cron 模板，不删除已经创建的 Job。"""
    inv.show(inv.send("DELETE", f"/crons/{cron_id}"), no_content=True)


@cron.command()
@click.argument("cron_id", type=int)
@common
@click.pass_obj
def enable(inv: Invocation, cron_id):
    """启用未来的定期派发。"""
    inv.show(inv.send("PATCH", f"/crons/{cron_id}", body={"enabled": True}))


@cron.command()
@click.argument("cron_id", type=int)
@common
@click.pass_obj
def disable(inv: Invocation, cron_id):
    """停止未来的定期派发，不取消已经创建的 Job。"""
    inv.show(inv.send("PATCH", f"/crons/{cron_id}", body={"enabled": False}))


@cron.command()
@click.argument("cron_id", type=int)
@common
@click.pass_obj
def run(inv: Invocation, cron_id):
    """从模板立即派发一次 Job，不改变定期进度。"""
    inv.show(inv.send("POST", f"/crons/{cron_id}/run"))
