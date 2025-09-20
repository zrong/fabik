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
    "NoteRequirementsFileName",
    "NoteOutputDir",
    "NoteOutputFile",
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
    FabikConfigFile,
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
    """ 当前工作目录。"""

    fabik_file: FabikConfigFile
    """ fabik 配置文件对象。"""

    env: str | None = None
    """ env 环境，默认为空，不指定环境时，会使用 WORK_DIR 中的默认环境。"""

    force: bool = False
    """ 强制覆盖存在的文件。 """

    rename: bool = False
    """ 是否重命名目标文件。 """

    env_postfix: bool = False
    """ 输出文件是否可包含 env 后缀。 """

    verbose: bool = False
    """ 启用详细日志。 """

    output_dir: Path | None = None
    output_file: Path | None = None
    fabik_config: FabikConfig | None = None
    _config_validators: list[Callable] = []  # 存储自定义验证器函数

    deploy_conn: "Deploy" = None  # type: ignore # noqa: F821
    
    @property
    def conf_data(self) -> dict[str, Any]:
        if self.fabik_config is None:
            return {}
        return self.fabik_config.root_data or {}

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
        if not self.fabik_config:
            return False

        # 运行所有注册的验证器
        for validator in self._config_validators:
            try:
                if not validator(self.fabik_config):
                    return False
            except Exception as e:
                echo_error(f"Config validation error: {str(e)}")
                raise typer.Abort()

        return True

    def use_work_dir_or_cwd(self) -> Path:
        """如果提供了配置文件，检测 work_dir 并返回。否则使用 cwd 作为 work_dir。"""
        try:

            self.load_conf_data(False)
            work_dir_str = self.fabik_config.getcfg("WORK_DIR") if self.fabik_config else None
            work_dir = Path(work_dir_str) if work_dir_str is not None else self.cwd
            if not work_dir.is_absolute():
                echo_warning(f"{work_dir} is not a absolute path.")
                raise typer.Exit()
            return work_dir
        except (PathError, ConfigError):
            # 其他错误直接使用 self.cwd 作为 work_dir
            pass
        return self.cwd

    def check_output(self, output: Path, is_file: bool = True) -> Path:
        """检测输出文件或者文件夹是否可写。"""
        # 使用指定的输出文件路径
        if not output.is_absolute():
            work_dir = self.use_work_dir_or_cwd()
            output = work_dir / output
            
        if is_file:
            if output.is_dir():
                raise typer.BadParameter(f"{output.absolute().as_posix()} 必须是一个文件。")

            # 检查父目录是否存在且可写
            parent_dir = output.parent
            if not parent_dir.exists():
                raise typer.BadParameter(f"目录 {parent_dir.absolute().as_posix()} 不存在。")

            if not parent_dir.is_dir():
                raise typer.BadParameter(f"{parent_dir.absolute().as_posix()} 不是一个文件夹。")
        else:
            if not output.is_dir():
                raise typer.BadParameter(f"{output.absolute().as_posix()} 必须是一个文件夹。")
            if not output.exists():
                raise typer.BadParameter(f"{output.absolute().as_posix()} 不存在。")

        return output

    def load_conf_data(
        self,
        check: bool = False,
        file_not_found_err_msg: str = 'Please call "fabik init" to generate a "fabik.toml" file.',
    ) -> dict[str, Any]:
        try:
            self.fabik_config = self.fabik_file.load_config()
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
            # 处理参数优先级和路径验证
            output_dir, output_file = self._resolve_output_parameters()
            
            if self.verbose:
                echo_info(
                    f"""{self.conf_data=}
                {self.cwd=!s}
                {output_dir=!s}
                {output_file=!s}
                {self.env=!s}
                {tpl_name=!s}
                {tpl_dir=!s}""",
                    panel_title="GlobalState::write_config_file()",
                )
            
            # 创建 ConfigReplacer，根据情况使用 output_dir
            # 获取环境数据
            env_data = self.fabik_config.env_data or {} if self.fabik_config else {}
            
            replacer = ConfigReplacer(
                self.conf_data,      # fabik_conf_data
                env_data,            # fabik_env_data (新增参数)
                self.cwd,
                output_dir=output_dir,
                tpl_dir=tpl_dir,
                env_name=self.env,
                verbose=self.verbose,
            )
            
            # 调用统一的 set_writer 方法，根据情况传递 output_file
            if output_file is not None:
                # 处理 output_file 的路径解析
                resolved_output_file = self._resolve_output_file_target(output_file, target_postfix)
                target, final_target = replacer.set_writer(
                    tpl_name,
                    force=self.force,
                    rename=self.rename,
                    output_file=resolved_output_file,
                    immediately=True,
                )
            else:
                # 使用原有的 output_dir 逻辑
                target, final_target = replacer.set_writer(
                    tpl_name,
                    force=self.force,
                    rename=self.rename,
                    target_postfix=target_postfix,
                    immediately=True,
                )

        except FabikError as e:
            echo_error(e.err_msg)
            raise typer.Abort()
        except Exception as e:
            echo_error(str(e))
            raise typer.Abort()
    
    def _resolve_output_parameters(self) -> tuple[Path | None, Path | None]:
        """解析输出参数的优先级和路径验证
        
        :return: (resolved_output_dir, resolved_output_file)
        """
        # 处理参数优先级：--output-file 优先于 --output-dir
        if self.output_file is not None:
            # 使用 --output-file 参数
            if self.output_dir is not None:
                # 显示警告：同时提供了两个参数
                echo_warning("Both --output-file and --output-dir provided. --output-dir will be ignored.")
            
            return None, self.output_file
        elif self.output_dir is not None:
            # 使用 --output-dir 参数，需要验证路径
            if not self.output_dir.is_absolute():
                resolved_output_dir = self.check_output(self.output_dir, is_file=False)
            else:
                resolved_output_dir = self.output_dir
            return resolved_output_dir, None
        else:
            # 都未提供，使用默认
            return None, None
    
    def _resolve_output_file_target(self, output_file: Path, target_postfix: str) -> Path:
        """解析输出文件的目标路径
        
        :param output_file: 输出文件路径
        :param target_postfix: 配置文件的后缀
        :return: 解析后的输出文件路径
        """
        if not output_file.is_absolute():
            resolved_output_file = self.check_output(output_file, is_file=True)
        else:
            resolved_output_file = output_file
        
        if self.env_postfix and self.env:
            resolved_output_file = resolved_output_file.with_name(
                resolved_output_file.stem + f"-{self.env}" + resolved_output_file.suffix
            )
        
        if target_postfix:
            resolved_output_file = resolved_output_file.with_name(
                resolved_output_file.stem + target_postfix + resolved_output_file.suffix
            )
        
        return resolved_output_file

    def copy_tpl_file(self, keyname: str, filename: str, rename: bool = False):
        """复制文件到目标文件夹。

        :param rename: 若文件已存在是否重命名
        """
        split_path = keyname.split("/")

        if self.fabik_config is None:
            echo_warning("Please perform GlobalState.load_conf_data first.")
            raise typer.Exit()

        config_validator_tpldir(self.fabik_config)
        # 源文件夹
        srcfiledir = Path(self.fabik_config.getcfg("TPL_DIR"))
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
            if self.fabik_config is None:
                self.load_conf_data(check=True)

            # 使用已加载的配置
            # 获取环境数据
            env_data = self.fabik_config.env_data or {} if self.fabik_config else {}
            
            replacer = ConfigReplacer(
                self.conf_data,      # fabik_conf_data
                env_data,            # fabik_env_data (新增参数)
                self.cwd, 
                env_name=self.env, 
                verbose=self.verbose
            )
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
                self.conf_data,
                self.cwd,
                Connection(**fabric_conf),
                self.env,
                self.verbose,
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
    conf_file={self.fabik_file!s}, 
    force={self.force}, 
    fabik_config={self.fabik_config!s}
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
NoteRequirementsFileName = Annotated[
    str, typer.Option(help="指定 requirements.txt 的文件名。")
]
NoteOutputDir = Annotated[
    Path | None,
    typer.Option(
        "--output-dir",
        "--output",  # 保留旧参数作为别名
        "-o",
        help="Output to the specified directory.",
    ),
]

NoteOutputFile = Annotated[
    Path | None,
    typer.Option(
        "--output-file",
        help="Output to the specified file path (overrides --output-dir).",
    ),
]


# 创建全局状态实例并注册默认验证器
global_state = GlobalState()
global_state.register_config_validator(config_validator_name_workdir)
