""" .. _fabik_error:

fabik.error
----------------------

错误处理。
"""

from typing import Any
from rich.console import Console
from rich.style import Style
from rich.panel import Panel

console: Console = Console(highlight=True)

class FabikError(Exception):
    err_type: Exception
    err_msg: str

    def __init__(self, *args: object, err_type: Exception, err_msg: str) -> None:
        super().__init__(*args)
        self.err_type = err_type
        self.err_msg = err_msg

    def __repr__(self) -> str:
        return f'{self.err_type.__class__.__name__} {self.err_msg} {self.args}'
    

class EncryptError(FabikError):
    """ 加密和解密错误。"""
    pass


class ConfigError(FabikError):
    """ 配置文件错误。"""
    pass


class PathError(FabikError):
    """ 路径错误。"""
    pass

class EnvError(FabikError):
    """ 环境设置错误。"""
    pass

class TplError(FabikError):
    """ 环境设置错误。"""
    pass


def echo(value:Any, *, panel_title:str | None=None, style:Style | str | None=None):
    """  调用 console.print 输出信息。"""
    if panel_title:
        value = Panel(value, title=panel_title, title_align='left')
    console.print(value, style=style)
    

def echo_info(value: Any, *, panel_title:str | None=None):
    """ 输出信息。"""
    echo(value, panel_title=panel_title)


def echo_warning(value: Any, *, panel_title:str | None=None):
    """ 输出警告。"""
    echo(value, panel_title=panel_title, style='yellow')


def echo_error(value: Any, *, panel_title:str | None=None):
    """ 输出错误。"""
    echo(value, panel_title=panel_title, style='red')
    