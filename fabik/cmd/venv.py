""" .. _fabik_cmd_venv:

fabik.cmd.venv
~~~~~~~~~~~~~~~~~~~~~~

venv 子命令相关函数
"""

import typer
from typing import Annotated
from enum import StrEnum

from fabik.error import echo_error


class DeployClassName(StrEnum):
    GUNICORN = "gunicorn"
    uWSGI = "uwsgi"


NoteReqirementsFileName = Annotated[
    str, typer.Option(help="指定 requirements.txt 的文件名。")
]


# 延迟导入避免循环导入
def _get_global_state():
    from fabik.cmd import global_state
    return global_state


def server_callback(
    deploy_class: Annotated[
        DeployClassName, typer.Option(help="指定部署类。")
    ] = DeployClassName.GUNICORN,
):
    global_state = _get_global_state()
    if deploy_class == DeployClassName.GUNICORN:
        from fabik.deploy.gunicorn import GunicornDeploy as Deploy

        global_state.build_deploy_conn(Deploy)
    elif deploy_class == DeployClassName.uWSGI:
        from fabik.deploy.uwsgi import UwsgiDeploy as Deploy

        global_state.build_deploy_conn(Deploy)


def venv_init(
    requirements_file_name: NoteReqirementsFileName = "requirements.txt",
):
    """「远程」部署远程服务器的虚拟环境。"""
    global_state = _get_global_state()
    try:
        rsync_exclude = global_state.conf_data.get("RSYNC_EXCLUDE", [])
        global_state.deploy_conn.rsync(exclude=rsync_exclude)
        global_state.deploy_conn.init_remote_venv(requirements_file_name)
    except Exception as e:
        echo_error(f"初始化虚拟环境失败: {str(e)}")
        raise typer.Abort()


def venv_update(
    name: Annotated[
        list[str] | None, typer.Argument(help="指定希望更新的 pip 包名称。")
    ] = None,
    all: Annotated[bool, typer.Option(help="更新所有 pip 包。")] = False,
):
    """「远程」部署远程服务器的虚拟环境。"""
    global_state = _get_global_state()
    try:
        if all:
            global_state.deploy_conn.pipupgrade(all=True)
        elif name is not None and len(name) > 0:
            global_state.deploy_conn.pipupgrade(names=name)
        else:
            echo_error("请提供希望更新的 pip 包名称。")
            raise typer.Abort()
    except Exception as e:
        echo_error(f"更新 pip 包失败: {str(e)}")
        raise typer.Abort()


def venv_outdated():
    """「远程」打印所有的过期的 python package。"""
    global_state = _get_global_state()
    global_state.deploy_conn.pipoutdated()  # type: ignore # noqa: F821
