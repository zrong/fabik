"""gen 子命令相关函数"""

import typer
from typing import Annotated
from enum import StrEnum

from fabik import util
from fabik.error import echo_info


class UUIDType(StrEnum):
    UUID1 = "uuid1"
    UUID4 = "uuid4"


def gen_password(
    password: Annotated[str, typer.Argument(help="提供密码。", show_default=False)],
    salt: Annotated[
        str,
        typer.Argument(help="提供密码盐值。", show_default=False),
    ],
):
    """返回加盐之后的 PASSWORD。"""
    echo_info(util.gen.gen_password(password, salt))


def gen_fernet_key():
    """生成一个 SECRET_KEY。"""
    echo_info(util.gen.gen_fernet_key())


def gen_token(length: Annotated[int, typer.Argument(help="字符串位数。")] = 8):
    """根据提供的位数，返回一个 token 字符串。"""
    echo_info(util.gen.gen_token(k=length))


def gen_uuid(
    name: Annotated[UUIDType, typer.Argument(help="UUID 类型。")] = UUIDType.UUID4,
):
    """根据提供的名称，调用 uuid 库返回一个 UUID 字符串，仅支持 uuid1 和 uuid4 两种类型。"""
    echo_info(util.gen.gen_uuid(name.value))