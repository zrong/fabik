""".. _fabik_cmd_main:

fabik.cmd.main
~~~~~~~~~~~~~~~~~~~~~~

主要命令相关函数
"""

from typing import Annotated
from pathlib import Path

import typer
import jinja2

import fabik
from fabik import tpl
from fabik.conf import FabikConfig
from fabik.conf.storage import FabikConfigFile
from fabik.error import echo_error, echo_info, echo_warning, FabikError
from fabik.cmd import global_state, NoteForce


def main_callback(
    ctx: typer.Context,
    env: Annotated[
        str | None, typer.Option("--env", "-e", help="Environment name.")
    ] = None,
    cwd: Annotated[
        Path | None,
        typer.Option(
            file_okay=False, exists=True, help="Specify the local working directory."
        ),
    ] = None,
    config_file: Annotated[
        Path | None,
        typer.Option(
            file_okay=True, exists=True, help="Specify the configuration file."
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show more information.")
    ] = False,
    version: Annotated[
        bool, typer.Option("--version", is_eager=True, help="Show fabik version.")
    ] = False,
):
    if version:
        echo_info(fabik.__version__)
        raise typer.Exit()

    # 如果没有子命令且没有版本选项，显示帮助
    if ctx.invoked_subcommand is None:
        echo_info(ctx.get_help())
        raise typer.Exit()

    try:
        global_state.verbose = verbose
        global_state.env = env
        global_state.fabik_file = FabikConfigFile.gen_fabik_config_file(
            work_dir=cwd, config_file=config_file
        )
        global_state.cwd = global_state.fabik_file.getdir()
    except FabikError as e:
        echo_error(e.err_msg)
        raise typer.Exit()

    if global_state.verbose:
        echo_info(
            f"{global_state!r}",
            panel_title="main_callback",
        )


def main_init(
    full_format: Annotated[
        bool, typer.Option(help="Use full format configuration file.")
    ] = False,
    force: NoteForce = False,
):
    """[local] Initialize fabik project, create fabik.toml and .fabik.env configuration files in the working directory."""
    # 对于 init 命令，直接使用 global_state.cwd，因为此时可能还没有配置文件
    work_dir: Path = global_state.cwd

    # 准备模板变量
    template_vars = {
        "create_time": f"{fabik.__now__!s}",
        "fabik_version": fabik.__version__,
        "WORK_DIR": work_dir.absolute().as_posix(),
        "NAME": work_dir.name,  # 使用目录名作为默认项目名
    }

    # 创建 fabik.toml
    toml_content = jinja2.Template(tpl.FABIK_TOML_TPL).render(**template_vars)

    # 创建 .fabik.env
    env_content = jinja2.Template(tpl.FABIK_ENV_TPL).render(**template_vars)

    toml_file = work_dir.joinpath(tpl.FABIK_TOML_FILE)
    env_file = work_dir.joinpath(tpl.FABIK_ENV_FILE)

    # 检查文件存在性和处理覆盖逻辑
    files_to_create = [(toml_file, toml_content), (env_file, env_content)]
    files_to_write = []  # 实际需要写入的文件列表
    has_existing_files = False  # 是否有已存在的文件

    for file_path, content in files_to_create:
        if file_path.exists():
            has_existing_files = True
            if force:
                echo_warning(f"Overwriting {file_path!s}.")
                files_to_write.append((file_path, content))
            else:
                echo_warning(f"{file_path!s} already exists. Skipping.")
        else:
            # 文件不存在，需要创建
            files_to_write.append((file_path, content))

    # 如果有已存在的文件但未使用 --force，且没有任何文件需要写入，则提示并退出
    if has_existing_files and not force and not files_to_write:
        echo_warning(
            "All configuration files already exist. Use --force to overwrite them."
        )
        raise typer.Exit()

    # 写入需要创建或覆盖的文件
    if files_to_write:
        for file_path, content in files_to_write:
            file_path.write_text(content)
            echo_info(f"{file_path} has been created.")
    else:
        echo_info("No files need to be created.")
