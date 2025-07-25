"""
pyape.builder.fabric
~~~~~~~~~~~~~~~~~~~

封装 fabric 的功能，提供远程部署能力。
"""

import re
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

from invoke import runners
from fabric.connection import Connection
from invoke.exceptions import Exit

from fabik.conf import ConfigReplacer
from fabik.error import FabikError, echo_error

logger = logging.Logger('fabric', level=logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def rsync(
    c,
    source: str,
    target: str,
    exclude=(),
    delete: bool=False,
    strict_host_keys: bool=True,
    rsync_opts: str="",
    ssh_opts: str="",
):
    """
    Convenient wrapper around your friendly local ``rsync``.

    https://github.com/fabric/patchwork/blob/master/patchwork/transfers.py

    Specifically, it calls your local ``rsync`` program via a subprocess, and
    fills in its arguments with Fabric's current target host/user/port. It
    provides Python level keyword arguments for some common rsync options, and
    allows you to specify custom options via a string if required (see below.)

    For details on how ``rsync`` works, please see its manpage. ``rsync`` must
    be installed on both the invoking system and the target in order for this
    function to work correctly.

    .. note::
        This function transparently honors the given
        `~fabric.connection.Connection`'s connection parameters such as port
        number and SSH key path.

    .. note::
        For reference, the approximate ``rsync`` command-line call that is
        constructed by this function is the following::

            rsync [--delete] [--exclude exclude[0][, --exclude[1][, ...]]] \\
                -pthrvz [rsync_opts] <source> <host_string>:<target>

    :param c:
        `~fabric.connection.Connection` object upon which to operate.
    :param str source:
        The local path to copy from. Actually a string passed verbatim to
        ``rsync``, and thus may be a single directory (``"my_directory"``) or
        multiple directories (``"dir1 dir2"``). See the ``rsync`` documentation
        for details.
    :param str target:
        The path to sync with on the remote end. Due to how ``rsync`` is
        implemented, the exact behavior depends on the value of ``source``:

        - If ``source`` ends with a trailing slash, the files will be dropped
          inside of ``target``. E.g. ``rsync(c, "foldername/",
          "/home/username/project")`` will drop the contents of ``foldername``
          inside of ``/home/username/project``.
        - If ``source`` does **not** end with a trailing slash, ``target`` is
          effectively the "parent" directory, and a new directory named after
          ``source`` will be created inside of it. So ``rsync(c, "foldername",
          "/home/username")`` would create a new directory
          ``/home/username/foldername`` (if needed) and place the files there.

    :param exclude:
        Optional, may be a single string or an iterable of strings, and is
        used to pass one or more ``--exclude`` options to ``rsync``.
    :param bool delete:
        A boolean controlling whether ``rsync``'s ``--delete`` option is used.
        If True, instructs ``rsync`` to remove remote files that no longer
        exist locally. Defaults to False.
    :param bool strict_host_keys:
        Boolean determining whether to enable/disable the SSH-level option
        ``StrictHostKeyChecking`` (useful for frequently-changing hosts such as
        virtual machines or cloud instances.) Defaults to True.
    :param str rsync_opts:
        An optional, arbitrary string which you may use to pass custom
        arguments or options to ``rsync``.
    :param str ssh_opts:
        Like ``rsync_opts`` but specifically for the SSH options string
        (rsync's ``--rsh`` flag.)
    """
    # Turn single-string exclude into a one-item list for consistency
    if isinstance(exclude, str):
        exclude = [exclude]
    # Create --exclude options from exclude list
    exclude_opts = ' --exclude "{}"' * len(exclude)
    # Double-backslash-escape
    exclusions = tuple([str(s).replace('"', '\\\\"') for s in exclude])
    # Honor SSH key(s)
    key_string = ""
    # TODO: seems plausible we need to look in multiple places if there's too
    # much deferred evaluation going on in how we eg source SSH config files
    # and so forth, re: connect_kwargs
    # TODO: we could get VERY fancy here by eg generating a tempfile from any
    # in-memory-only keys...but that's also arguably a security risk, so...
    keys = c.connect_kwargs.get("key_filename", [])
    # TODO: would definitely be nice for Connection/FabricConfig to expose an
    # always-a-list, always-up-to-date-from-all-sources attribute to save us
    # from having to do this sort of thing. (may want to wait for Paramiko auth
    # overhaul tho!)
    if isinstance(keys, str):
        keys = [keys]
    if keys:
        key_string = "-i " + " -i ".join(keys)
    # Get base cxn params
    user, host, port = c.user, c.host, c.port
    port_string = f"-p {port}"
    # Remote shell (SSH) options
    rsh_string = ""
    # Strict host key checking
    disable_keys = "-o StrictHostKeyChecking=no"
    if not strict_host_keys and disable_keys not in ssh_opts:
        ssh_opts += f" {disable_keys}"
    rsh_parts = [key_string, port_string, ssh_opts]
    if any(rsh_parts):
        rsh_string = "--rsh='ssh {}'".format(" ".join(rsh_parts))
    # Set up options part of string
    options_map = {
        "delete": "--delete" if delete else "",
        "exclude": exclude_opts.format(*exclusions),
        "rsh": rsh_string,
        "extra": rsync_opts,
    }
    options = "{delete}{exclude} -pthrvz {extra} {rsh}".format(**options_map)
    # Create and run final command string
    # TODO: richer host object exposing stuff like .address_is_ipv6 or whatever
    if host.count(":") > 1:
        # Square brackets are mandatory for IPv6 rsync address,
        # even if port number is not specified
        cmd = "rsync {} {} [{}@{}]:{}"
    else:
        cmd = "rsync {} {} {}@{}:{}"
    cmd = cmd.format(options, source, user, host, target)
    return c.local(cmd)


class Deploy(object):
    fabik_conf: dict
    work_dir: Path
    conn: Connection
    env_name: str | None = None
    pye: str
    replacer: ConfigReplacer

    def __init__(self, fabik_conf: dict, work_dir: Path, conn: Connection, env_name: str | None=None):
        """ 初始化
        """
        self.env_name = env_name
        self.fabik_conf = fabik_conf
        self.conn = conn
        self.work_dir = Path(work_dir)
        self.pye = fabik_conf['PYE']
        self.replacer = ConfigReplacer(fabik_conf, self.work_dir, env_name=env_name)
        self.replacer.check_env_name()

    def check_remote_conn(self):
        """ 确保当前提供的 conn 是远程版本
        """
        if not isinstance(self.conn, Connection):
            raise Exit('Use -H to provide a host!')

    def get_remote_path(self, *args) -> str:
        return self.replacer.deploy_dir.joinpath(*args).as_posix()

    def remote_exists(self, file):
        """ 是否存在远程文件 file
        """
        self.check_remote_conn()
        # files.exists 仅接受字符串
        if isinstance(file, Path):
            file = file.resolve().as_posix()
        command = f'test -e "$(echo {file})"'
        logger.info(f'{command=}')
        return self.conn.run(command, hide=True, warn=True).ok

    def make_remote_dir(self, *args):
        """ 创建部署文件夹
        """
        self.check_remote_conn()
        remotedir = self.get_remote_path(*args)
        if not self.remote_exists(remotedir):
            command = 'mkdir %s' % remotedir
            logger.info('创建远程文件夹 %s', command)
            self.conn.run(command)

    def cat_remote_file(self, *args):
        """ 使用 cat 命令获取远程文件的内容
        """
        f = self.get_remote_path(*args)
        logger.info('cat_remote_file %s', f)
        if not self.remote_exists(f):
            return None
        result = self.conn.run('cat ' + f, warn=False, hide=True)
        return result.stdout

    def get_remote_pid(self, host=None, port=None):
        """ 利用命令行查找某个端口运行进程的 pid
        :param host: IP 地址
        :param port: 端口号
        """
        self.check_remote_conn()
        address = None
        if host:
            address = host
        if port:
            p = ':' + str(port)
            if address:
                address += '@' + p
            else:
                address = p
        if not address:
            raise Exit('需要 host 或 port 配置。')
        # command = 'lsof -i :2004 | tail -1'
        command_fmt = 'lsof -i {} | tail -1'
        command = command_fmt.format(address)
        result = self.conn.run(command, warn=False, hide=True)
        if result.stdout == '':
            return None
        return re.split(r'\s+', result.stdout)[1]

    def init_remote_dir(self, deploy_dir):
        """ 创建远程服务器的运行环境
        """
        deploy_dir_path = Path(deploy_dir)
        for d in [ self.replacer.deploy_dir,
            deploy_dir,
            deploy_dir_path.joinpath('logs'),
            deploy_dir_path.joinpath('output') ]:
            self.make_remote_dir(d)

    def source_venv(self):
        remote_venv_dir = self.get_remote_path('venv')
        if not self.remote_exists(remote_venv_dir):
            raise Exit('venv 还没有创建！请先执行 init_remote_venv')
        return 'source {}/bin/activate'.format(remote_venv_dir)

    def init_remote_venv(self, req_path: str='requirements.txt'):
        """ 创建虚拟环境
        """
        remote_venv_dir = self.get_remote_path('venv')
        if not self.remote_exists(remote_venv_dir):
            self.conn.run(f'{self.pye} -m venv {remote_venv_dir}')
        with self.conn.prefix(f'source {remote_venv_dir}/bin/activate'):
            self.conn.run('pip install -U pip')
            self.conn.run(f'pip install -r {self.get_remote_path(req_path)}')

    def piplist(self, format='columns'):
        """ 获取虚拟环境中的所有安装的 python 模块
        :@param format: columns (default), freeze, or json
        """
        with self.conn.prefix(self.source_venv()):
            result = self.conn.run('pip list --format ' + format)
            return result.stdout

    def pipoutdated(self, format='columns'):
        """ 查看过期的 python 模块
        :@param format: columns (default), freeze, or json
        """
        with self.conn.prefix(self.source_venv()):
            result = self.conn.run('pip list --outdated --format ' + format)
            return result.stdout

    def pipupgrade(self, names=None, all=False):
        """ 更新一个 python 模块
        """
        with self.conn.prefix(self.source_venv()):
            mod_names = []
            if all:
                result = self.conn.run('pip list --outdated --format json')
                if result.ok:
                    mod_names = [item['name'] for item in json.loads(result.stdout)]
            elif names:
                mod_names = [name for name in names]
            if mod_names:
                self.conn.run('pip install -U ' + ' '.join(mod_names))

    def put_tpl(self, tpl_name, force=False):
        """ 基于 jinja2 模板生成配置文件，根据 env 的值决定是否上传
        """
        # 创建远程文件夹
        self.make_remote_dir()
        # 获取远程文件的绝对路径
        target_remote = self.get_remote_path(tpl_name)
        tpltarget_remote_exists = self.remote_exists(target_remote)
        if force and tpltarget_remote_exists:
            logger.warning('delete %s', target_remote)
            remoter = self.conn.run(f'rm -f {target_remote}')
            if remoter.ok:
                logger.warning(f'删除远程配置文件 {target_remote}')
            tpltarget_remote_exists = False
        
        # 本地创建临时文件后上传
        if force or not tpltarget_remote_exists:
            # 创建一个临时文件用于上传，使用后缀
            _, final_file = self.replacer.set_writer(tpl_name, force=force, target_postfix=f'.{self.env_name}')
            self.conn.put(final_file, target_remote)
            logger.warning('覆盖远程配置文件 %s', target_remote)
            localrunner = runners.Local(self.conn)
            # 删除本地的临时配置文件
            localr = localrunner.run(f'rm -f {final_file.as_posix()}')
            if localr is not None and localr.ok:
                logger.warning(f'删除本地临时文件 {final_file.as_posix()}')
            
    def put_config(self, files: dict[str, str], force: bool=False) -> None:
        for tpl_name in files.keys():
            self.put_tpl(tpl_name, force)

    def rsync(self, exclude=[], is_windows=False):
        """ 部署最新程序到远程服务器
        """
        if is_windows:
            # 因为 windows 下面的 rsync 不支持 windows 风格的绝对路径，转换成相对路径
            pdir = str(self.work_dir.relative_to('.').resolve())
        else:
            pdir = str(self.work_dir.resolve())
        if not pdir.endswith('/'):
            pdir += '/'
        deploy_dir = self.get_remote_path()
        self.init_remote_dir(deploy_dir)
        rsync(self.conn, pdir, deploy_dir, exclude=exclude)
        logger.warn('RSYNC [%s] to [%s]', pdir, deploy_dir)

    def get_logs(self, extras=[]):
        """ 下载远程 logs 到本地
        """
        log_files = ['app.log', 'error.log', 'access.log']
        time_string = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        for f in log_files + extras:
            logf = self.get_remote_path('logs/{}'.format(f))
            if not self.remote_exists(logf):
                logger.warning('找不到远程 log 文件 %s', logf)
                continue
            logp = Path(logf)
            local_file = self.work_dir.joinpath('logs', '{name}_{basename}_{times}{extname}'.format(name=self.env_name, times=time_string, basename=logp.name, extname=logp.suffix))
            self.conn.get(logf, local=local_file)