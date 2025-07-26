""" .. _fabik_deploy_gunicorn:

fabik.deploy.gunicorn
~~~~~~~~~~~~~~~~~~~~~~

封装远程 gunicorn 部署。
"""

from pathlib import Path
from fabric.connection import Connection
from invoke.exceptions import Exit

from fabik.deploy import Deploy, logger


class GunicornDeploy(Deploy):
    """ 使用 Gunicorn 来部署服务
    """
    def __init__(self, fabik_conf: dict, work_dir: Path, conn: Connection, env_name: str | None=None):
        super().__init__(fabik_conf, work_dir, conn, env_name)

    def get_pid_file(self):
        """ 使用 pidfile 来判断进程是否启动
        """
        pidfile = self.get_remote_path('gunicorn.pid')
        if self.remote_exists(pidfile):
            return pidfile
        return None

    def get_pid_value(self, *args):
        """ 获取远程 pid 文件中的 pid 值
        """
        pid_value = self.cat_remote_file('gunicorn.pid')
        if pid_value is None:
            raise Exit('gunicorn.pid 没有值！')
        return pid_value.strip()

    def get_gunicorn_exe(self):
        """ 获取 venv 中 uwsgi 的可执行文件绝对路径
        """
        gunicorn_exe = self.get_remote_path('venv/bin/gunicorn')
        if not self.remote_exists(gunicorn_exe):
            raise Exit('没有找到 gunicorn 可执行文件！请先执行 init_remote_venv')
        return gunicorn_exe

    def start(self, wsgi_app=None, daemon=None):
        """ 启动服务进程
        :@param wsgi_app: 传递 wsgi_app 名称
        :@param daemon: 若值为 True，则强制加上 -D 参数
        """
        pidfile = self.get_pid_file()
        if pidfile is not None:
            raise Exit('进程不能重复启动！')
        conf = self.get_remote_path('gunicorn.conf.py')
        cmd = self.get_gunicorn_exe() + ' --config ' + conf
        if daemon is True:
            cmd += ' -D'
        if wsgi_app is not None:
            cmd += ' ' + wsgi_app
        self.conn.run(cmd)

    def stop(self):
        """ 停止 API 进程
        """
        pidvalue = self.get_pid_value()
        killr = self.conn.run('kill -s TERM ' + pidvalue)
        if killr.ok:
            logger.warning('优雅关闭 %s', pidvalue)
            # 删除 pidfile 以便下次启动
            self.conn.run('rm %s' % self.get_pid_file())
        else:
            logger.warning('关闭 %s 失败', pidvalue)

    def reload(self):
        """ 优雅重载 API 进程
        """
        pidvalue = self.get_pid_value()
        killr = self.conn.run('kill -s HUP ' + pidvalue)
        if killr.ok:
            logger.warning('优雅重载 %s', pidvalue)
        else:
            logger.warning('重载 %s 失败', pidvalue)
