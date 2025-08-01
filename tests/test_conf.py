"""
Tests for fabik.cmd module's conf_tpl and conf_make commands
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import json
import tomli_w

import typer
import jinja2
from fabik.cmd import conf_tpl, conf_make, global_state, config_validator_tpldir
from fabik.error import PathError, ConfigError


class TestConfCommands:
    """测试 conf_tpl 和 conf_make 命令"""

    def setup_method(self):
        """每个测试方法前重置 global_state"""
        global_state.cwd = None
        global_state.env = None
        global_state.conf_file = None
        global_state.fabic_config = None
        global_state.force = False
        global_state._config_validators = []

    def test_conf_tpl_with_valid_files(self, temp_dir, mocker, mock_echo_functions):
        """测试 conf_tpl 命令处理有效的模板文件"""
        # 创建模板目录和文件
        tpl_dir = temp_dir / "tpls"
        tpl_dir.mkdir()
        test_tpl1 = tpl_dir / "test1.jinja2"
        test_tpl2 = tpl_dir / "test2.jinja2"
        test_tpl1.write_text("template content 1")
        test_tpl2.write_text("template content 2")

        # 设置 global_state
        global_state.cwd = temp_dir
        global_state.env = "dev"

        # 模拟 FabikConfig
        mock_fabik_config = MagicMock()
        mock_fabik_config.getcfg.return_value = str(tpl_dir)
        mock_fabik_config.root_data = {"ENV": {"dev": {}}}
        global_state.fabic_config = mock_fabik_config

        # 模拟 load_conf_data 方法
        mocker.patch(
            "fabik.cmd.GlobalState.load_conf_data",
            return_value=mock_fabik_config.root_data,
        )

        # 模拟 Path.exists 方法，让它返回 True
        mocker.patch("pathlib.Path.exists", return_value=True)

        # 模拟 write_config_file 方法
        mock_write_config_file = mocker.patch("fabik.cmd.GlobalState.write_config_file")

        # 执行测试
        conf_tpl(["test1", "test2"], env_postfix=False)

        # 验证结果
        assert mock_write_config_file.call_count == 2
        mock_write_config_file.assert_has_calls(
            [
                call("test1", tpl_dir=tpl_dir, target_postfix=""),
                call("test2", tpl_dir=tpl_dir, target_postfix=""),
            ]
        )

    def test_conf_tpl_with_env_postfix(self, temp_dir, mocker, mock_echo_functions):
        """测试 conf_tpl 命令使用环境名称后缀"""
        # 创建模板目录和文件
        tpl_dir = temp_dir / "tpls"
        tpl_dir.mkdir()
        test_tpl = tpl_dir / "config.jinja2"
        test_tpl.write_text("template content")

        # 设置 global_state
        global_state.cwd = temp_dir
        global_state.env = "prod"

        # 模拟 FabikConfig
        mock_fabik_config = MagicMock()
        mock_fabik_config.getcfg.return_value = str(tpl_dir)
        mock_fabik_config.root_data = {"ENV": {"prod": {}}}
        global_state.fabic_config = mock_fabik_config

        # 模拟 load_conf_data 方法
        mocker.patch(
            "fabik.cmd.GlobalState.load_conf_data",
            return_value=mock_fabik_config.root_data,
        )

        # 模拟 Path.exists 方法，让它返回 True
        mocker.patch("pathlib.Path.exists", return_value=True)

        # 模拟 write_config_file 方法
        mock_write_config_file = mocker.patch("fabik.cmd.GlobalState.write_config_file")

        # 执行测试
        conf_tpl(["config"], env_postfix=True)

        # 验证结果
        mock_write_config_file.assert_called_once_with(
            "config", tpl_dir=tpl_dir, target_postfix=".prod"
        )

    def test_conf_tpl_with_nonexistent_file(
        self, temp_dir, mocker, mock_echo_functions
    ):
        """测试 conf_tpl 命令处理不存在的模板文件"""
        # 创建模板目录
        tpl_dir = temp_dir / "tpls"
        tpl_dir.mkdir()

        # 设置 global_state
        global_state.cwd = temp_dir

        # 模拟 FabikConfig
        mock_fabik_config = MagicMock()
        mock_fabik_config.getcfg.return_value = str(tpl_dir)
        mock_fabik_config.root_data = {}
        global_state.fabic_config = mock_fabik_config

        # 模拟 load_conf_data 方法
        mocker.patch(
            "fabik.cmd.GlobalState.load_conf_data",
            return_value=mock_fabik_config.root_data,
        )

        # 执行测试，应该抛出异常
        with pytest.raises(typer.Abort):
            conf_tpl(["nonexistent"], env_postfix=False)

        # 验证错误信息
        mock_echo_functions["echo_error"].assert_called_once()
        assert "not found" in mock_echo_functions["echo_error"].call_args[0][0]

    def test_conf_tpl_validates_tpl_dir(self, temp_dir, mocker, mock_echo_functions):
        """测试 conf_tpl 命令验证 tpl_dir 是否存在"""
        # 设置 global_state
        global_state.cwd = temp_dir

        # 模拟 load_conf_data 方法
        mock_load_conf_data = mocker.patch("fabik.cmd.GlobalState.load_conf_data")
        mock_load_conf_data.side_effect = typer.Abort()

        # 执行测试，应该抛出异常
        with pytest.raises(typer.Abort):
            conf_tpl(["test"], env_postfix=False)

        # 验证 config_validator_tpldir 被注册
        assert len(global_state._config_validators) > 0
        assert config_validator_tpldir in global_state._config_validators

    def test_conf_make_basic(self, temp_dir, mocker, mock_echo_functions):
        """测试 conf_make 命令基本功能"""
        # 设置 global_state
        global_state.cwd = temp_dir
        global_state.env = "dev"

        # 模拟 load_conf_data 方法
        mock_load_conf_data = mocker.patch("fabik.cmd.GlobalState.load_conf_data")

        # 模拟 write_config_file 方法
        mock_write_config_file = mocker.patch("fabik.cmd.GlobalState.write_config_file")

        # 执行测试
        conf_make(["app.json", "db.toml"], env_postfix=False)

        # 验证结果
        mock_load_conf_data.assert_called_once_with(check=True)
        assert mock_write_config_file.call_count == 2
        mock_write_config_file.assert_has_calls(
            [call("app.json", target_postfix=""), call("db.toml", target_postfix="")]
        )

    def test_conf_make_with_env_postfix(self, temp_dir, mocker, mock_echo_functions):
        """测试 conf_make 命令使用环境名称后缀"""
        # 设置 global_state
        global_state.cwd = temp_dir
        global_state.env = "staging"

        # 模拟 load_conf_data 方法
        mock_load_conf_data = mocker.patch("fabik.cmd.GlobalState.load_conf_data")

        # 模拟 write_config_file 方法
        mock_write_config_file = mocker.patch("fabik.cmd.GlobalState.write_config_file")

        # 执行测试
        conf_make(["config.json"], env_postfix=True)

        # 验证结果
        mock_write_config_file.assert_called_once_with(
            "config.json", target_postfix=".staging"
        )

    def test_integration_with_configreplacer(self, temp_dir, mocker):
        """测试与 ConfigReplacer 的集成"""
        # 创建模板目录和文件
        tpl_dir = temp_dir / "tpls"
        tpl_dir.mkdir()
        test_tpl = tpl_dir / "test.json.jinja2"
        test_tpl.write_text('{"name": "{{ NAME }}", "env": "{{ ENV }}"}')

        # 设置 global_state
        global_state.cwd = temp_dir
        global_state.env = "test"

        # 创建配置数据
        conf_data = {
            "NAME": "test_app",
            "TPL_DIR": str(tpl_dir),
            "WORK_DIR": str(temp_dir),
            "ENV": {"test": {"env": "test_env"}},
        }

        # 模拟 FabikConfig
        mock_fabik_config = MagicMock()
        mock_fabik_config.getcfg.side_effect = lambda *args, **kwargs: (
            conf_data["TPL_DIR"]
            if args == ("TPL_DIR")
            else conf_data["WORK_DIR"]
            if args == ("WORK_DIR")
            else None
        )
        mock_fabik_config.root_data = conf_data
        global_state.fabic_config = mock_fabik_config

        # 模拟 load_conf_data 方法
        mocker.patch("fabik.cmd.GlobalState.load_conf_data", return_value=conf_data)

        # 模拟 Path.exists 方法，让它返回 True
        mocker.patch("pathlib.Path.exists", return_value=True)

        # 模拟 ConfigReplacer
        mock_config_replacer = mocker.patch("fabik.cmd.ConfigReplacer")
        mock_replacer_instance = MagicMock()
        mock_config_replacer.return_value = mock_replacer_instance

        # 模拟 set_writer 方法
        mock_replacer_instance.set_writer.return_value = (
            temp_dir / "test.json",
            temp_dir / "test.json",
        )

        # 模拟 writer 属性
        mock_writer = MagicMock()
        mock_replacer_instance.writer = mock_writer

        # 执行测试
        conf_tpl(["test.json"], env_postfix=False)

        # 验证结果
        mock_config_replacer.assert_called_once_with(
            conf_data, work_dir=temp_dir, tpl_dir=tpl_dir, env_name="test"
        )
        mock_replacer_instance.set_writer.assert_called_once_with(
            "test.json", False, ""
        )
        mock_writer.write_file.assert_called_once_with(False)


class TestConfCommandsIntegration:
    """集成测试 conf_tpl 和 conf_make 命令"""

    def setup_method(self):
        """每个测试方法前重置 global_state"""
        global_state.cwd = None
        global_state.env = None
        global_state.conf_file = None
        global_state.fabic_config = None
        global_state.force = False
        global_state._config_validators = []

    def test_conf_tpl_integration(self, temp_dir, mocker):
        """集成测试 conf_tpl 命令"""
        # 创建必要的目录结构
        tpl_dir = temp_dir / "tpls"
        tpl_dir.mkdir()

        # 创建模板文件
        json_tpl = tpl_dir / "config.json.jinja2"
        json_tpl.write_text(
            '{"name": "{{ NAME }}", "env": "{{ ENV }}", "path": "{{ WORK_DIR }}"}'
        )

        toml_tpl = tpl_dir / "settings.toml.jinja2"
        toml_tpl.write_text("""
[app]
name = "{{ NAME }}"
env = "{{ ENV }}"

[path]
work_dir = "{{ WORK_DIR }}"
""")

        # 创建 fabik.toml 配置文件
        fabik_toml_content = {
            "NAME": "test_project",
            "WORK_DIR": str(temp_dir),
            "TPL_DIR": str(tpl_dir),
            "ENV": {"dev": {"env": "development"}},
            "DEPLOY_DIR": "/srv/app/test_project",
        }

        # 模拟 FabikConfig
        mock_fabik_config = MagicMock()
        mock_fabik_config.getcfg.side_effect = lambda *args, **kwargs: (
            fabik_toml_content["TPL_DIR"]
            if args == ("TPL_DIR")
            else mock_fabik_config["WORK_DIR"]
            if args == ("WORK_DIR")
            else None
        )
        mock_fabik_config.root_data = fabik_toml_content
        global_state.fabic_config = mock_fabik_config

        # 设置 global_state
        global_state.cwd = temp_dir
        global_state.env = "dev"

        # 模拟 load_conf_data 方法
        mocker.patch(
            "fabik.cmd.GlobalState.load_conf_data", return_value=fabik_toml_content
        )

        # 模拟 Path.exists 方法，让它返回 True
        mocker.patch("pathlib.Path.exists", return_value=True)

        # 模拟 ConfigReplacer
        mock_replacer_class = mocker.patch("fabik.cmd.ConfigReplacer")

        # 模拟 ConfigWriter
        mock_writer = MagicMock()

        # 设置 mock_replacer 实例
        mock_replacer = MagicMock()
        mock_replacer_class.return_value = mock_replacer
        mock_replacer.set_writer.return_value = (
            temp_dir / "config.json",
            temp_dir / "config.json",
        )
        mock_replacer.writer = mock_writer

        # 执行 conf_tpl 命令
        conf_tpl(["config.json", "settings.toml"], env_postfix=False)

        # 验证 ConfigReplacer 被正确调用
        assert mock_replacer_class.call_count == 2
        mock_replacer.set_writer.assert_any_call("config.json", False, "")
        mock_replacer.set_writer.assert_any_call("settings.toml", False, "")
        assert mock_writer.write_file.call_count == 2

    def test_conf_make_integration(self, temp_dir, mocker):
        """集成测试 conf_make 命令"""
        # 创建 fabik.toml 配置内容
        fabik_toml_content = {
            "NAME": "test_project",
            "ENV": {"prod": {"env": "production"}},
            "DEPLOY_DIR": "/srv/app/test_project",
            "PATH": {"work_dir": str(temp_dir)},
            "database": {"host": "localhost", "port": 5432, "name": "testdb"},
            "app": {"debug": False, "log_level": "INFO"},
        }

        # 模拟 FabikConfig
        mock_fabik_config = MagicMock()
        mock_fabik_config.root_data = fabik_toml_content
        global_state.fabic_config = mock_fabik_config

        # 设置 global_state
        global_state.cwd = temp_dir
        global_state.env = "prod"

        # 模拟 load_conf_data 方法
        mocker.patch(
            "fabik.cmd.GlobalState.load_conf_data", return_value=fabik_toml_content
        )

        # 模拟 ConfigReplacer
        mock_replacer_class = mocker.patch("fabik.cmd.ConfigReplacer")

        # 模拟 ConfigWriter
        mock_writer = MagicMock()

        # 设置 mock_replacer 实例
        mock_replacer = MagicMock()
        mock_replacer_class.return_value = mock_replacer
        mock_replacer.set_writer.side_effect = [
            (temp_dir / "database.json", temp_dir / "database.json"),
            (temp_dir / "app.json", temp_dir / "app.json"),
        ]
        mock_replacer.writer = mock_writer

        # 执行 conf_make 命令
        conf_make(["database.json", "app.json"], env_postfix=False)

        # 验证 ConfigReplacer 被正确调用
        assert mock_replacer_class.call_count == 2
        mock_replacer.set_writer.assert_any_call("database.json", False, "")
        mock_replacer.set_writer.assert_any_call("app.json", False, "")
        assert mock_writer.write_file.call_count == 2

    def test_conf_make_with_force(self, temp_dir, mocker):
        """测试 conf_make 命令使用 force 参数覆盖现有文件"""
        # 创建一个已存在的配置文件
        config_file = temp_dir / "config.json"
        config_file.write_text('{"version": "0.9.0"}')

        # 创建 fabik.toml 配置内容
        fabik_toml_content = {
            "NAME": "test_project",
            "ENV": {"test": {"env": "test_env"}},
            "PATH": {"work_dir": str(temp_dir)},
            "config": {"version": "1.0.0"},
        }

        # 模拟 FabikConfig
        mock_fabik_config = MagicMock()
        mock_fabik_config.root_data = fabik_toml_content
        global_state.fabic_config = mock_fabik_config

        # 设置 global_state
        global_state.cwd = temp_dir

        # 模拟 load_conf_data 方法
        mocker.patch(
            "fabik.cmd.GlobalState.load_conf_data", return_value=fabik_toml_content
        )

        # 模拟 ConfigReplacer
        mock_replacer_class = mocker.patch("fabik.cmd.ConfigReplacer")

        # 模拟 ConfigWriter
        mock_writer = MagicMock()

        # 设置 mock_replacer 实例
        mock_replacer = MagicMock()
        mock_replacer_class.return_value = mock_replacer
        mock_replacer.set_writer.return_value = (
            temp_dir / "config.json",
            temp_dir / "config.json",
        )
        mock_replacer.writer = mock_writer

        # 不使用 force 参数
        global_state.force = False
        conf_make(["config.json"], env_postfix=False)

        # 验证 write_file 被调用，使用 force=False
        mock_writer.write_file.assert_called_with(False)

        # 使用 force 参数
        global_state.force = True
        conf_make(["config.json"], env_postfix=False)

        # 验证 write_file 被调用，使用 force=True
        mock_writer.write_file.assert_called_with(True)
