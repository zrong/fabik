"""
.. _fabik_logging:

fabik.logging
-------------------

提供 logging 支持
"""

import sys
import logging
from logging.handlers import WatchedFileHandler
from logging import StreamHandler, Formatter
from pathlib import Path

TEXT_LOG_FORMAT = """
[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s [%(pathname)s:%(lineno)d]:
%(threadName)s:%(processName)s:%(created)s
%(message)s"""


def _create_file_handler(target, filename, chmod=False):
    """创建一个基于文件的 log handler
    :param target: 一个 Path 对象，或者一个 path 字符串
    """
    logsdir = None
    if isinstance(target, Path):
        logsdir = target
    else:
        logsdir = Path(target)
    # 如果是创建文件夹，权限就是 777，如果文件夹存在，又没有调用 chmod，则使用原来的权限
    # 创建或者设置 logs 文件夹的权限，让其他 user 也可以写入（例如nginx）
    # 注意，要设置 777 权限，需要使用 0o40777 或者先设置 os.umask(0)
    # 0o40777 是根据 os.stat() 获取到的 st_mode 得到的
    if not logsdir.exists():
        logsdir.mkdir(mode=0o40777)
    if chmod:
        logsdir.chmod(0o40777)
    logfile = logsdir.joinpath(filename + '.log')
    if not logfile.exists():
        logfile.touch()
    # 使用 WatchedFileHandler 在文件改变的时候自动打开新的流，配合 logrotate 使用
    return WatchedFileHandler(logfile, encoding='utf8')


def get_logger(
    name: str,
    target: Path | str,
    type_: str = 'file',
    fmt: str = 'text',
    level: int = logging.INFO,
):
    """基于 target 创建一个 logger

    :param name: logger 的名称，不要带扩展名
    :param target: 项目主目录的的 path 字符串或者 Path 对象，
        也可以是 tcp://127.0.0.1:8334 这样的地址
    :param type_: stream/file/zmq/pyzog 若使用 pyzog ，
        则调用 get_pyzog_handler，fmt 参数必须为 config_dict
    :param fmt: ``text/json/config_dict``
        如果 ``type_`` 参数为 pyzog，则必须为 ``config_dict``
    :param level: logging 的 level 级别
    :return: 一个 Logger 对象
    """
    hdr = None
    formatter: Formatter | None = None

    if type_ == 'file':
        hdr = _create_file_handler(target, name)
    else:
        hdr = StreamHandler(sys.stdout)
    if fmt == 'raw':
        formatter = Formatter()
    elif fmt == 'default':
        formatter = Formatter(TEXT_LOG_FORMAT)
    else:
        formatter = Formatter(fmt)

    hdr.setLevel(level)
    hdr.setFormatter(formatter)

    log_ = logging.getLogger(name)
    log_.addHandler(hdr)
    log_.setLevel(level)
    return log_
