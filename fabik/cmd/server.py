""" .. _fabik_cmd_server:

fabik.cmd.server
~~~~~~~~~~~~~~~~~~~~~~

server 子命令相关函数
"""

from typing import Annotated

import typer

from fabik.error import echo_error, FabikError
from fabik.cmd import global_state, DeployClassName



def server_callback(
    deploy_class: Annotated[
        DeployClassName, typer.Option(help="指定部署类。")
    ] = DeployClassName.GUNICORN,
):
    if deploy_class == DeployClassName.GUNICORN:
        from fabik.deploy.gunicorn import GunicornDeploy as Deploy

        global_state.build_deploy_conn(Deploy)
    elif deploy_class == DeployClassName.uWSGI:
        from fabik.deploy.uwsgi import UwsgiDeploy as Deploy

        global_state.build_deploy_conn(Deploy)


def server_deploy():
    """「远程」部署项目到远程服务器。"""
    global_state.deploy_conn.rsync(
        exclude=global_state.fabik_config.getcfg("RSYNC_EXCLUDE", [])
    )  # type: ignore # noqa: F821
    global_state.deploy_conn.put_config(force=True)  # type: ignore # noqa: F821


def server_start():
    """「远程」在服务器上启动项目进程。"""
    global_state.deploy_conn.start()  # type: ignore # noqa: F821


def server_stop():
    """「远程」在服务器上停止项目进程。"""
    global_state.deploy_conn.stop()  # type: ignore # noqa: F821


def server_reload():
    """「远程」在服务器上重载项目进程。"""
    global_state.deploy_conn.reload()  # type: ignore # noqa: F821


def server_dar():
    """「远程」在服务器上部署代码，然后执行重载。也就是 deploy and reload 的组合。"""
    try:
        global_state.deploy_conn.rsync(
            exclude=global_state.conf_data.get("RSYNC_EXCLUDE", [])
        )  # type: ignore # noqa: F821
        global_state.deploy_conn.put_config(force=True)  # type: ignore # noqa: F821
        global_state.deploy_conn.reload()  # type: ignore # noqa: F821
    except FabikError as e:
        echo_error(e.err_msg)
        raise typer.Abort()
    except Exception as e:
        echo_error(str(e))
        raise typer.Abort()
