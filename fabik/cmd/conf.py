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
from fabik.cmd import global_state

NoteForce = Annotated[
    bool, typer.Option("--force", "-f", help="Force to overwrite the existing file.")
]
NoteEnvPostfix = Annotated[
    bool, typer.Option(help="在生成的配置文件名称末尾加上环境名称后缀。")
]


def conf_callback(
    force: NoteForce = False,
    output_dir: Annotated[
        Path | None, typer.Option(help="指定输出目录的完整路径。")
    ] = None,
):
    global_state.force = force
    global_state.output_dir = output_dir


def conf_tpl(
    file: Annotated[
        list[str],
        typer.Argument(
            help="Provide configuration file names based on the tpl directory."
        ),
    ],
    env_postfix: NoteEnvPostfix = False,
):
    """[local] Initialize configuration file content based on the template files in the local tpl directory."""
    # 需要检查 tpl_dir 是否存在
    global_state.register_config_validator(config_validator_tpldir)
    global_state.load_conf_data(check=True)
    tpl_dir = Path(global_state.fabic_config.getcfg("TPL_DIR"))  # type: ignore
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
            target_postfix=f".{global_state.env}" if env_postfix else "",
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
            f, target_postfix=f".{global_state.env}" if env_postfix else ""
        )
