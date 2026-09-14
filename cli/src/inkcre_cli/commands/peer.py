"""Peer record discovery and explicit HTTP readiness observation."""

import asyncio

import click
import httpx

from ..command import Group, Invocation, common, duration, paging, segment
from ..errors import CommandError


@click.group(cls=Group)
def peer():
    """读取 Peer 记录；wake 只针对已配置的 HTTP connection。"""


@peer.command("list")
@paging
@common
@click.pass_obj
def list_peers(inv: Invocation, limit, cursor):
    """lease_active 来自数据库时间，不等于所有 capability 可用。"""
    inv.show(inv.send("GET", "/peers", params={"limit": limit, "cursor": cursor}))


@peer.command()
@click.argument("peer_id", default="self")
@common
@click.pass_obj
def get(inv: Invocation, peer_id):
    """读取 UUID 或内置别名 self 所指向的接入 Peer。"""
    inv.show(inv.send("GET", "/peers/" + segment(peer_id)))


async def wait_ready(inv: Invocation, seconds: float):
    client = inv.client
    last_error = None
    async with httpx.AsyncClient(timeout=30) as http:
        try:
            async with asyncio.timeout(seconds):
                while True:
                    response = await http.send(
                        client.build_request("GET", "/readyz", authenticated=False)
                    )
                    try:
                        return {
                            "endpoint": client.base_url,
                            "readyz": client.read_response(response),
                        }
                    except CommandError as error:
                        if error.status != 503:
                            raise
                        last_error = error
                    await asyncio.sleep(2)
        except TimeoutError:
            if last_error:
                raise last_error from None
            raise CommandError("唤醒观察预算已用尽，尚未取得就绪响应") from None


@peer.command()
@click.option("--for", "wait_for", default="30s", show_default=True)
@common
@click.pass_obj
def wake(inv: Invocation, wait_for):
    """在有界时间内请求当前 connection 的 /readyz；不发现或猜测其它 Peer 地址。"""
    inv.show(asyncio.run(wait_ready(inv, duration(wait_for))))
