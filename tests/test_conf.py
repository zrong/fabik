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
from fabik.cmd.conf import conf_tpl, conf_make
from fabik.cmd import global_state
from fabik.conf import config_validator_tpldir
from fabik.error import PathError, ConfigError


class TestConfCommands:
    """测试 conf_tpl 和 conf_make 命令"""

    def setup_method(self):
        """每个测试方法前重置 global_state"""
        global_state.cwd = None
        global_state.env = None
        global_state.conf_file = None
        global_state.fabik_config = None
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
        global_state.fabik_config = mock_fabik_config

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
        global_state.env_postfix = False
        conf_tpl(["test1", "test2"])

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
        global_state.fabik_config = mock_fabik_config

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
        global_state.env_postfix = True
        conf_tpl(["config"])

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
        global_state.fabik_config = mock_fabik_config

        # 模拟 load_conf_data 方法
        mocker.patch(
            "fabik.cmd.GlobalState.load_conf_data",
            return_value=mock_fabik_config.root_data,
        )

        # 执行测试，应该抛出异常
        global_state.env_postfix = False
        with pytest.raises(typer.Abort):
            conf_tpl(["nonexistent"])

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
        global_state.env_postfix = False
        with pytest.raises(typer.Abort):
            conf_tpl(["test"])

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
        global_state.env_postfix = False
        conf_make(["app.json", "db.toml"])

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
        global_state.env_postfix = True
        conf_make(["config.json"])

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
            if args == ("TPL_DIR",)
            else conf_data["WORK_DIR"]
            if args == ("WORK_DIR",)
            else None
        )
        mock_fabik_config.root_data = conf_data
        global_state.fabik_config = mock_fabik_config

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
        global_state.env_postfix = False
        conf_tpl(["test.json"])

        # 验证结果
        mock_config_replacer.assert_called_once_with(
            conf_data, temp_dir, output_dir=None, tpl_dir=tpl_dir, env_name="test", verbose=False
        )
        mock_replacer_instance.set_writer.assert_called_once_with(
            "test.json", force=False, rename=False, target_postfix="", immediately=True
        )


class TestConfCommandsIntegration:
    """集成测试 conf_tpl 和 conf_make 命令"""

    def setup_method(self):
        """每个测试方法前重置 global_state"""
        global_state.cwd = None
        global_state.env = None
        global_state.conf_file = None
        global_state.fabik_config = None
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
            if args == ("TPL_DIR",)
            else fabik_toml_content["WORK_DIR"]
            if args == ("WORK_DIR",)
            else None
        )
        mock_fabik_config.root_data = fabik_toml_content
        global_state.fabik_config = mock_fabik_config

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
        global_state.env_postfix = False
        conf_tpl(["config.json", "settings.toml"])

        # 验证 ConfigReplacer 被正确调用
        assert mock_replacer_class.call_count == 2
        mock_replacer.set_writer.assert_any_call("config.json", force=False, rename=False, target_postfix="", immediately=True)
        mock_replacer.set_writer.assert_any_call("settings.toml", force=False, rename=False, target_postfix="", immediately=True)

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
        global_state.fabik_config = mock_fabik_config

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
        global_state.env_postfix = False
        conf_make(["database.json", "app.json"])

        # 验证 ConfigReplacer 被正确调用
        assert mock_replacer_class.call_count == 2
        mock_replacer.set_writer.assert_any_call("database.json", force=False, rename=False, target_postfix="", immediately=True)
        mock_replacer.set_writer.assert_any_call("app.json", force=False, rename=False, target_postfix="", immediately=True)

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
        global_state.fabik_config = mock_fabik_config

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
        global_state.env_postfix = False
        conf_make(["config.json"])

        # 使用 force 参数
        global_state.force = True
        global_state.env_postfix = False
        conf_make(["config.json"])

        # 验证 set_writer 被正确调用
        assert mock_replacer.set_writer.call_count == 2
        # 验证第一次调用（force=False）
        mock_replacer.set_writer.assert_any_call(
            "config.json",
            force=False,
            rename=False,
            target_postfix="",
            immediately=True,
        )
        # 验证第二次调用（force=True）
        mock_replacer.set_writer.assert_any_call(
            "config.json",
            force=True,
            rename=False,
            target_postfix="",
            immediately=True,
        )

    def test_conf_callback_with_output_file(self, temp_dir):
        """测试 conf_callback 处理 --output-file 参数"""
        from fabik.cmd.conf import conf_callback
        
        output_file = temp_dir / "custom_config.json"
        
        # 执行 conf_callback
        conf_callback(
            force=False,
            rename=False, 
            output_dir=None,
            output_file=output_file,
            env_postfix=False
        )
        
        # 验证结果：只进行简单赋值
        assert global_state.output_file == output_file
        assert global_state.output_dir is None
        assert global_state.force is False
        assert global_state.rename is False
        assert global_state.env_postfix is False
    
    def test_conf_callback_with_both_output_params(self, temp_dir):
        """测试 conf_callback 同时提供 --output-file 和 --output-dir 参数"""
        from fabik.cmd.conf import conf_callback
        
        output_dir = temp_dir / "configs"
        output_dir.mkdir()
        output_file = temp_dir / "custom_config.json"
        
        # 执行 conf_callback
        conf_callback(
            force=False,
            rename=False,
            output_dir=output_dir,
            output_file=output_file,
            env_postfix=False
        )
        
        # 验证结果：只进行简单赋值，不处理优先级
        assert global_state.output_file == output_file
        assert global_state.output_dir == output_dir
    
    def test_conf_callback_with_only_output_dir(self, temp_dir):
        """测试 conf_callback 仅提供 --output-dir 参数"""
        from fabik.cmd.conf import conf_callback
        
        output_dir = temp_dir / "configs"
        output_dir.mkdir()
        
        # 执行 conf_callback
        conf_callback(
            force=True,
            rename=True,
            output_dir=output_dir,
            output_file=None,
            env_postfix=True
        )
        
        # 验证结果：只进行简单赋值
        assert global_state.output_dir == output_dir
        assert global_state.output_file is None
        assert global_state.force is True
        assert global_state.rename is True
        assert global_state.env_postfix is True
    
    def test_resolve_output_parameters_priority(self, temp_dir, mocker):
        """测试 _resolve_output_parameters 方法的参数优先级处理"""
        from fabik.cmd import global_state
        
        output_dir = temp_dir / "configs"
        output_dir.mkdir()
        output_file = temp_dir / "custom_config.json"
        
        # 设置 global_state
        global_state.cwd = temp_dir
        global_state.output_dir = output_dir
        global_state.output_file = output_file
        
        # 模拟 echo_warning
        mock_echo_warning = mocker.patch("fabik.cmd.echo_warning")
        
        # 测试参数优先级处理
        resolved_output_dir, resolved_output_file = global_state._resolve_output_parameters()
        
        # 验证结果：--output-file 优先
        assert resolved_output_dir is None
        assert resolved_output_file == output_file
        
        # 验证警告信息
        mock_echo_warning.assert_called_once_with(
            "Both --output-file and --output-dir provided. --output-dir will be ignored."
        )
    
    def test_resolve_output_parameters_dir_only(self, temp_dir):
        """测试 _resolve_output_parameters 方法仅处理 output_dir"""
        from fabik.cmd import global_state
        
        output_dir = temp_dir / "configs"
        output_dir.mkdir()
        
        # 设置 global_state  
        global_state.cwd = temp_dir
        global_state.output_dir = output_dir
        global_state.output_file = None
        
        # 测试仅有 output_dir
        resolved_output_dir, resolved_output_file = global_state._resolve_output_parameters()
        
        # 验证结果
        assert resolved_output_dir == output_dir
        assert resolved_output_file is None
