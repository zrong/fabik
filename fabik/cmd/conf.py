""".. _fabik_cmd_conf:

fabik.cmd.conf
~~~~~~~~~~~~~~~~~~~~~~

conf 子命令相关函数
"""

import typer
from typing import Annotated
from pathlib import Path

from fabik.conf import config_validator_tpldir
from fabik.error import echo_error
from fabik.cmd import global_state, NoteOutputDir, NoteOutputFile, NoteForce, NoteRename, NoteEnvPostfix


def conf_callback(
    force: NoteForce = False,
    rename: NoteRename = False,
    output_dir: NoteOutputDir = None,
    output_file: NoteOutputFile = None,
    env_postfix: NoteEnvPostfix = False,
):
    global_state.force = force
    global_state.rename = rename
    global_state.output_dir = output_dir
    global_state.output_file = output_file
    global_state.env_postfix = env_postfix


def conf_tpl(
    file: Annotated[
        list[str],
        typer.Argument(
            help="Provide configuration file names based on the tpl directory."
        ),
    ],
):
    """[local] Initialize configuration file content based on the template files in the local tpl directory."""
    # 需要检查 tpl_dir 是否存在
    global_state.register_config_validator(config_validator_tpldir)
    global_state.load_conf_data(check=True)
    tpl_dir = Path(global_state.fabik_config.TPL_DIR)  # type: ignore
    tpl_names: list[str] = []
    for n in file:
        # 模板名称统一不带 jinja2 后缀，模板文件必须带有 jinja2 后缀。
        tpl_name = n[:-7] if n.endswith(".jinja2") else n
        tpl_file = tpl_dir.joinpath(f"{tpl_name}.jinja2")
        tpl_names.append(tpl_name)
        if not tpl_file.exists():
            echo_error(f'Template file "{tpl_file}" not found.')
            raise typer.Abort()

    for tpl_name in tpl_names:
        global_state.write_config_file(
            tpl_name,
            tpl_dir=tpl_dir,
            target_postfix=f".{global_state.fabik_config.env_name}" if global_state.env_postfix else "",  # pyright: ignore[reportOptionalMemberAccess]
        )


def conf_make(
    file: Annotated[
        list[str],
        typer.Argument(help="Make a configuration file in fabik.toml."),
    ],
    env_postfix: NoteEnvPostfix = False,
):
    """[local] Initialize configuration file content based on the fabik.toml, no template file is used."""
    global_state.load_conf_data(check=True)
    for f in file:
        global_state.write_config_file(
            f, target_postfix=f".{global_state.fabik_config.env_name}" if global_state.env_postfix else ""  # pyright: ignore[reportOptionalMemberAccess]
        )
