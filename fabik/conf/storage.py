""".._fabik_conf_storage:

fabik.conf.storage
~~~~~~~~~~~~~~~~~~~~~~~~~

fabik 配置文件读取和存储。
"""

import os
from pathlib import Path
import tomllib
from typing import Any, Union

import typer
from dotenv import dotenv_values

import fabik
from fabik.error import ConfigError, PathError, EnvError, echo_error
from fabik.tpl import FABIK_ENV_FILE, FABIK_TOML_FILE
from fabik.conf import merge_dict


FABIK_DATA: str = "root_data"
FABIK_ENV: str = "env_data"


class FabikConfig:
    """处理 FABIK 配置的值。"""

    __project_name: str
    """ 项目名称。"""

    root_data: dict[str, Any]
    """ 保存 FABIK_TOML_FILE 中载入的配置。"""

    env_data: dict[str, Any]
    """ 存储 FABIK_ENV_FILE 文件中载入的配置。"""
    
    env_name: str = ""
    """ 存储命令行传递的 env 参数。"""
    
    envs: dict[str, dict[str, Any]]| None = None
    

    def __init__(
        self,
        root_data: dict | None = None,
        env_data: dict | None = None,
        env_name: str  = ""
    ):
        """接受配置文件的 值
        :param cfg: 配置文件路径
        """
        self.root_data = root_data or {}
        self.env_data = env_data or {}
        self.env_name = env_name
        
        self._update_root_env_data()
        self.envs = self.root_data.get('ENV', None)
        
    @property
    def NAME(self) -> str:
        """ 配置中的 NAME"""
        return self.__project_name

    @property
    def WORK_DIR(self) -> str | None:
        """ 配置中的 WORK_DIR"""
        return self._get_path_str('WORK_DIR')

    @property
    def TPL_DIR(self) -> str | None:
        """ 配置中的 TPL_DIR"""
        return self._get_path_str('TPL_DIR')
    
    def _update_root_env_data(self):
        """ 将环境配置的 NO_NAME_VAR 值合并到 root_data 中，
        将环境配置的值覆盖同名，环境变量的值覆盖配置的值，保存到 env_data 中。
        NO_NAME_VAR: 不以项目名称值开头的环境变量。
        """
        # 获取项目名称（优先从环境配置获取）
        self.__project_name = self.env_data.get("NAME", self.root_data.get("NAME", fabik.__name__))
        
        # 将NO_NAME_VAR 并入 root_data
        name_prefix = f"{self.__project_name.upper()}_"
        non_name_vars = {
            k: v for k, v in self.env_data.items() if not k.startswith(name_prefix)
        }

        # 合并配置：环境配置覆盖 TOML 配置中的同名键，仅限 NO_NAME_VAR
        self.root_data = merge_dict(self.root_data, non_name_vars)

        # 获取系统环境变量，仅处理以项目名称开头的环境变量
        fabik_env_var_in_os_environ = {
            k: v for k, v in dict(os.environ).items() if k.startswith(name_prefix)
        }
        # 合并配置：  以 env_data 中的值作为基础，env_data 中的值覆盖系统环境变量中的同名值
        self.env_data = merge_dict(fabik_env_var_in_os_environ, self.env_data)

    def _get_path_str(self, var_name: str) -> str | None:
        """ 获取配置中的路径变量的绝对路径字符串形式 """
        # 存入 root_data 中的 NO_NAME_VAR 已经合并过 env_data 中的同名变量了。
        # 因此仅从 root_data 中获取即可
        p = self.root_data.get(var_name)
        if p:
            return Path(p).resolve().as_posix()
        return None

    def get_env_var_name(self, var_name: str) -> str:
        """ 获取 ENV 变量的名称。"""
        env_prefix: str = self.env_name if self.env_name else ""
        return f"{self.NAME.upper()}_{env_prefix.upper()}_{var_name}"

    def check_env_name(self):
        """仅在 env_name 有效时，才会检查 envs 的值。"""
        if self.env_name:
            if not self.envs or not isinstance(self.envs, dict):
                raise EnvError(err_type=TypeError(), err_msg="envs must be a dict.")
            if self.env_name not in self.envs:
                raise EnvError(
                    err_type=KeyError(),
                    err_msg=f"env_name {self.env_name} not found in envs.",
                )

    def get_env_value(self, key: str | None = None, default_value: Any = None) -> Any:
        """获取环境变量中的值。"""
        if self.env_name is None or self.envs is None:
            return default_value
        env_obj = self.envs.get(self.env_name, None)
        if env_obj is None:
            return default_value
        if key is None:
            return env_obj
        return env_obj.get(key, default_value)

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
        elif data == FABIK_ENV:
            data = self.env_data or {}
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
        elif data == FABIK_ENV:
            data = self.env_data or {}
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

    def __repr__(self) -> str:
        return f"""{self.__class__.__name__}
        ({self.__project_name=!s}, 
        {self.env_name=!s},
        {self.envs=!s},
        {self.root_data=!s}, 
        {self.env_data=!s})"""


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

    def load_config(self, env_name: str="") -> FabikConfig:
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

        # 将不以项目名称值开头的环境变量 (NO_NAME_VAR) 并入 root_data
        name_prefix = f"{project_name.upper()}_"  # pyright: ignore[reportOptionalMemberAccess]
        non_name_vars = {
            k: v for k, v in env_data.items() if not k.startswith(name_prefix)
        }

        # 合并配置：环境配置覆盖 TOML 配置中的同名键
        root_data = merge_dict(root_data, non_name_vars)
        return FabikConfig(root_data, env_data, env_name)

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
        ({self.__work_dir=!s}, 
        {self.fabik_toml=!s}, 
        {self.fabik_env=!s})"""


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
