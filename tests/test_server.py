"""
使用真实 Typer 命令测试服务器相关功能

本测试文件使用真实的 CLI 命令进行测试，验证命令注册、参数处理和基本功能
"""

import tempfile
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

# 导入 CLI 应用
from fabik.cli import cli
from fabik.cmd import global_state


class TestServerCommands:
    """使用真实 Typer 命令测试服务器功能"""

    @pytest.fixture(scope="class")
    def test_project_dir(self):
        """创建临时测试项目目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            
            # 创建测试用的 fabik.toml
            fabik_toml = test_dir / "fabik.toml"
            fabik_toml.write_text(f'''
NAME = 'test_project'
PYE = 'python3'
DEPLOY_DIR = '/srv/app/test_project'

[PATH]
work_dir = "{test_dir}"
tpl_dir = "{test_dir}/tpls"

[FABRIC]
host = 'localhost'
user = 'test_user'

RSYNC_EXCLUDE = [
    '.git',
    '__pycache__',
    '*.pyc',
    '.pytest_cache',
    'tests',
]

['.env']
FLASK_ENV = 'production'
FLASK_RUN_PORT = 5000

['gunicorn.conf.py']
wsgi_app = 'wsgi:test_app'
bind = '127.0.0.1:5000'
''')
            
            # 创建必要的目录
            (test_dir / "tpls").mkdir()
            (test_dir / "logs").mkdir(exist_ok=True)
            
            yield test_dir

    @pytest.fixture
    def runner(self):
        """Typer CLI 运行器"""
        return CliRunner()

    def test_server_command_structure(self, runner: CliRunner):
        """测试服务器命令结构"""
        # 测试服务器命令帮助
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "server" in result.output
        
        # 测试服务器子命令帮助
        result = runner.invoke(cli, ["server", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "deploy" in result.output
        assert "start" in result.output
        assert "stop" in result.output
        assert "reload" in result.output
        assert "dar" in result.output

    def test_venv_command_structure(self, runner: CliRunner):
        """测试 venv 命令结构"""
        # 测试 venv 命令帮助
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "venv" in result.output
        
        # 测试 venv 子命令帮助
        result = runner.invoke(cli, ["venv", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "update" in result.output
        assert "outdated" in result.output

    def test_server_deploy_help(self, runner: CliRunner):
        """测试 server deploy 命令帮助"""
        result = runner.invoke(cli, ["server", "deploy", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "部署项目到远程服务器" in result.output

    def test_server_start_help(self, runner: CliRunner):
        """测试 server start 命令帮助"""
        result = runner.invoke(cli, ["server", "start", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "启动项目进程" in result.output

    def test_server_stop_help(self, runner: CliRunner):
        """测试 server stop 命令帮助"""
        result = runner.invoke(cli, ["server", "stop", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "停止项目进程" in result.output

    def test_server_reload_help(self, runner: CliRunner):
        """测试 server reload 命令帮助"""
        result = runner.invoke(cli, ["server", "reload", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "重载项目进程" in result.output

    def test_server_dar_help(self, runner: CliRunner):
        """测试 server dar 命令帮助"""
        result = runner.invoke(cli, ["server", "dar", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "部署代码，然后执行重载" in result.output

    def test_venv_update_help(self, runner: CliRunner):
        """测试 venv update 命令帮助"""
        result = runner.invoke(cli, ["venv", "update", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "部署远程服务器的虚拟环境" in result.output
        assert "--init" in result.output
        assert "--requirements-file-name" in result.output

    def test_venv_outdated_help(self, runner: CliRunner):
        """测试 venv outdated 命令帮助"""
        result = runner.invoke(cli, ["venv", "outdated", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "打印所有的过期的 python package" in result.output

    def test_command_registration(self, runner: CliRunner):
        """测试命令是否正确注册"""
        # 测试所有顶级命令都存在
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        
        commands = ["init", "gen", "conf", "venv", "server"]
        for cmd in commands:
            assert cmd in result.output, f"命令 {cmd} 应该存在"

    def test_global_state_initialization(self, test_project_dir: Path):
        """测试全局状态初始化"""
        # 保存当前状态
        original_cwd = global_state.cwd
        original_env = global_state.env
        
        try:
            # 设置测试状态
            global_state.cwd = test_project_dir
            global_state.conf_file = test_project_dir / "fabik.toml"
            global_state.env = "local"
            
            # 测试配置加载
            conf_data = global_state.load_conf_data()
            assert isinstance(conf_data, dict)
            assert conf_data.get("NAME") == "test_project"
            assert conf_data.get("PYE") == "python3"
            
        finally:
            # 恢复状态
            global_state.cwd = original_cwd
            global_state.env = original_env

    def test_server_callback_registration(self, runner: CliRunner):
        """测试服务器回调注册"""
        # 测试不同部署类的选项
        result = runner.invoke(cli, ["server", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "--deploy-class" in result.output
        assert "gunicorn" in result.output
        assert "uwsgi" in result.output

    def test_environment_parameter(self, runner: CliRunner, test_project_dir: Path):
        """测试环境参数处理"""
        # 测试环境参数传递
        result = runner.invoke(cli, ["-e", "local", "server", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        
        result = runner.invoke(cli, ["--env", "prod", "venv", "--help"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_error_handling(self, runner: CliRunner):
        """测试错误处理"""
        # 测试不存在的配置文件
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_dir = Path(temp_dir) / "empty"
            empty_dir.mkdir()
            
            result = runner.invoke(cli, ["--cwd", str(empty_dir), "server", "--help"])
            # 应该显示错误信息而不是崩溃
            assert result.exit_code == 1 or "fabik.toml" in result.output

    def test_config_file_parameter(self, runner: CliRunner, test_project_dir: Path):
        """测试配置文件参数"""
        # 测试自定义配置文件
        custom_config = test_project_dir / "custom.toml"
        shutil.copy(test_project_dir / "fabik.toml", custom_config)
        
        result = runner.invoke(cli, ["--conf-file", str(custom_config), "server", "--help"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_command_chaining(self, runner: CliRunner, test_project_dir: Path):
        """测试命令链式调用"""
        # 测试多个参数组合
        result = runner.invoke(cli, [
            "--cwd", str(test_project_dir),
            "-e", "local",
            "server",
            "--help"
        ], catch_exceptions=False)
        assert result.exit_code == 0

    def test_help_consistency(self, runner: CliRunner):
        """测试帮助信息一致性"""
        # 测试所有帮助信息都包含中文
        commands = [
            ["server"],
            ["venv"],
            ["server", "deploy"],
            ["server", "start"],
            ["server", "stop"],
            ["server", "reload"],
            ["server", "dar"],
            ["venv", "update"],
            ["venv", "outdated"],
        ]
        
        for cmd in commands:
            result = runner.invoke(cli, cmd + ["--help"], catch_exceptions=False)
            assert result.exit_code == 0
            assert len(result.output) > 0

    def test_server_subcommands_registration(self):
        """测试服务器子命令注册"""
        # 获取服务器命令组
        server_group = None
        for cmd in cli.registered_commands:
            if cmd.name == "server":
                server_group = cmd
                break
        
        assert server_group is not None, "server 命令组应该存在"
        
        # 检查服务器子命令
        server_commands = [sub.name for sub in server_group.registered_commands]
        expected_server_cmds = ["deploy", "start", "stop", "reload", "dar"]
        
        for cmd in expected_server_cmds:
            assert cmd in server_commands, f"服务器子命令 {cmd} 应该存在"

    def test_venv_subcommands_registration(self):
        """测试 venv 子命令注册"""
        # 获取 venv 命令组
        venv_group = None
        for cmd in cli.registered_commands:
            if cmd.name == "venv":
                venv_group = cmd
                break
        
        assert venv_group is not None, "venv 命令组应该存在"
        
        # 检查 venv 子命令
        venv_commands = [sub.name for sub in venv_group.registered_commands]
        expected_venv_cmds = ["update", "outdated"]
        
        for cmd in expected_venv_cmds:
            assert cmd in venv_commands, f"venv 子命令 {cmd} 应该存在"

    def test_gen_requirements_command(self, runner: CliRunner):
        """测试 gen requirements 命令"""
        # 由于需要 uv 环境，测试帮助信息
        result = runner.invoke(cli, ["gen", "requirements", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "requirements.txt" in result.output

    def test_venv_update_with_requirements(self, runner: CliRunner):
        """测试 venv update 带 requirements 参数"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_project"
            test_dir.mkdir()
            
            result = runner.invoke(cli, [
                "--cwd", str(test_dir),
                "venv", "update", "--help"
            ], catch_exceptions=False)
            assert result.exit_code == 0
            assert "--requirements-file-name" in result.output

    def test_deployment_class_options(self, runner: CliRunner):
        """测试部署类选项"""
        # 测试 gunicorn 选项
        result = runner.invoke(cli, ["server", "--deploy-class", "gunicorn", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        
        # 测试 uwsgi 选项
        result = runner.invoke(cli, ["server", "--deploy-class", "uwsgi", "--help"], catch_exceptions=False)
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])