""" .. _fabik_cmd_gen:

fabik.cmd.gen
~~~~~~~~~~~~~~~~~~~~~~

gen 子命令相关函数
"""

import typer
from typing import Annotated
from enum import StrEnum
import subprocess
from pathlib import Path

from fabik import util
from fabik.error import echo_info, echo_warning, echo_error


class UUIDType(StrEnum):
    UUID1 = "uuid1"
    UUID4 = "uuid4"


NoteForce = Annotated[
    bool, typer.Option("--force", "-f", help="Force to overwrite the existing file.")
]
NoteReqirementsFileName = Annotated[
    str, typer.Option(help="指定 requirements.txt 的文件名。")
]


# 延迟导入避免循环导入
def _get_global_state():
    from fabik.cmd import global_state
    return global_state


def gen_password(
    password: Annotated[str, typer.Argument(help="提供密码。", show_default=False)],
    salt: Annotated[
        str,
        typer.Argument(help="提供密码盐值。", show_default=False),
    ],
):
    """返回加盐之后的 PASSWORD。"""
    echo_info(util.gen.gen_password(password, salt))


def gen_fernet_key():
    """生成一个 SECRET_KEY。"""
    echo_info(util.gen.gen_fernet_key())


def gen_token(length: Annotated[int, typer.Argument(help="字符串位数。")] = 8):
    """根据提供的位数，返回一个 token 字符串。"""
    echo_info(util.gen.gen_token(k=length))


def gen_uuid(
    name: Annotated[UUIDType, typer.Argument(help="UUID 类型。")] = UUIDType.UUID4,
):
    """根据提供的名称，调用 uuid 库返回一个 UUID 字符串，仅支持 uuid1 和 uuid4 两种类型。"""
    echo_info(util.gen.gen_uuid(name.value))


def gen_requirements(
    force: NoteForce = False,
    requirements_file_name: NoteReqirementsFileName = "requirements.txt",
):
    """使用 uv 命令为当前项目生成 requirements.txt 依赖文件。"""
    global_state = _get_global_state()
    work_dir: Path = global_state.check_work_dir_or_use_cwd()
    requirements_txt = work_dir / requirements_file_name
    if requirements_txt.exists() and not force:
        echo_warning(
            f"{requirements_txt.absolute().as_posix()} 文件已存在，使用 --force 强制覆盖。"
        )
        raise typer.Exit()
    try:
        # 执行 uv export 命令生成 requirements.txt
        subprocess.run(
            [
                "uv",
                "export",
                "--format",
                "requirements-txt",
                "--no-hashes",
                "--output-file",
                f"{requirements_txt.absolute().as_posix()}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        echo_info(f"{requirements_txt.absolute().as_posix()} 文件已成功生成！")
    except subprocess.CalledProcessError as e:
        echo_error(f"生成 {requirements_txt.absolute().as_posix()} 失败: {e.stderr}")
        raise typer.Abort()
    except FileNotFoundError:
        echo_error("未找到 uv 命令，请确保已安装 uv 工具")
        raise typer.Abort()
