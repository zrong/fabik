""" .._fabik_util:

fabik.util
------------------

封装的小工具。
"""

import hashlib
import base64


def md5txt(txt: str | bytes) -> str:
    """
    计算 MD5 字符串散列
    :param txt:
    :return:
    """
    md5obj = hashlib.md5()
    if isinstance(txt, str):
        txt = txt.encode('utf-8')
    md5obj.update(txt)
    return md5obj.hexdigest()


def md5base64(txt: str | bytes) -> str:
    """md5(base64) 算法
    验证工具： http://www.cmd5.com/hash.aspx
    """
    m = hashlib.md5()
    if isinstance(txt, str):
        txt = txt.encode('utf-8')
    m.update(txt)
    return base64.encodebytes(m.digest())[:-1].decode('utf8')


# 在函数定义之后导入gen，避免循环导入
from . import gen

__all__ = ['md5txt', 'md5base64', 'gen']
