""" .. _fabik_deploy_tmux:

fabik.deploy.tmux
~~~~~~~~~~~~~~~~~~~

封装远程 tmux 调用。
"""

class Tmux(object):
    """Tmux helper for fabric > 2"""
    def __init__(self, runner, session_name='default'):
        self.session_name = session_name
        self.run_cmd = runner.run

        self.create_session()

    def create_session(self):
        test = self.run_cmd('tmux has-session -t %s' % self.session_name, warn=True)

        if test.failed:
            self.run_cmd('tmux new-session -d -s %s' % self.session_name)

        self.run_cmd(
            'tmux set-option -t %s -g allow-rename off' % self.session_name)

    def recreate(self):
        self.kill_session()
        self.create_session()

    def kill_session(self):
        self.run_cmd('tmux kill-session -t %s' % self.session_name)

    def command(self, command, pane=0):
        self.run_cmd('tmux send-keys -t %s:%s "%s" ENTER' % (
            self.session_name, pane, command))

    def new_window(self, name):
        self.run_cmd('tmux new-window -t %s -n %s' % (self.session_name, name))

    def find_window(self, name):
        test = self.run_cmd('tmux list-windows -t %s | grep \'%s\'' % (self.session_name, name), warn=True)

        return test.ok

    def rename_window(self, new_name, old_name=None):
        if old_name is None:
            self.run_cmd('tmux rename-window %s' % new_name)
        else:
            self.run_cmd('tmux rename-window -t %s %s' % (old_name, new_name))

    def wait_for(self, signal_name):
        self.run_cmd('tmux wait-for %s' % signal_name)

    def run_singleton(self, command, orig_name, wait=True):
        run_name = "run/%s" % orig_name
        done_name = "done/%s" % orig_name

        # If the program is running we wait to be finished.
        if self.find_window(run_name):
            self.wait_for(run_name)

        # If the program is not running we create a window with done_name
        if not self.find_window(done_name):
            self.new_window(done_name)

        self.rename_window(run_name, done_name)

        # Check that we can execute the commands in the correct window
        assert self.find_window(run_name)

        rename_window_cmd = 'tmux rename-window -t %s %s' % (
            run_name, done_name)
        signal_cmd = 'tmux wait-for -S %s' % run_name

        expanded_command = '%s ; %s ; %s' % (
            command, rename_window_cmd, signal_cmd)
        self.command(expanded_command, run_name)

        if wait:
            self.wait_for(run_name)
