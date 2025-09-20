""".. _fabik_conf:

fabik.conf
~~~~~~~~~~~~~~~~~~~

处理配置文件。
"""

__all__ = [
    "merge_dict",
    "config_validator_tpldir",
    "config_validator_name_workdir",
    "FabikConfig",
    "FabikConfigFile",
    'FABIK_DATA',
    'FABIK_ENV',
    "ConfigWriter",
    "ConfigReplacer",
]


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
        new_value = None
        if isinstance(xv, dict):
            new_value = xv.copy()
            # 对于 dict 执行递归替换
            if isinstance(yv, dict):
                z[xk] = {}
                new_value = merge_dict(new_value, yv, z[xk])
            # 对于 list 直接进行浅复制
            elif isinstance(yv, list):
                new_value = yv.copy()
            # 对于标量值（非 None）则直接替换
            elif yv is not None:
                new_value = yv
        else:
            new_value = xv.copy() if isinstance(xv, list) else xv
            if isinstance(yv, dict) or isinstance(yv, list):
                new_value = yv.copy()
            elif yv is not None:
                new_value = yv
        z[xk] = new_value

    # 将 y 中有但 x 中没有的键加入 z
    for yk, yv in y.items():
        if x.get(yk, None) is None:
            z[yk] = yv
    return z


from .storage import (
    FabikConfig,
    FabikConfigFile,
    FABIK_DATA,
    FABIK_ENV,
    config_validator_tpldir,
    config_validator_name_workdir,
)
from .processor import ConfigWriter, ConfigReplacer
