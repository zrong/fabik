""" .. _fabik_cmd:

fabik.cmd
----------------------------

fabik command line toolset
"""

# 从各个子模块导入所有函数
from fabik.cmd import (
    main_callback,
    main_init,
    gen_requirements,
    GlobalState,
    global_state,
    UUIDType,
    DeployClassName,
    NoteRename,
    NoteForce,
    NoteEnvPostfix,
    NoteReqirementsFileName,
)

from fabik.cmd.gen import (
    gen_password,
    gen_fernet_key,
    gen_token,
    gen_uuid,
)

from fabik.cmd.conf import (
    conf_callback,
    conf_tpl,
    conf_make,
)

from fabik.cmd.venv import (
    server_callback,
    venv_init,
    venv_update,
    venv_outdated,
)

from fabik.cmd.server import (
    server_deploy,
    server_start,
    server_stop,
    server_reload,
    server_dar,
)

__all__ = [
    "main_callback",
    "main_init",
    "conf_callback",
    "conf_tpl",
    "conf_make",
    "gen_requirements",
    "gen_password",
    "gen_fernet_key",
    "gen_token",
    "gen_uuid",
    "server_callback",
    "venv_init",
    "venv_update",
    "venv_outdated",
    "server_deploy",
    "server_start",
    "server_stop",
    "server_reload",
    "server_dar",
    "GlobalState",
    "global_state",
    "UUIDType",
    "DeployClassName",
    "NoteRename",
    "NoteForce",
    "NoteEnvPostfix",
    "NoteReqirementsFileName",
]