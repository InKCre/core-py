"""Agent definitions and read-only AI/profile discovery."""

import click

from ..command import Group, Invocation, common, input_options, load_input, paging, segment
from ..schema import request_schema


@click.group(cls=Group)
def agent():
    """管理 Agent definition；不启动对话或本机 Agent runtime。"""


@agent.command("list")
@paging
@common
@click.pass_obj
def list_agents(inv: Invocation, limit, cursor):
    """列出 Agent definition。"""
    inv.show(inv.send("GET", "/agents", params={"limit": limit, "cursor": cursor}))


@agent.command()
@click.argument("agent_id", type=int)
@common
@click.pass_obj
def get(inv: Invocation, agent_id):
    """读取一个 Agent definition。"""
    inv.show(inv.send("GET", f"/agents/{agent_id}"))


@agent.command()
@input_options
@common
@click.pass_obj
def create(inv: Invocation, schema, input_file, input_json):
    """创建 Agent definition；模型用 ai models、工具用 agent tools 发现。"""
    if schema:
        return inv.show(request_schema(inv.client, "/agents", "POST"))
    inv.show(inv.send("POST", "/agents", body=load_input(input_file, input_json)))


@agent.command()
@click.argument("agent_id", type=int)
@input_options
@common
@click.pass_obj
def update(inv: Invocation, agent_id, schema, input_file, input_json):
    """修改提交的 Agent definition 字段。"""
    if schema:
        return inv.show(request_schema(inv.client, "/agents/{agent_id}", "PATCH"))
    inv.show(inv.send("PATCH", f"/agents/{agent_id}", body=load_input(input_file, input_json)))


@agent.command()
@click.argument("agent_id", type=int)
@common
@click.pass_obj
def delete(inv: Invocation, agent_id):
    """删除 Agent definition。"""
    inv.show(inv.send("DELETE", f"/agents/{agent_id}"), no_content=True)


@agent.command()
@click.argument("tool_id", required=False)
@paging
@common
@click.pass_obj
def tools(inv: Invocation, tool_id, limit, cursor):
    """列出本机已注册 Agent Tool；给定 ID 时取得完整合同，不执行工具。"""
    inv.show(
        inv.send(
            "GET",
            "/agent-tools" + ("/" + segment(tool_id) if tool_id else ""),
            params={"limit": limit, "cursor": cursor},
        )
    )


@click.group(cls=Group)
def ai():
    """发现 AI 模型，不混入 Agent definition 的管理范围。"""


@ai.command()
@click.argument("model_id", type=int, required=False)
@paging
@common
@click.pass_obj
def models(inv: Invocation, model_id, limit, cursor):
    """列出 AIModel，或读取指定 ID；不返回 Provider 的 secret config。"""
    inv.show(
        inv.send(
            "GET",
            "/ai/models" + (f"/{model_id}" if model_id is not None else ""),
            params={"limit": limit, "cursor": cursor},
        )
    )


@click.group("embedding-profile", cls=Group)
def embedding_profile():
    """只读发现语义检索可选的 embedding profile。"""


@embedding_profile.command("list")
@paging
@common
@click.pass_obj
def list_profiles(inv: Invocation, limit, cursor):
    """列出 EmbeddingProfile。"""
    inv.show(inv.send("GET", "/embedding-profiles", params={"limit": limit, "cursor": cursor}))


@embedding_profile.command("get")
@click.argument("profile_id", type=int)
@common
@click.pass_obj
def get_profile(inv: Invocation, profile_id):
    """读取 EmbeddingProfile。"""
    inv.show(inv.send("GET", f"/embedding-profiles/{profile_id}"))
