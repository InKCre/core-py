"""Click's native dispatch, with the CLI's stdout/stderr and exit contract."""

import json
import sys

import click
import httpx
from pydantic import ValidationError

from .command import Group, Invocation, common
from .commands import agent, config, connection, extension, info, jobs, peer, sink, source
from .errors import CommandError
from .output import compact


@click.group(cls=Group, context_settings={"help_option_names": ["-h", "--help"]})
@common
def cli():
    """InKCre 的 REST 命令行界面。用 --help 离线发现操作，用 --schema 查询当前输入合同。

    CLI 不是 Core/Peer，不访问数据库或执行 Job。connection 管本机接入，config 管远端配置。
    """


for command in (
    info.recall,
    info.get,
    info.update,
    info.delete,
    info.graph,
    info.resolver,
    source.source,
    jobs.organization,
    jobs.job,
    jobs.cron,
    agent.agent,
    agent.ai,
    agent.embedding_profile,
    config.config,
    connection.connection,
    extension.extension,
    peer.peer,
    sink.sink,
    sink.query,
):
    cli.add_command(command)


def main() -> None:
    invocation = Invocation()
    code = 0
    failure = None
    try:
        result = cli.main(standalone_mode=False, obj=invocation)
        if isinstance(result, int):
            code = result
    except CommandError as error:
        failure, code = error.as_dict(), error.exit_code
    except click.ClickException as error:
        failure, code = {"detail": error.format_message()}, 2
    except ValidationError as error:
        failure, code = {"detail": json.loads(error.json(include_url=False))}, 2
    except (OSError, httpx.RequestError) as error:
        failure, code = {"detail": str(error)}, 1
    except (KeyboardInterrupt, click.Abort):
        failure, code = {"detail": "观察已中断；没有请求停止远端 Job"}, 130
    finally:
        invocation.close()
    if failure is not None:
        click.echo(
            compact(failure) if invocation.output.json_mode else str(failure["detail"]), err=True
        )
    sys.exit(code)


if __name__ == "__main__":
    main()
