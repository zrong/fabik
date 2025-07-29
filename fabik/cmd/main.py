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
    conf_file: Annotated[
        Path | None,
        typer.Option(
            file_okay=True, exists=True, help="Specify the configuration file."
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option('--verbose', "-v", help="Show more information.")
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
        global_state.cwd = FabikConfig.gen_work_dir(cwd)
        global_state.conf_file = (
            FabikConfig.gen_fabik_toml(work_dir=global_state.cwd, conf_file=None)
            if conf_file is None
            else conf_file
        )
    except FabikError as e:
        echo_error(e.err_msg)
        raise typer.Exit()

    if global_state.verbose:
        echo_info(
            f"{global_state!r}",
            panel_title="LOG: main_callback",
        )

def main_init(
    full_format: Annotated[
        bool, typer.Option(help="Use full format configuration file.")
    ] = False,
    force: NoteForce = False,
):
    """[local] Initialize fabik project, create fabik.toml configuration file in the working directory."""
    work_dir: Path = global_state.use_work_dir_or_cwd()

    value = jinja2.Template(
        tpl.FABIK_TOML_TPL if full_format else tpl.FABIK_TOML_SIMPLE_TPL
    ).render(
        create_time=f"{fabik.__now__!s}",
        fabik_version=fabik.__version__,
        WORK_DIR=work_dir.absolute().as_posix(),
    )

    toml_file = work_dir.joinpath(tpl.FABIK_TOML_FILE)

    if toml_file.exists():
        if force:
            # 如果强制覆盖，直接写入文件
            echo_warning(f"{toml_file!s} already exists. Overwriting it.")
        else:
            # 如果不强制覆盖，提示文件存在并退出
            echo_warning(f"{toml_file!s} already exists. Use --force to overwrite it.")
            raise typer.Exit()

    # 写入配置文件
    toml_file.write_text(value)
    echo_info(f"{toml_file} has been created.")
