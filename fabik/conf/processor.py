"""  .._fabik_conf_processor:

fabik.conf.processor
~~~~~~~~~~~~~~~~~~~~~~~~~
    
fabik command line interface implementation
"""

import os
import jinja2
from pathlib import Path
from typing import Any
import shutil

import tomllib
import tomli_w
import json
from dotenv import dotenv_values

import fabik
from fabik.error import (
    EnvError,
    echo_error,
    echo_info,
    echo_warning,
    FabikError,
    ConfigError,
    TplError,
)
from fabik.conf import merge_dict


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
    fabik_name: str  # 在初始化时固化
    fabik_conf_data: dict  # 重命名的属性
    fabik_env_data: dict   # 新增的环境数据属性
    work_dir: Path
    output_dir: Path | None = None
    tpl_dir: Path | None = None
    deploy_dir: Path  # 不会为 None，总是有默认值
    replace_environ: list[str] | None = None
    verbose: bool = False
    writer: ConfigWriter | None = None

    def __init__(
        self,
        fabik_conf_data: dict[str, Any],
        fabik_env_data: dict[str, Any],  # 新增参数
        work_dir: Path,
        *,
        output_dir: Path | None = None,
        tpl_dir: Path | None = None,
        env_name: str | None = None,
        verbose: bool = False,
    ):
        """初始化"""
        self.fabik_conf_data = fabik_conf_data
        self.fabik_env_data = fabik_env_data  # 新增
        self.work_dir = work_dir

        self.output_dir = output_dir
        self.tpl_dir = tpl_dir
        self.env_name = env_name
        self.verbose = verbose

        # 合并配置数据用于获取 ENV 等配置
        merged_conf = merge_dict(fabik_conf_data, fabik_env_data)
        self.envs = merged_conf.get("ENV", None)

        self.check_env_name()

        """设置替换用的 key"""
        # 固化 fabik_name：优先从环境配置获取，然后从 TOML 配置获取
        self.fabik_name = (
            fabik_env_data.get("NAME") or 
            fabik_conf_data.get("NAME") or 
            "fabik"
        )
        
        # 使用合并后的配置获取 DEPLOY_DIR
        self.deploy_dir = Path(
            merged_conf.get("DEPLOY_DIR", f"/srv/app/{self.fabik_name}")
        )
        if not self.deploy_dir.is_absolute():
            raise ConfigError(
                err_type=ValueError(),
                err_msg=f"DEPLOY_DIR must be a absolute path! Now is {self.deploy_dir}.",
            )
        self.replace_environ = self.get_tpl_value("REPLACE_ENVIRON", merge=False)

    def _fill_root_meta(self, replace_obj: dict = {}):
        """向被替换的值，填充 NAME/WORK_DIR/DEPLOY_DIR 变量。"""
        # 直接使用固化的 fabik_name
        replace_obj["NAME"] = self.fabik_name
        
        # 优先从环境配置获取 WORK_DIR，否则使用当前工作目录
        work_dir_from_env = self.fabik_env_data.get("WORK_DIR")
        if work_dir_from_env:
            replace_obj["WORK_DIR"] = Path(work_dir_from_env).resolve().as_posix()
        else:
            replace_obj["WORK_DIR"] = self.work_dir.resolve().as_posix()
        
        # 优先从环境配置获取 TPL_DIR
        tpl_dir_from_env = self.fabik_env_data.get("TPL_DIR")
        if tpl_dir_from_env:
            replace_obj["TPL_DIR"] = Path(tpl_dir_from_env).resolve().as_posix()
        
        # 处理 DEPLOY_DIR（优先从环境配置获取）
        deploy_dir = (
            self.fabik_env_data.get("DEPLOY_DIR") or
            self.fabik_conf_data.get("DEPLOY_DIR") or
            f"/srv/app/{self.fabik_name}"
        )
        if isinstance(deploy_dir, str):
            deploy_dir = Path(deploy_dir)
        if isinstance(deploy_dir, Path):
            replace_obj["DEPLOY_DIR"] = deploy_dir.as_posix()
        
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
        base_obj = self.fabik_conf_data.get(tpl_name, None)
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


