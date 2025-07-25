""".._fabik_cmd:

fabik.cmd
----------------------------

fabik command line toolset
"""

__all__ = [
    "main_callback",
    "main_init",
    "conf_callback",
    "conf_tpl",
    "gen_requirements",
]

from enum import StrEnum
from ntpath import expanduser
import shutil
from pathlib import Path
from typing import Any, Callable

import jinja2
import typer
from typing import Annotated
import subprocess

import fabik
from fabik import tpl, util
from fabik.conf import (
    ConfigReplacer,
    FabikConfig,
    config_validator_name_workdir,
    config_validator_tpldir,
)
from fabric.connection import Connection
from fabik.error import (
    ConfigError,
    FabikError,
    PathError,
    echo_error,
    echo_info,
    echo_warning,
)


class UUIDType(StrEnum):
    UUID1 = "uuid1"
    UUID4 = "uuid4"


class DeployClassName(StrEnum):
    GUNICORN = "gunicorn"
    uWSGI = "uwsgi"


class GlobalState:
    cwd: Path
    conf_file: Path
    env: str | None = None
    force: bool = False
    fabic_config: FabikConfig | None = None
    _config_validators: list[Callable] = []  # 存储自定义验证器函数

    deploy_conn: "Deploy" = None  # type: ignore # noqa: F821

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

    def check_work_dir_or_use_cwd(self) -> Path:
        """如果提供了配置文件，检测 work_dir 并返回。否则使用 cwd 作为 work_dir。"""
        try:
            conf = FabikConfig(self.cwd, cfg=self.conf_file)
            conf.load_root_data()
            work_dir = Path(conf.getcfg("PATH", "work_dir"))
            if not work_dir.is_absolute():
                echo_warning(f"{work_dir} is not a absolute path.")
                raise typer.Exit()
            return work_dir
        except (PathError, ConfigError):
            pass
        return self.cwd

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

    def copy_tpl_file(self, keyname: str, filename: str, rename: bool = False):
        """复制文件到目标文件夹。

        :param rename: 若文件已存在是否重命名
        """
        split_path = keyname.split("/")

        if self.fabic_config is None:
            echo_warning("Please perform GlobalState.load_conf_data first.")
            raise typer.Exit()

        config_validator_tpldir(self.fabic_config)
        # 源文件夹
        srcfiledir = Path(self.fabic_config.getcfg("PATH", "tpl_dir"))
        # 目标文件夹
        dstfiledir = self.cwd
        while len(split_path) > 1:
            # 检测是否拥有中间文件夹，若有就创建它
            dstfiledir = dstfiledir.joinpath(split_path[0])  # type: ignore
            srcfiledir = srcfiledir.joinpath(split_path[0])
            if not dstfiledir.exists():
                dstfiledir.mkdir()
            split_path = split_path[1:]

        srcfile = srcfiledir / filename
        dstfile = dstfiledir / filename  # type: ignore

        if dstfile.exists():
            if self.force:
                shutil.copyfile(srcfile, dstfile)
                echo_info(f"覆盖 [red]{srcfile}[/] 到 [red]{dstfile}[/]")
            elif rename:
                dstbak = dstfile.parent.joinpath(dstfile.name + ".bak")
                if dstbak.exists():
                    echo_warning(
                        f"备份文件 [red]{dstbak}[/] 已存在！请先删除备份文件。"
                    )
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

    def build_deploy_conn(self, deploy_class: type["Deploy"]) -> "Deploy":  # type: ignore  # noqa: F821
        """创建一个远程部署连接。"""
        try:
            # 确保配置已加载
            if self.fabic_config is None:
                self.load_conf_data(check=True)

            # 使用已加载的配置
            replacer = ConfigReplacer(self.conf_data, self.cwd, env_name=self.env)  # type: ignore
            # 从 fabik.toml 配置中获取服务器地址
            fabric_conf = replacer.get_tpl_value("FABRIC", merge=True)
            pye_conf = replacer.get_tpl_value("PYE", merge=True)

            # 确保 fabric_conf 是一个字典
            if (
                not isinstance(fabric_conf, dict)
                or "host" not in fabric_conf
                or "user" not in fabric_conf
            ):
                raise ConfigError(
                    err_type=ValueError(),
                    err_msg="FABRIC configuration must contain 'host' and 'user' parameter",
                )

            if pye_conf is None:
                raise ConfigError(
                    err_type=ValueError(),
                    err_msg="PYE configuration is required",
                )

            d = deploy_class(
                global_state.conf_data,
                global_state.cwd,
                Connection(**fabric_conf),
                global_state.env,
            )
            self.deploy_conn = d
            return d
        except FabikError as e:
            echo_error(e.err_msg)
            raise typer.Abort()
        except Exception as e:
            echo_error(str(e))
            raise typer.Abort()

    def __repr__(self) -> str:
        return f"""{self.__class__.__name__}(
    env={self.env}, 
    cwd={self.cwd!s}, 
    conf_file={self.conf_file!s}, 
    force={self.force}, 
    fabic_config={self.fabic_config!s}
)"""


# 创建全局状态实例并注册默认验证器
global_state = GlobalState()
global_state.register_config_validator(config_validator_name_workdir)


# ==============================================
# functions for command line interface
# ==============================================

NoteRename = Annotated[bool, typer.Option(help="If the target file exists, rename it.")]
NoteForce = Annotated[
    bool, typer.Option("--force", "-f", help="Force to overwrite the existing file.")
]
NoteEnvPostfix = Annotated[
    bool, typer.Option(help="在生成的配置文件名称末尾加上环境名称后缀。")
]
NoteReqirementsFileName = Annotated[
    str, typer.Option(help="指定 requirements.txt 的文件名。")
]


def main_callback(
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
):
    try:
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
    work_dir: Path = global_state.check_work_dir_or_use_cwd()

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
    # 需要检查 tpl_dir 是否存在
    global_state.register_config_validator(config_validator_tpldir)
    global_state.load_conf_data(check=True)
    tpl_dir = Path(global_state.fabic_config.getcfg("PATH", "tpl_dir"))  # type: ignore
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


# -------------------------------------- 子命令 gen
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


# ---------------------------- 子命令 venv
#
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


def venv_update(
    name: Annotated[
        list[str] | None, typer.Argument(help="指定希望更新的 pip 包名称。")
    ] = None,
    init: Annotated[bool, typer.Option(help="是否初始化虚拟环境。")] = False,
    requirements_file_name: NoteReqirementsFileName = "requirements.txt",
):
    """「远程」部署远程服务器的虚拟环境。"""
    if global_state.deploy_conn is None:
        echo_error("部署连接未初始化，请检查 FABRIC 配置")
        raise typer.Abort()
        
    if init:
        # 初始化时先部署项目文件
        try:
            rsync_exclude = global_state.conf_data.get("RSYNC_EXCLUDE", [])
            global_state.deploy_conn.rsync(exclude=rsync_exclude)
            global_state.deploy_conn.init_remote_venv(requirements_file_name)
        except Exception as e:
            echo_error(f"初始化虚拟环境失败: {str(e)}")
            raise typer.Abort()
    
    try:
        if name is not None and len(name) > 0:
            global_state.deploy_conn.pipupgrade(names=name)
        else:
            global_state.deploy_conn.pipupgrade(all=True)
    except Exception as e:
        echo_error(f"更新 pip 包失败: {str(e)}")
        raise typer.Abort()


def venv_outdated():
    """「远程」打印所有的过期的 python package。"""
    global_state.deploy_conn.pipoutdated()  # type: ignore # noqa: F821


# ---------------------------- 子命令 server


def server_deploy():
    """「远程」部署项目到远程服务器。"""
    global_state.deploy_conn.rsync(exclude=global_state.fabic_config.getcfg("RSYNC_EXCLUDE", []))  # type: ignore # noqa: F821
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
