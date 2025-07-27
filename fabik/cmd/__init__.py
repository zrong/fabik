""".. _fabik_cmd:

fabik.cmd
----------------------------

fabik command line toolset
"""

__all__ = [
    "GlobalState",
    "global_state",
    "UUIDType",
    "DeployClassName",
    "NoteRename",
    "NoteForce",
    "NoteEnvPostfix",
    "NoteReqirementsFileName",
]

from enum import StrEnum
import shutil
from pathlib import Path
from typing import Any, Callable

import typer
from typing import Annotated

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
    
    def check_output_file(self, output_file: Path, is_file: bool=True) -> Path:
        """ 检测输出文件或者文件夹是否可写。"""
        # 使用指定的输出文件路径
        file = Path(output_file).resolve().absolute()
        
        if is_file:
            if file.is_dir():
                echo_error(f"{file.absolute().as_posix()} 必须是一个文件。")
                raise typer.Exit()

            # 检查父目录是否存在且可写
            parent_dir = file.parent
            if not parent_dir.exists():
                echo_error(f"目录 {parent_dir.absolute().as_posix()} 不存在。")
                raise typer.Exit()
            
            if not parent_dir.is_dir():
                echo_error(f"{parent_dir.absolute().as_posix()} 不是一个文件夹。")
                raise typer.Exit()
        else:
            if not file.is_dir():
                echo_error(f"{file.absolute().as_posix()} 必须是一个文件夹。")
                raise typer.Exit()
            if not file.exists():
                echo_error(f"{file.absolute().as_posix()} 不存在。")
                raise typer.Exit()
            
        return file

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
NoteOutputFile = Annotated[
    Path | None, typer.Option("--output", "-o", help="指定输出文件的绝对路径。")
]


# 创建全局状态实例并注册默认验证器
global_state = GlobalState()
global_state.register_config_validator(config_validator_name_workdir)
