""".._fabik_cmd:

fabik.cmd
----------------------------

fabik command line toolset
"""

__all__ = ["main_callback", "main_init", "conf_callback", "conf_tpl"]

import shutil
from pathlib import Path
from typing import Any, Callable

import jinja2
import typer
from typing import Annotated

import fabik
from fabik.conf import ConfigReplacer, FabikConfig, TplWriter
from fabik.tpl import FABIK_TOML_FILE, FABIK_TOML_TPL, FABIK_TOML_SIMPLE_TPL
from fabric.connection import Connection
from fabik.error import (
    ConfigError,
    FabikError,
    PathError,
    echo_error,
    echo_info,
    echo_warning,
)


class GlobalState:
    cwd: Path | None = None
    env: str | None = None
    force: bool = False
    conf_file: Path | None = None
    fabic_config: FabikConfig | None = None
    _config_validators: list[Callable] = []  # 存储自定义验证器函数

    @property
    def conf_data(self) -> dict[str, Any]:
        if self.fabic_config is None:
            return {}
        return self.fabic_config.root_data or {}

    def register_config_validator(self, validator_func: Callable) -> None:
        """注册一个配置验证函数，用于验证配置数据。

        验证函数应接受 FabikConfig 对象作为参数，返回 bool 值表示验证结果。
        如果验证失败，验证函数应自行处理错误提示。

        :param validator_func: 验证函数
        """
        if callable(validator_func) and validator_func not in self._config_validators:
            self._config_validators.append(validator_func)

    def _check_conf_data(self) -> bool:
        """执行所有已注册的配置验证器"""
        if not self.fabic_config:
            return False

        # 运行所有注册的验证器
        for validator in self._config_validators:
            try:
                if not validator(self.fabic_config):
                    return False
            except Exception as e:
                echo_error(f"Config validation error: {str(e)}")
                raise typer.Abort()

        return True

    def load_conf_data(
        self,
        check: bool = False,
        file_not_found_err_msg: str = 'Please call "fabik init" to generate a "fabik.toml" file.',
    ) -> dict[str, Any]:
        try:
            self.fabic_config = FabikConfig(self.cwd, cfg=self.conf_file)
            self.fabic_config.load_root_data()
            if check:
                self._check_conf_data()
            return self.conf_data
        except PathError as e:
            if isinstance(e.err_type, FileNotFoundError):
                echo_error(file_not_found_err_msg)
            else:
                echo_error(e.err_msg)
            raise typer.Abort()
        except ConfigError as e:
            echo_error(e.err_msg)
            raise typer.Abort()
        except FabikError as e:
            echo_error(e.err_msg)
            raise typer.Abort()
        except Exception as e:
            echo_error(e)
            raise typer.Abort()

    def write_config_file(
        self,
        tpl_name: str,
        /,
        tpl_dir: Path | None = None,
        target_postfix: str = "",
    ) -> None:
        """写入配置文件

        :param target_postfix: 配置文件的后缀
        """
        try:
            replacer = ConfigReplacer(
                global_state.conf_data,
                work_dir=global_state.cwd,  # type: ignore
                tpl_dir=tpl_dir,
                env_name=global_state.env,
            )
            target, final_target = replacer.set_writer(
                tpl_name, global_state.force, target_postfix
            )

            # 写入文件
            if replacer.writer:
                replacer.writer.write_file(global_state.force)
        except FabikError as e:
            echo_error(e.err_msg)
            raise typer.Abort()
        except Exception as e:
            echo_error(str(e))
            raise typer.Abort()


def check_none(value: Any, key_list: list[str]) -> Any:
    if value is None:
        echo_error(f'Key "{key_list!s}" not found in config.')
        raise typer.Abort()
    return value


def check_path_exists(p: Path) -> bool:
    if not p.is_absolute():
        echo_error(f"{p!s} is not a absolute path.")
        raise typer.Abort()
    if not p.exists():
        echo_error(f"{p!s} is not a exists path.")
        raise typer.Abort()
    return True


# 默认验证器函数
def config_validator_name_workdir(config: FabikConfig) -> bool:
    """检查 NAME 和 work_dir 是否存在"""
    keys = (["NAME"], ["PATH", "work_dir"])
    for key_list in keys:
        value = check_none(config.getcfg(*key_list), key_list)
        if key_list[-1] == "work_dir":
            check_path_exists(Path(value))
    return True


def config_validator_tpldir(config: FabikConfig) -> bool:
    """默认的配置验证逻辑，检查必要的配置项是否存在"""
    key_list = ["PATH", "tpl_dir"]
    value = check_none(config.getcfg(*key_list), key_list)
    check_path_exists(Path(value))
    return True


# 创建全局状态实例并注册默认验证器
global_state = GlobalState()
global_state.register_config_validator(config_validator_name_workdir)


def copytplfile(keyname: str, filename: str, rename: bool = False):
    """复制文件到目标文件夹。

    :param rename: 若文件已存在是否重命名
    """
    split_path = keyname.split("/")

    # 源文件夹
    srcfiledir = pyape_tpl_dir
    # 目标文件夹
    dstfiledir = global_state.cwd
    while len(split_path) > 1:
        # 检测是否拥有中间文件夹，若有就创建它
        dstfiledir = dstfiledir.joinpath(split_path[0])
        srcfiledir = srcfiledir.joinpath(split_path[0])
        if not dstfiledir.exists():
            dstfiledir.mkdir()
        split_path = split_path[1:]

    srcfile = srcfiledir / filename
    dstfile = dstfiledir / filename

    if dstfile.exists():
        if global_state.force:
            shutil.copyfile(srcfile, dstfile)
            echo_info(f"覆盖 [red]{srcfile}[/] 到 [red]{dstfile}[/]")
        elif rename:
            dstbak = dstfile.parent.joinpath(dstfile.name + ".bak")
            if dstbak.exists():
                echo_warning(f"备份文件 [red]{dstbak}[/] 已存在！请先删除备份文件。")
            else:
                shutil.move(dstfile, dstbak)
                echo_info(f"备份文件 [yellow]{dstfile}[/] 到 [yellow]{dstbak}[/]")
                shutil.copyfile(srcfile, dstfile)
                echo_info(f"复制 {srcfile} 到 {dstfile}")
        else:
            echo_warning(f"文件 [red]{dstfile}[/] 已存在！")
    else:
        shutil.copyfile(srcfile, dstfile)
        echo_info(f"复制 [red]{srcfile}[/] 到 [red]{dstfile}[/]！")


def build_deploy_conn(ctx: typer.Context, deploy_class: type["Deploy"]) -> "Deploy":  # noqa: F821
    """创建一个远程部署连接。"""
    try:
        pyape_conf = check_fabik_toml(ctx)
        replacer = ConfigReplacer(global_state.env, pyape_conf, global_state.cwd)
        # 从 pyape.toml 配置中获取服务器地址
        fabric_conf = replacer.get_tpl_value("FABRIC", merge=False)

        d = deploy_class(
            global_state.env,
            global_state.conf_data,
            Connection(**fabric_conf),
            global_state.cwd,
        )
        return d
    except FabikError as e:
        ctx.fail(e.err_msg)
    except Exception as e:
        ctx.fail(str(e))


# ==============================================
# functions for command line interface
# ==============================================

NoteEnv = Annotated[str | None, typer.Option("--env", "-e", help="Environment name.")]
NoteCwd = Annotated[
    Path,
    typer.Option(
        file_okay=False, exists=True, help="Specify the local working directory."
    ),
]
NoteConfFile = Annotated[
    Path | None,
    typer.Option(file_okay=True, exists=True, help="Specify the configuration file."),
]
NoteRename = Annotated[bool, typer.Option(help="If the target file exists, rename it.")]
NoteForce = Annotated[
    bool, typer.Option("--force", "-f", help="Force to overwrite the existing file.")
]
NoteEnvPostfix = Annotated[
    bool, typer.Option(help="在生成的配置文件名称末尾加上环境名称后缀。")
]


def main_callback(
    env: NoteEnv = None,
    cwd: NoteCwd = Path.cwd(),
    conf_file: NoteConfFile = None,
):
    global_state.cwd = cwd
    global_state.env = env
    global_state.conf_file = FabikConfig.gen_fabik_toml(
        work_dir=global_state.cwd, conf_file=conf_file
    )
    echo_info(f"main_callback {global_state=}", panel_title="LOG: main_callback")


def main_init(
    full_format: Annotated[
        bool, typer.Option(help="Use full format configuration file.")
    ] = False,
    force: NoteForce = False,
):
    """[local] Initialize fabik project, create fabik.toml configuration file in the working directory."""
    work_dir: Path = Path()
    try:
        conf = FabikConfig(global_state.cwd, cfg=global_state.conf_file)
        conf.load_root_data()
        work_dir = Path(conf.getcfg("PATH", "work_dir"))
        if not work_dir.is_absolute():
            echo_warning(f"{work_dir} is not a absolute path.")
            raise typer.Abort()
    except (PathError, ConfigError):
        pass

    value = jinja2.Template(
        FABIK_TOML_TPL if full_format else FABIK_TOML_SIMPLE_TPL
    ).render(
        create_time=f"{fabik.__now__!s}",
        fabik_version=fabik.__version__,
        WORK_DIR=work_dir.absolute().as_posix(),
    )

    toml_file = work_dir.joinpath(FABIK_TOML_FILE)

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


def conf_callback(
    force: NoteForce = False,
):
    global_state.force = force


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
    files: list[Path] = []
    # 需要检查 tpl_dir 是否存在
    global_state.register_config_validator(config_validator_tpldir)
    global_state.load_conf_data(check=True)
    tpl_dir = Path(global_state.fabic_config.getcfg("PATH", "tpl_dir"))  # type: ignore
    for n in file:
        f = tpl_dir.joinpath(n)
        files.append(f)
        if not f.exists():
            echo_error(f'Template file "{f}" not found.')
            raise typer.Abort()

    for f in files:
        global_state.write_config_file(
            f.name,
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
