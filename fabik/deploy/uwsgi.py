""" .._fabik_deploy_uwsgi:

fabik.deploy.uwsgi
~~~~~~~~~~~~~~~~~~~

封装远程 uwsgi 部署。
"""


from pathlib import Path

from invoke.exceptions import Exit
from fabik.deploy import Deploy


class UwsgiDeploy(Deploy):
    """ 使用 uWSGI 来部署服务
    """
    def __init__(self, env_name, pyape_conf, conn, work_dir: Path | None = None):
        super().__init__(env_name, pyape_conf, conn, work_dir)

    def get_fifo_file(self):
        """ 使用 master-fifo 来管理进程
        http://uwsgi-docs-zh.readthedocs.io/zh_CN/latest/MasterFIFO.html
        """
        fifofile = self.get_remote_path('uwsgi.fifo')
        if self.remote_exists(fifofile):
            return fifofile
        return None

    def get_pid_file(self):
        """ 使用 pidfile 来判断进程是否启动
        """
        pidfile = self.get_remote_path('uwsgi.pid')
        if self.remote_exists(pidfile):
            return pidfile
        return None

    def get_uwsgi_exe(self):
        """ 获取 venv 中 uwsgi 的可执行文件绝对路径
        """
        uwsgi_exe = self.get_remote_path('venv/bin/uwsgi')
        if not self.remote_exists(uwsgi_exe):
            raise Exit('没有找到 uwsgi 可执行文件！请先执行 init_remote_venv')
        return uwsgi_exe

    def start(self):
        """ 启动服务进程
        """
        pidfile = self.get_pid_file()
        if pidfile is not None:
            raise Exit('进程不能重复启动！')
        self.conn.run(self.get_uwsgi_exe() + ' ' + self.get_remote_path('uwsgi.ini'))

    def stop(self):
        """ 停止 API 进程
        """
        fifofile = self.get_fifo_file()
        if fifofile is not None:
            self.conn.run('echo q > %s' % fifofile)
        pidfile = self.get_pid_file()
        # 删除 pidfile 以便下次启动
        if pidfile is not None:
            self.conn.run('rm %s' % pidfile)

    def reload(self):
        """ 优雅重载 API 进程
        """
        fifofile = self.get_fifo_file()
        if fifofile is None:
            raise Exit('进程还没有启动！')
        self.conn.run('echo r > %s' % fifofile)
