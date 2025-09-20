""".._fabik_conf_storage:

fabik.conf.storage
~~~~~~~~~~~~~~~~~~~~~~~~~

fabik 配置文件读取和存储。
"""

from pathlib import Path
import tomllib
from typing import Any, Union

import typer
from dotenv import dotenv_values

import fabik
from fabik.error import ConfigError, PathError, echo_error
from fabik.tpl import FABIK_ENV_FILE, FABIK_TOML_FILE
from fabik.conf import merge_dict


FABIK_DATA: str = "root_data"


class FabikConfig:
    """处理 FABIK 配置的值。"""

    root_data: dict[str, Any] | None = None
    """ 保存 FABIK_TOML_FILE 中载入的配置。"""

    env_data: dict[str, Any] | None = None
    """ 存储 FABIK_ENV_FILE 文件中的配置。"""

    def __init__(
        self,
        root_data: dict | None = None,
        env_data: dict | None = None,
    ):
        """接受配置文件的 值
        :param cfg: 配置文件路径
        """
        self.root_data = root_data or {}
        self.env_data = env_data or {}

    def getcfg(
        self, *args, default_value: Any = None, data: str | dict = FABIK_DATA
    ) -> Any:
        """递归获取 conf 中的值。getcfg 不仅可用于读取 config.toml 的值，还可以通过传递 data 用于读取任何字典的值。

        :param args: 需要读取的参数，支持多级调用，若级不存在，不会报错。
        :param default_value: 找不到这个键就提供一个默认值。
        :param data: 提供一个 dict，否则使用 cfg_data。
        :return: 获取的配置值
        """
        if data == FABIK_DATA:
            data = self.root_data or {}
        if args and isinstance(data, dict):
            cur_data = data.get(args[0], default_value)
            return self.getcfg(*args[1:], default_value=default_value, data=cur_data)
        return data

    def setcfg(self, *args, value: Any, data: str | dict = FABIK_DATA) -> None:
        """递归设置 conf 中的值。setcfg 不仅可用于设置 config.toml 的值，还可以通过传递 data 用于读取任何字典的值。

        :param args: 需要设置的参数，支持多级调用，若级不存在，会自动创建一个内缪的 dict。
        :param data: 提供一个 dict，否则使用 cfg_data。
        :param value: 需要设置的值。
        """
        if data == FABIK_DATA:
            data = self.root_data or {}
        if args and isinstance(data, dict):
            arg0 = args[0]
            if len(args) > 1:
                cur_data = data.get(arg0)
                if cur_data is None:
                    cur_data = {}
                    data[arg0] = cur_data
                self.setcfg(*args[1:], value=value, data=cur_data)
            else:
                data[arg0] = value


class FabikConfigFile:
    """解析 FABIK 配置文件，管理 work_dir。"""

    __work_dir: Path
    """ 保存工作文件夹所在路径。"""

    fabik_toml: Path
    """ 保存 FABIK_TOML 文件路径。"""

    fabik_env: Path
    """ 保存 FABIK_ENV 文件路径。"""

    def __init__(self, work_dir: Path, fabik_toml: Path, fabik_env: Path):
        """初始化全局文件。
        :param Path work_dir: 工作文件夹
        :param Path fabik_toml: 主配置文件路径
        :param Path fabik_env: 环境配置文件路径
        """
        self.__work_dir = work_dir
        self.fabik_toml = fabik_toml
        self.fabik_env = fabik_env

        for p in [self.__work_dir, self.fabik_toml, self.fabik_env]:
            if p is None or not isinstance(p, Path) or not p.is_absolute():
                echo_error(
                    "The Path must be a absolute path!",
                )
                raise typer.Exit()

    @staticmethod
    def gen_work_dir(work_dir: Path | str | None = None) -> Path:
        """生成工作文件夹。"""
        work_dir = Path.cwd() if work_dir is None else Path(work_dir)
        if not work_dir.is_absolute():
            raise PathError(
                err_type=ValueError(), err_msg=f"{work_dir} is not a absolute path."
            )
        return work_dir

    @staticmethod
    def gen_fabik_config_file(
        *, work_dir: Path | str | None = None, config_file: Path | str | None = None
    ) -> "FabikConfigFile":
        """根据提供的路径，生成一个 FabikConfigFile 配置文件对象，包含主配置文件和环境配置文件。"""
        work_dir = FabikConfigFile.gen_work_dir(work_dir)

        # 生成 fabik.toml 的路径
        fabik_toml = config_file or FABIK_TOML_FILE
        if isinstance(fabik_toml, str):
            fabik_toml = Path(fabik_toml)
        if not fabik_toml.is_absolute():
            fabik_toml = work_dir.joinpath(fabik_toml)

        # 生成 .fabik.env 的路径
        fabik_env = work_dir.joinpath(FABIK_ENV_FILE)

        return FabikConfigFile(work_dir, fabik_toml, fabik_env)

    @property
    def file_exists(self) -> bool:
        """返回配置文件 FABIK_TOML 是否存在。"""
        return self.fabik_toml.exists() and self.fabik_env.exists()

    def load_config(self) -> FabikConfig:
        """获取主配置文件并合并环境配置"""
        # 检查两个文件必须同时存在
        if not self.file_exists:
            missing_files = [
                f for f in [self.fabik_toml, self.fabik_env] if not f.exists()
            ]
            raise ConfigError(
                err_type=FileNotFoundError(),
                err_msg=f"Required config files not found: {missing_files!s}",
            )

        root_data = {}
        env_data = {}
        try:
            root_data = tomllib.loads(self.fabik_toml.read_text(encoding="utf-8"))
        except FileNotFoundError as e:
            raise ConfigError(err_type=e, err_msg=f"{self.fabik_toml} not found.")
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(
                err_type=e,
                err_msg=f"Decode {self.fabik_toml} error: {e}",
            )

        try:
            # 使用 dotenv_values 读取 .env 格式文件
            env_data = dotenv_values(self.fabik_env) or {}
            # 过滤掉 None 值
            env_data = {k: v for k, v in env_data.items() if v is not None}
        except Exception as e:
            raise ConfigError(
                err_type=e,
                err_msg=f"Load {self.fabik_env} error: {e}",
            )

        # 获取项目名称（优先从环境配置获取）
        project_name = env_data.get("NAME", root_data.get("NAME", fabik.__name__))

        # 将不以项目名称值开头的环境变量并入 root_data
        name_prefix = f"{project_name.upper()}_"  # pyright: ignore[reportOptionalMemberAccess]
        non_name_vars = {
            k: v for k, v in env_data.items() if not k.startswith(name_prefix)
        }

        # 合并配置：环境配置覆盖 TOML 配置中的同名键
        root_data = merge_dict(root_data, non_name_vars)
        return FabikConfig(root_data, env_data)

    def getdir(self, *args, work_dir: Path | None = None) -> Path:
        """基于当前项目的运行文件夹，返回一个 pathlib.Path 对象
        如果传递 basedir，就基于这个 basedir 创建路径

        :param args: 传递路径
        :param Path work_dir: 工作文件夹
        """
        if work_dir is not None:
            return Path(work_dir, *args)
        if self.__work_dir is None:
            raise PathError(err_type=ValueError(), err_msg="Please set work_dir first!")
        return Path(self.__work_dir, *args)

    def __repr__(self) -> str:
        return f"""{self.__class__.__name__}
        (work_dir={self.__work_dir!s}, 
        fabik_toml={self.fabik_toml!s}, 
        fabik_env={self.fabik_env!s})"""


def check_none(value: Any, key_list: list[str]) -> Any:
    if value is None:
        echo_error(f'Key "{key_list!s}" not found in config.')
        raise typer.Abort()
    return value


def check_path_exists(p: Path) -> bool:
    if not p.is_absolute():
        echo_error(f"{p!s} is not a absolute path.")
        raise typer.Exit()
    if not p.exists():
        echo_error(f"{p!s} is not a exists path.")
        raise typer.Exit()
    return True


def config_validator_name_workdir(config: FabikConfig) -> bool:
    """检查 NAME 和 WORK_DIR 是否存在，支持嵌套 key。"""
    keys = (["NAME"], ["WORK_DIR"])
    for key_list in keys:
        value = check_none(config.getcfg(*key_list), key_list)
        if key_list[-1] == "WORK_DIR":
            check_path_exists(Path(value))
    return True


def config_validator_tpldir(config: FabikConfig) -> bool:
    """默认的配置验证逻辑，检查必要的配置项是否存在"""
    key_list = ["TPL_DIR"]
    value = check_none(config.getcfg(*key_list), key_list)
    check_path_exists(Path(value))
    return True
