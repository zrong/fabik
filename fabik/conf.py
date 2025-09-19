"""
.. _fabik_conf:

fabik.conf
-------------------

提供配置文件支持
"""

import os
import jinja2
from pathlib import Path
from typing import Any, Union
import shutil

import tomllib
import tomli_w
import json
import typer
from dotenv import dotenv_values

import fabik
from fabik.error import (
    EnvError,
    echo_error,
    echo_info,
    echo_warning,
    FabikError,
    ConfigError,
    PathError,
    TplError,
)
from fabik.tpl import FABIK_TOML_FILE, FABIK_ENV_FILE


FABIK_DATA: str = "root_data"


def merge_dict(x: dict, y: dict, z: dict | None = None) -> dict:
    """合并 x 和 y 两个 dict。

    1. 用 y 的同 key 值覆盖 x 的值。
    2. y 中的新键名 (x 中同级不存在) 增加到 x 中。

    返回一个新的 dict，不修改 x 和 y。

    :param x: x 被 y 覆盖。
    :param y: y 覆盖 x。
    :return: dict
    """
    if z is None:
        z = {}
    # 以 x 的键名为标准，用 y 中包含的 x 键名覆盖 x 中的值
    for xk, xv in x.items():
        yv = y.get(xk, None)
        newv = None
        if isinstance(xv, dict):
            newv = xv.copy()
            # 对于 dict 执行递归替换
            if isinstance(yv, dict):
                z[xk] = {}
                newv = merge_dict(newv, yv, z[xk])
            # 对于 list 直接进行浅复制
            elif isinstance(yv, list):
                newv = yv.copy()
            # 对于标量值（非 None）则直接替换
            elif yv is not None:
                newv = yv
        else:
            newv = xv.copy() if isinstance(xv, list) else xv
            if isinstance(yv, dict) or isinstance(yv, list):
                newv = yv.copy()
            elif yv is not None:
                newv = yv
        z[xk] = newv

    # 将 y 中有但 x 中没有的键加入 z
    for yk, yv in y.items():
        if x.get(yk, None) is None:
            z[yk] = yv
    return z


class FabikConfig:
    """解析和处理 FABIK 配置文件。"""

    root_data: dict[str, Any] | None = None
    """ 保存 FABIK_TOML_FILE 中载入的配置。"""
    
    env_data: dict[str, Any] | None = None
    """ 存储 FABIK_ENV_FILE 文件中的配置。"""

    __work_dir: Path | None = None
    """ 保存工作文件夹所在路径。"""

    fabik_toml: Path | None = None
    """ 保存 FABIK_TOML 文件路径。"""

    fabik_env: Path | None = None
    """ 保存 FABIK_ENV 文件路径。"""

    def __init__(
        self,
        work_dir: Path | str | None = None,
        cfg: dict | Path | str | None = None,
    ):
        """初始化全局文件。

        :param Path work_dir: 工作文件夹
        :param Path cofig_file: 配置文件路径
        :param str|dict cfg: 相对于工作文件夹的配置文件地址，或者配置内容本身
        """
        self.__work_dir = None if work_dir is None else Path(work_dir)

        if isinstance(cfg, dict):
            self.root_data = cfg
        else:
            self.fabik_toml = FabikConfig.gen_fabik_toml(
                work_dir=work_dir, conf_file=cfg
            )

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
    def gen_fabik_toml(
        *, work_dir: Path | str | None = None, conf_file: Path | str | None = None
    ) -> Path:
        """生成 fabik.toml 配置文件路径。"""
        work_dir = FabikConfig.gen_work_dir(work_dir)

        if conf_file is None:
            conf_file = FABIK_TOML_FILE
        if isinstance(conf_file, str):
            conf_file = Path(conf_file)
        if not conf_file.is_absolute():
            conf_file = work_dir.joinpath(conf_file)
        return conf_file.resolve().absolute()

    @property
    def file_exists(self) -> bool:
        """返回配置文件 FABIK_TOML 是否存在。"""
        return self.fabik_toml is not None and self.fabik_toml.exists()

    def load_root_data(self) -> dict[str, Any]:
        """获取主配置文件 duel.toml 并进行简单的检测"""
        if self.root_data is None:
            fabik_toml_file = self.fabik_toml.resolve().absolute() if self.fabik_toml else Path(FABIK_TOML_FILE)
            try:
                if self.fabik_toml is None:
                    raise ConfigError(
                        err_type=FileNotFoundError(),
                        err_msg=f"{FABIK_TOML_FILE} not found.",
                    )
                self.root_data = tomllib.loads(
                    fabik_toml_file.read_text(encoding="utf-8")
                )
            except FileNotFoundError as e:
                raise ConfigError(err_type=e, err_msg=f"{fabik_toml_file} not found.")
            except tomllib.TOMLDecodeError as e:
                raise ConfigError(
                    err_type=e,
                    err_msg=f"Decode {fabik_toml_file} error: {e}",
                )
        return self.root_data

    def merge_root_data(self, data: Union["FabikConfig", dict]) -> dict:
        """使用提供的数据更新 root_data 中的数据，返回的值用于覆盖当前配置文件。"""
        if not self.file_exists:
            raise ConfigError(
                err_type=FileNotFoundError(), err_msg=f"{self.fabik_toml} not found."
            )
        if isinstance(data, dict):
            return merge_dict(data, self.root_data or {})
        return merge_dict(data.root_data or {}, self.root_data or {})

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

    def __repr__(self) -> str:
        return f"""{self.__class__.__name__}
        (work_dir={self.__work_dir!s}, 
        fabik_toml={self.fabik_toml!s}, 
        root_data={self.root_data!s})"""


class ConfigWriter:
    """写入配置文件。"""

    tpl_name: str
    dst_file: Path
    replace_obj: dict
    verbose: bool = False

    def __init__(
        self, tpl_name: str, dst_file: Path, replace_obj: dict, verbose: bool = False
    ) -> None:
        """初始化
        :param tplname: 模版名称，不含扩展名
        :param dstname: 目标名称
        """
        self.tpl_name = tpl_name
        self.dst_file = dst_file
        self.replace_obj = replace_obj
        self.verbose = verbose

    def _write_key_value(self):
        """输出 key = value 形式的文件"""
        txt = "\n".join([f"{k} = {v}" for k, v in self.replace_obj.items()])
        self.dst_file.write_text(txt)
        echo_info(f"文件 {self.dst_file.as_posix()} 创建成功。")

    def _write_file_by_type(self):
        """根据后缀决定如何处理渲染。"""
        if self.tpl_name.endswith(".toml"):
            self.dst_file.write_text(tomli_w.dumps(self.replace_obj))
            echo_info(f"文件 {self.dst_file.as_posix()} 创建成功。")
        elif self.tpl_name == ".env":
            self._write_key_value()
        else:
            # 对于不支持的文件类型，使用 json 格式渲染
            self.dst_file.write_text(
                json.dumps(self.replace_obj, ensure_ascii=False, indent=4)
            )
            echo_info(f"文件 {self.dst_file.as_posix()} 创建成功。")

    def write_file(self, force: bool = True, rename: bool = False):
        """写入配置文件
        :param force: 若 force 为 False，则仅当文件不存在的时候才写入。
        :param rename: 是否重命名原始文件。
        """
        if not self.dst_file.exists():
            self._write_file_by_type()
        elif force:
            if rename:
                bak_file = self.dst_file.parent.joinpath(
                    f"{self.dst_file.name}.bak_{int(fabik.__now__.timestamp())}"
                )
                # 强制覆盖的时候备份原始文件
                shutil.copyfile(self.dst_file, bak_file)
                echo_warning(
                    f"备份文件 {self.dst_file.as_posix()} 到 {bak_file.as_posix()}。"
                )
            self._write_file_by_type()
        else:
            echo_error(
                f"文件 {self.dst_file.as_posix()} 已存在。使用 --force 覆盖，使用 --rename 在覆盖前重命名。"
            )


class TplWriter(ConfigWriter):
    """基于模板文件的配置写入器"""

    tpl_filename: str
    tpl_dir: Path
    tpl_env: jinja2.Environment

    def __init__(
        self,
        tpl_name: str,
        dst_file: Path,
        replace_obj: dict[str, Any],
        tpl_dir: Path,
        verbose: bool = False,
    ) -> None:
        """初始化
        :param tplname: 模版名称，不含扩展名
        :param dstname: 目标名称
        :param tpl_dir: 模板文件目录
        """
        super().__init__(tpl_name, dst_file, replace_obj, verbose)

        # 自动增加 jinja2 后缀，模板文件必须带有 jinja2 后缀。
        self.tpl_filename = (
            tpl_name if tpl_name.endswith(".jinja2") else f"{tpl_name}.jinja2"
        )
        self.tpl_dir = tpl_dir
        self.tpl_env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.tpl_dir))

    def _write_by_jinja(self):
        """能找到模板文件，调用 jinja2 直接渲染。"""
        tpl = self.tpl_env.get_template(self.tpl_filename)
        self.dst_file.write_text(tpl.render(self.replace_obj))
        if self.verbose:
            echo_info(
                f"{self.tpl_filename=}\n{self.dst_file.absolute().as_posix()}\n{self.replace_obj=}",
                panel_title="TplWriter::_write_by_jinja()",
            )
        echo_info(
            f"从模板 {self.tpl_filename} 创建文件 {self.dst_file.as_posix()} 成功。"
        )

    def _write_file_by_type(self):
        """重写父类的方法，仅支持 jinja2 模版渲染。"""
        try:
            self._write_by_jinja()
        except TplError as e:
            raise TplError(
                err_type=e, err_msg=f"模版文件 {self.tpl_filename} 错误： {e!s}"
            )


class ConfigReplacer:
    env_name: str | None = None
    """ 不提供 env_name，就不会读取 ENV 中的值。"""

    envs: dict | None = None
    fabik_name: str
    fabik_conf: dict
    work_dir: Path
    output_dir: Path | None = None
    tpl_dir: Path | None = None
    deploy_dir: Path | None = None
    replace_environ: list[str] | None = None
    verbose: bool = False
    writer: ConfigWriter | None = None

    def __init__(
        self,
        fabik_conf: dict[str, Any],
        work_dir: Path,
        *,
        output_dir: Path | None = None,
        tpl_dir: Path | None = None,
        env_name: str | None = None,
        verbose: bool = False,
    ):
        """初始化"""
        self.fabik_conf = fabik_conf
        self.work_dir = work_dir

        self.output_dir = output_dir
        self.tpl_dir = tpl_dir
        self.env_name = env_name
        self.verbose = verbose

        self.envs = fabik_conf.get("ENV", None)

        self.check_env_name()

        """设置替换用的 key"""
        self.fabik_name = self.fabik_conf.get("NAME", "fabik")
        self.deploy_dir = Path(
            self.fabik_conf.get("DEPLOY_DIR", f"/srv/app/{self.fabik_name}")
        )
        if not self.deploy_dir.is_absolute():
            raise ConfigError(
                err_type=ValueError(),
                err_msg=f"DEPLOY_DIR must be a absolute path! Now is {self.deploy_dir}.",
            )
        self.replace_environ = self.get_tpl_value("REPLACE_ENVIRON", merge=False)

    def _fill_root_meta(self, replace_obj: dict = {}):
        """向被替换的值，填充 NAME/WORK_DIR/DEPLOY_DIR  变量。"""
        replace_obj["NAME"] = self.fabik_name
        replace_obj["WORK_DIR"] = self.work_dir.resolve().as_posix()
        # 增加 {DEPLOY_DIR} 的值进行替换
        if isinstance(self.deploy_dir, Path):
            replace_obj["DEPLOY_DIR"] = self.deploy_dir.as_posix()
        if self.env_name:
            replace_obj["ENV_NAME"] = self.env_name

        return replace_obj

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

    def get_tpl_value(
        self,
        tpl_name: str,
        *,
        merge: bool = True,
        wrap_key: str | None = None,
        check_tpl_name: bool = False,
    ) -> Any:
        """获取配置模版中的值。
        :param tpl_name: 配置模版的键名
        :param merge: 是否合并，对于已知的标量，应该选择不合并
        :param wrap_key: 是否做一个包装。如果提供，则会将提供的值作为 key 名，在最终值之上再包装一层
        :param check_tpl_name: 检测 tpl_name 设置的值是否存在，不存在的话就报错。
        """
        base_obj = self.fabik_conf.get(tpl_name, None)
        update_obj = self.get_env_value(tpl_name)

        if check_tpl_name and base_obj is None:
            raise ConfigError(
                err_type=TypeError(), err_msg=f"{tpl_name} not found in fabik.toml."
            )

        # 对于非字典类型，强制不使用合并
        if not isinstance(base_obj, dict) or not isinstance(update_obj, dict):
            merge = False

        if self.verbose:
            echo_info(
                f"{tpl_name=} {merge=} {wrap_key=} {base_obj=} {update_obj=}",
                panel_title="ConfigReplacer::get_tpl_value BEFORE MERGE",
            )
        if merge:
            repl_obj = merge_dict(base_obj or {}, update_obj or {})
        else:
            repl_obj = update_obj or base_obj

        return {wrap_key: repl_obj} if wrap_key else repl_obj

    def get_environ(self) -> dict[str, str]:
        """从系统环境变量和 .env 文件中获取预设变量的值。
        
        .env 文件中的变量会覆盖环境变量中的同名值。
        返回合并后的环境变量字典。
        """
        # 从系统环境变量开始
        env_values = dict(os.environ)
        
        # 查找 .env 文件
        env_file = self.work_dir / ".env"
        if env_file.exists():
            # 从 .env 文件读取变量，这些变量会覆盖系统环境变量
            dotenv_vars = dotenv_values(env_file)
            # 过滤掉值为 None 的项（dotenv_values 可能返回 None 值）
            dotenv_vars = {k: v for k, v in dotenv_vars.items() if v is not None}
            env_values.update(dotenv_vars)
        
        return env_values

    def replace(self, value: str) -> str:
        """替换 value 中的占位符"""
        # 环境变量替换用
        environ_keys = {}
        # 替换 NAME 和 WORK_DIR
        replace_obj = self._fill_root_meta()
        # 获取环境变量中的替换值
        if self.replace_environ is not None:
            env_values = self.get_environ()
            for n in self.replace_environ:
                # FABIK_LOCAL_NAME
                environ_key = (
                    f"{self.fabik_name.upper()}_{self.env_name.upper()}_{n}"
                    if self.env_name
                    else f"{self.fabik_name.upper()}_{n}"
                )
                environ_keys[n] = environ_key
                environ_value = env_values.get(environ_key)
                if environ_value is not None:
                    replace_obj[n] = environ_value
        try:
            if self.verbose:
                echo_info(
                    f"""{value=}\n{replace_obj=}""",
                    panel_title="LOG: ConfigReplacer::replace()",
                )
            # new_value = value.format_map(replace_obj)
            new_value = jinja2.Template(value).render(replace_obj)
            return new_value
        except KeyError as e:
            # 抛出对应的 environ key 的错误
            error_key = e.args[0]
            raise FabikError(
                e,
                err_type=e,
                err_msg=f"""error_key: {error_key}
{environ_keys=}
{replace_obj=}.""",
            )

    def get_replace_obj(self, tpl_name: str) -> dict:
        """获取已经替换过所有值的对象。"""
        if self.verbose:
            echo_info(
                f"{tpl_name=}",
                panel_title="ConfigReplacer::get_replace_obj() BEFORE",
            )
        replace_obj_before = self.get_tpl_value(tpl_name, check_tpl_name=True)
        replace_str = tomli_w.dumps(replace_obj_before)
        # 将 obj 转换成 toml 字符串，进行一次替换，然后再转换回 obj
        # 采用这样的方法可以不必处理复杂的层级关系
        replace_obj_after = tomllib.loads(self.replace(replace_str))
        # 再填充一次 ROOT META，让文件模板也可以使用 NAME/WORK_DIR/DEPLOY_DIR
        replace_obj_after = self._fill_root_meta(replace_obj_after)
        if self.verbose:
            echo_info(
                f"""{tpl_name=}
            {replace_obj_before=!s}
            {replace_obj_after=!s}""",
                panel_title=f"{self.__class__.__name__}::get_replace_obj() AFTER",
            )
        return replace_obj_after

    def set_writer(
        self,
        tpl_name: str,
        *,
        force: bool = True,
        rename: bool = False,
        target_postfix: str = "",
        output_file: Path | None = None,
        immediately: bool = False,
    ) -> tuple[Path, Path]:
        """写入配置文件。
        :param tpl_name: 配置中的根名称，一般情况下是一个表。
        :param output_file: 可选的具体输出文件路径，如果提供则优先使用
        """
        replace_obj = self.get_replace_obj(tpl_name)
        
        if output_file is not None:
            # 使用指定的文件路径
            final_target = output_file
            target = output_file
        else:
            # 使用 output_dir 逻辑
            output_dir: Path = self.work_dir if self.output_dir is None else self.output_dir
            # 不加后缀的文件路径
            target = output_dir.joinpath(tpl_name)
            # 加入后缀的文件路径，大部分情况下与 target 相同
            final_target = output_dir.joinpath(f"{tpl_name}{target_postfix}")

        # 基于是否提供了 tpl_dir 决定使用哪种写入器
        self.writer = (
            ConfigWriter(tpl_name, final_target, replace_obj, self.verbose)
            if self.tpl_dir is None
            else TplWriter(
                tpl_name, final_target, replace_obj, self.tpl_dir, self.verbose
            )
        )

        if immediately:
            self.writer.write_file(force, rename)
        return target, final_target



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


# 默认验证器函数
def config_validator_name_workdir(config: FabikConfig) -> bool:
    """检查 NAME 和 work_dir 是否存在，支持嵌套 key。"""
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
