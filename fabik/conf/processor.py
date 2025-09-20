""".._fabik_conf_processor:

fabik.conf.processor
~~~~~~~~~~~~~~~~~~~~~~~~~

fabik command line interface implementation
"""

import jinja2
from pathlib import Path
from typing import Any
import shutil

import tomllib
import tomli_w
import json

import fabik
from fabik.conf import FABIK_ENV, FabikConfig
from fabik.error import (
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

    fabik_config: FabikConfig

    work_dir: Path
    output_dir: Path | None = None
    tpl_dir: Path | None = None
    deploy_dir: Path  # 不会为 None，总是有默认值
    replace_environ: list[str] | None = None
    verbose: bool = False
    writer: ConfigWriter | None = None

    def __init__(
        self,
        fabik_config: FabikConfig,
        work_dir: Path,
        *,
        output_dir: Path | None = None,
        tpl_dir: Path | None = None,
        verbose: bool = False,
    ):
        """初始化"""
        self.fabik_config = fabik_config
        self.work_dir = work_dir

        self.output_dir = output_dir
        self.tpl_dir = tpl_dir
        self.verbose = verbose

        self.fabik_config.check_env_name()

        self.deploy_dir = Path(self._get_deploy_dir())
        if not self.deploy_dir.is_absolute():
            raise ConfigError(
                err_type=ValueError(),
                err_msg=f"DEPLOY_DIR must be a absolute path! Now is {self.deploy_dir}.",
            )
        self.replace_environ = self.get_tpl_value("REPLACE_ENVIRON", merge=False)

    def _get_deploy_dir(self):
        """获取 DEPLOY_DIR 的 字符串形态"""
        # 处理 DEPLOY_DIR（优先从环境配置获取）
        return self.fabik_config.getcfg(
            "DEPLOY_DIR", f"/srv/app/{self.fabik_config.NAME}"
        )

    def _fill_root_meta(self, replace_obj: dict = {}):
        """向被替换的值，填充 NAME/WORK_DIR/DEPLOY_DIR 变量。"""
        # 直接使用固化的 fabik_name
        replace_obj["NAME"] = self.fabik_config.NAME

        # 优先从环境配置获取 WORK_DIR，否则使用当前工作目录
        work_dir_from_env = self.fabik_config.WORK_DIR
        if work_dir_from_env:
            replace_obj["WORK_DIR"] = Path(work_dir_from_env).resolve().as_posix()
        else:
            replace_obj["WORK_DIR"] = self.work_dir.resolve().as_posix()

        # 优先从环境配置获取 TPL_DIR
        tpl_dir_from_env = self.fabik_config.TPL_DIR
        if tpl_dir_from_env:
            replace_obj["TPL_DIR"] = Path(tpl_dir_from_env).resolve().as_posix()

        replace_obj["DEPLOY_DIR"] = Path(self._get_deploy_dir()).as_posix()
        if self.env_name:
            replace_obj["ENV_NAME"] = self.fabik_config.env_name

        return replace_obj

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
        base_obj = self.fabik_config.getcfg(tpl_name)
        update_obj = self.fabik_config.get_env_value(tpl_name)

        if check_tpl_name and base_obj is None:
            if self.verbose:
                echo_error(
                    f"{merge=} {wrap_key=} {check_tpl_name=} {base_obj=} {update_obj=}",
                    panel_title=f"ConfigReplacer::get_tpl_value({tpl_name=!s}) BEFORE tpl_name NOT FOUND",
                )
            raise ConfigError(
                err_type=TypeError(), err_msg=f"{tpl_name} not found in fabik config."
            )

        # 对于非字典类型，强制不使用合并
        if not isinstance(base_obj, dict) or not isinstance(update_obj, dict):
            merge = False

        if self.verbose:
            echo_info(
                f"{tpl_name=} {merge=} {wrap_key=} {base_obj=} {update_obj=}",
                panel_title=f"ConfigReplacer::get_tpl_value({tpl_name=!s}) BEFORE MERGE",
            )
        if merge:
            repl_obj = merge_dict(base_obj or {}, update_obj or {})
        else:
            repl_obj = update_obj or base_obj

        if self.verbose:
            echo_info(
                f"{tpl_name=} {merge=} {wrap_key=} {base_obj=} {update_obj=} {repl_obj=}",
                panel_title=f"ConfigReplacer::get_tpl_value({tpl_name=!s}) AFTER MERGE",
            )

        return {wrap_key: repl_obj} if wrap_key else repl_obj

    def replace(self, value: str) -> str:
        """替换 value 中的占位符"""
        # 环境变量替换用
        environ_keys = {}
        # 替换 NAME 和 WORK_DIR
        replace_obj = self._fill_root_meta()
        # 获取环境变量中的替换值
        if self.replace_environ is not None:
            for n in self.replace_environ:
                # FABIK_LOCAL_NAME
                env_var_name = self.fabik_config.get_env_var_name(n)
                environ_keys[n] = env_var_name
                environ_value = self.fabik_config.getcfg(env_var_name, data=FABIK_ENV)
                if self.verbose:
                    echo_info(
                        f"""{env_var_name=}\n{environ_value=}""",
                        panel_title=f"LOG: ConfigReplacer::replace() CURRENT REPLACE_ENVIRON {n=!s}",
                    )

                if environ_value is not None:
                    replace_obj[n] = environ_value
        if self.verbose:
            echo_info(
                f"""{environ_keys=}\n{replace_obj=}""",
                panel_title="LOG: ConfigReplacer::replace() AFTER REPLACE_ENVIRON",
            )
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
        if self.verbose:
            echo_info(
                f"{tpl_name=} {force=!s} {rename=!s} {target_postfix=} {output_file=} {immediately}",
                panel_title="ConfigReplacer::set_writer() BEFORE",
            )
        replace_obj = self.get_replace_obj(tpl_name)

        if output_file is not None:
            # 使用指定的文件路径
            final_target = output_file
            target = output_file
        else:
            # 使用 output_dir 逻辑
            output_dir: Path = (
                self.work_dir if self.output_dir is None else self.output_dir
            )
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
